"""Explanation providers. Recommendations and ranking always come from ml.engine."""

import os
from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    @abstractmethod
    def explain(self, recommendation: dict, target: dict | None) -> str:
        """Explain a predetermined recommendation without changing its rank or impact."""


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
    """Optional future LLM explanation adapter; currently deterministic and keyless."""


class NvidiaProvider(TemplateAIProvider):
    """Optional future LLM explanation adapter; currently deterministic and keyless."""


def get_ai_provider() -> BaseAIProvider:
    name = os.getenv("AI_PROVIDER", "template").strip().lower()
    providers = {"template": TemplateAIProvider, "openai": OpenAIProvider, "nvidia": NvidiaProvider}
    if name not in providers:
        raise ValueError(f"Unknown AI_PROVIDER {name!r}; choose template, openai, or nvidia")
    return providers[name]()
