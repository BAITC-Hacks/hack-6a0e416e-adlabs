"""One live request per external provider, plus an offline template check."""

from pathlib import Path
import os
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.data import load_dataset  # noqa: E402
from backend.app.services.ai_provider import (  # noqa: E402
    AIExplanation, NvidiaProvider, OpenAIProvider, ProviderError, TemplateAIProvider, get_ai_status,
)
from backend.app.services.navigator import ask_navigator  # noqa: E402


def main() -> int:
    data = load_dataset()
    answer = ask_navigator(data, "E0100", "Почему первая активность лучше второй?", "compare",
                           None, None, TemplateAIProvider())
    packet = answer.pop("_evidence_packet")
    assert answer["provider"] == "template" and answer["summary"] and packet["activities"]
    print("template: PASS")
    status = get_ai_status()
    configured = {"nvidia": status["nvidia_configured"], "openai": status["openai_configured"]}
    failed = False
    requests = 0
    for name, provider in (("nvidia", NvidiaProvider()), ("openai", OpenAIProvider())):
        if not configured[name]:
            print(f"{name}: BLOCKED_BY_MISSING_KEY")
            failed = True
            continue
        started = perf_counter()
        requests += 1
        try:
            result = provider.rephrase(answer, "Почему первая активность лучше второй?", packet)
            AIExplanation.model_validate(result["ai_explanation"])
        except (ProviderError, KeyError, ValueError) as exc:
            reason = str(exc) if isinstance(exc, ProviderError) else "invalid_schema"
            print(f"{name}: FAIL ({reason}) latency_ms={round((perf_counter() - started) * 1000)}")
            failed = True
        else:
            print(f"{name}: PASS model={os.getenv(provider.model_var, provider.default_model)} latency_ms={round((perf_counter() - started) * 1000)}")
    print(f"real_requests_attempted={requests}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
