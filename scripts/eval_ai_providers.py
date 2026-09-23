"""Small grounded comparison: five evidence packets, one call per provider and case."""

from pathlib import Path
import os
import re
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.data import load_dataset  # noqa: E402
from backend.app.services.ai_provider import (  # noqa: E402
    AIExplanation, NvidiaProvider, OpenAIProvider, ProviderError, TemplateAIProvider, get_ai_status,
)
from backend.app.services.navigator import ask_navigator, calculate_skill_gap, recommend_activities  # noqa: E402


CASES = (
    ("golden_E0100", "E0100", "Почему первая активность лучше второй?", "compare", None),
    ("without_career_goal", "E0003", "Какой следующий шаг?", None, None),
    ("unmet_prerequisites", "E0001", "Можно ли начать EV_006?", None, "EV_006"),
    ("closest_to_target", "E0106", "Что поможет достичь цели?", None, None),
    ("no_eligible_activities", "E0029", "Что делать, если активностей нет?", None, None),
)


def _score(result: dict, packet: dict) -> dict:
    structured = AIExplanation.model_validate(result["ai_explanation"])
    text = " ".join((structured.summary, *structured.why_recommended, *structured.expected_impact,
                     *structured.limitations, structured.next_step))
    employee = packet["employee"]
    ids_valid = set(structured.evidence_ids) <= set(packet["allowed_evidence_ids"])
    # The provider adapter already rejects unknown numbers; this flags visible human review dimensions.
    return {
        "schema": True,
        "known_ids": ids_valid,
        "numbers_grounded": True,
        "russian": len(re.findall(r"[А-Яа-яЁё]", text)) >= 20,
        "personalized": employee["full_name"].split()[0] in text or bool(
            packet["activities"] and packet["activities"][0]["title"] in text),
        "clear": 40 <= len(text) <= 1800,
        "actionable": len(structured.next_step) >= 12,
        "factual_correctness": "manual_review",
    }


def main() -> int:
    data = load_dataset()
    status = get_ai_status()
    selected = {status["configured_provider"], status["fallback_provider"]} - {"template"}
    requests = 0
    failures = 0
    for label, employee_id, question, intent, event_id in CASES:
        employee = data.employees[employee_id]
        if label == "without_career_goal":
            assert employee["career_goal"] is None
        if label == "closest_to_target":
            assert calculate_skill_gap(data, employee_id)["progress_pct"] >= 80
        if label == "no_eligible_activities":
            assert not recommend_activities(data, employee_id, TemplateAIProvider())["recommendations"]
        answer = ask_navigator(data, employee_id, question, intent, event_id, None, TemplateAIProvider())
        packet = answer.pop("_evidence_packet")
        if label == "unmet_prerequisites":
            assert packet["blocked_activity"] and any(
                not item["met"] for item in packet["blocked_activity"]["prerequisites"])
        print(f"case={label} template=PASS")
        for name, provider in (("nvidia", NvidiaProvider()), ("openai", OpenAIProvider())):
            if not status[f"{name}_configured"]:
                state = "BLOCKED_BY_MISSING_KEY" if name in selected else "SKIPPED_NOT_SELECTED"
                print(f"case={label} provider={name} result={state}")
                failures += name in selected
                continue
            started = perf_counter()
            requests += 1
            try:
                result = provider.rephrase(answer, question, packet)
                dimensions = _score(result, packet)
            except (ProviderError, KeyError, ValueError) as exc:
                reason = str(exc) if isinstance(exc, ProviderError) else "invalid_schema"
                print(f"case={label} provider={name} result=FAIL reason={reason} latency_ms={round((perf_counter() - started) * 1000)}")
                failures += 1
            else:
                print(f"case={label} provider={name} result=PASS model={os.getenv(provider.model_var, provider.default_model)} latency_ms={round((perf_counter() - started) * 1000)} dimensions={dimensions}")
    print(f"real_requests_attempted={requests} cases={len(CASES)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
