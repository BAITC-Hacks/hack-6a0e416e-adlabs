"""Explanation providers. Recommendations and ranking always come from ml.engine."""

import os
import json
from urllib import request
from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    @abstractmethod
    def explain(self, recommendation: dict, target: dict | None) -> str:
        """Explain a predetermined recommendation without changing its rank or impact."""

    def rephrase(self, answer: dict, question: str) -> dict:
        return answer


class TemplateAIProvider(BaseAIProvider):
    def explain(self, recommendation: dict, target: dict | None) -> str:
        if target is None:
            return "No career target is set."
        target_name = f"{target['role']} {target['grade']}"
        gains = recommendation.get("matched_skill_gains", [])
        skills = ", ".join(
            f"{gain['name']} ({gain['current_level']}→{gain['projected_level']}, closes {gain['gap_closed']})"
            for gain in gains if gain.get("gap_closed", 0) > 0
        ) or "target skill gaps"
        breakdown = recommendation.get("score_breakdown", {})
        reason = "critical skill coverage" if any(gain.get("critical") for gain in gains) else "target gap coverage"
        delta = recommendation.get("projected_impact", {}).get("progress_delta_pct", 0)
        return (
            f"For the {target_name} target, this activity develops {skills}. "
            f"Projected progress gain: {delta:.1f} percentage points. "
            f"The score includes {reason}; completing it does not guarantee promotion."
        )


class OpenAIProvider(TemplateAIProvider):
    def rephrase(self, answer: dict, question: str) -> dict:
        return _llm_rephrase(answer, question, "openai", "OPENAI_API_KEY", "OPENAI_MODEL",
                             "https://api.openai.com/v1/chat/completions", "gpt-4o-mini")


class NvidiaProvider(TemplateAIProvider):
    def rephrase(self, answer: dict, question: str) -> dict:
        return _llm_rephrase(answer, question, "nvidia", "NVIDIA_API_KEY", "NVIDIA_MODEL",
                             "https://integrate.api.nvidia.com/v1/chat/completions", "openai/gpt-oss-20b")


def _llm_rephrase(answer: dict, question: str, provider: str, key_var: str,
                  model_var: str, endpoint: str, default_model: str) -> dict:
    key = os.getenv(key_var)
    if not key:
        return answer
    payload = {
        "model": os.getenv(model_var, default_model), "temperature": 0, "max_tokens": 8,
        "messages": [
            {"role": "system", "content": "Choose answer presentation for a career question. "
             "Reply with exactly one word: brief or context. No explanation."},
            {"role": "user", "content": json.dumps({"question": question, "summary": answer["summary"],
                                                   "reason": answer["reason"]}, ensure_ascii=False)},
        ],
    }
    try:
        req = request.Request(endpoint, data=json.dumps(payload).encode("utf-8"),
                              headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with request.urlopen(req, timeout=5) as response:
            choice = json.load(response)["choices"][0]["message"]["content"].strip().lower()
        if choice in {"brief", "context"}:
            summary = answer["summary"] if choice == "brief" else f"{answer['summary']} {answer['reason']}"
            return {**answer, "provider": provider, "summary": summary}
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError):
        pass
    return answer


def get_ai_provider() -> BaseAIProvider:
    name = os.getenv("AI_PROVIDER", "template").strip().lower()
    providers = {"template": TemplateAIProvider, "openai": OpenAIProvider, "nvidia": NvidiaProvider}
    if name not in providers:
        raise ValueError(f"Unknown AI_PROVIDER {name!r}; choose template, openai, or nvidia")
    return providers[name]()
