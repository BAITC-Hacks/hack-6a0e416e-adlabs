"""Provider contract tests use HTTP mocks and cannot spend API credits."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.data import load_dataset
from backend.app.main import app
from backend.app.services.ai_provider import (
    NvidiaProvider, OpenAIProvider, ProviderError, TemplateAIProvider, get_ai_provider,
)
from backend.app.services.navigator import ask_navigator


def _case():
    data = load_dataset()
    answer = ask_navigator(data, "E0100", "Почему первая лучше второй?", "compare", None, None,
                           TemplateAIProvider())
    packet = answer.pop("_evidence_packet")
    return answer, packet


def _explanation(packet, **updates):
    value = {
        "summary": "Первый шаг учитывает текущий разрыв.",
        "why_recommended": ["Активность закрывает нужные навыки."],
        "expected_impact": ["Прогноз указан в расчёте."],
        "limitations": ["Повышение не гарантировано."],
        "next_step": "Проверьте условия участия.",
        "confidence": "medium",
        "evidence_ids": [packet["employee"]["employee_id"]],
    }
    value.update(updates)
    return value


def test_openai_structured_output_and_request(monkeypatch):
    answer, packet = _case()
    monkeypatch.setenv("OPENAI_API_KEY", "mock-only")

    def handler(request):
        payload = json.loads(request.content)
        assert request.url.path == "/v1/responses"
        assert payload["text"]["format"]["schema"]["additionalProperties"] is False
        assert payload["model"]
        return httpx.Response(200, json={"status": "completed", "output": [
            {"content": [{"type": "output_text", "text": json.dumps(_explanation(packet), ensure_ascii=False)}]}
        ]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = OpenAIProvider(client).rephrase(answer, "Почему?", packet)
    assert result["provider"] == "openai"
    assert result["ai_explanation"]["confidence"] == "medium"
    assert result["profile_facts"] == answer["profile_facts"]


def test_nvidia_structured_output_and_request(monkeypatch):
    answer, packet = _case()
    monkeypatch.setenv("NVIDIA_API_KEY", "mock-only")
    monkeypatch.setenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    def handler(request):
        payload = json.loads(request.content)
        assert request.url.path == "/v1/chat/completions"
        assert payload["messages"][0]["role"] == "system"
        return httpx.Response(200, json={"choices": [
            {"message": {"content": json.dumps(_explanation(packet), ensure_ascii=False)}}
        ]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = NvidiaProvider(client).rephrase(answer, "Почему?", packet)
    assert result["provider"] == "nvidia"


@pytest.mark.parametrize("status,reason", [(429, "rate_limit"), (401, "authentication_failed")])
def test_http_errors_are_safe(monkeypatch, status, reason):
    answer, packet = _case()
    monkeypatch.setenv("OPENAI_API_KEY", "mock-only")
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status))) as client:
        with pytest.raises(ProviderError, match=reason):
            OpenAIProvider(client).rephrase(answer, "Почему?", packet)


def test_unknown_id_and_number_rejected(monkeypatch):
    answer, packet = _case()
    monkeypatch.setenv("NVIDIA_API_KEY", "mock-only")
    for invalid in (_explanation(packet, evidence_ids=["EV_999"]),
                    _explanation(packet, summary="Прогноз 98765%.")):
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(invalid, ensure_ascii=False)}}]}
        ))) as client:
            with pytest.raises(ProviderError):
                NvidiaProvider(client).rephrase(answer, "Почему?", packet)


def test_timeout_is_safe_and_falls_back(monkeypatch):
    answer, packet = _case()
    monkeypatch.setenv("OPENAI_API_KEY", "mock-only")

    def timeout(request):
        raise httpx.ReadTimeout("timed out", request=request)

    with httpx.Client(transport=httpx.MockTransport(timeout)) as client:
        with pytest.raises(ProviderError, match="timeout"):
            OpenAIProvider(client).rephrase(answer, "Почему?", packet)


def test_route_falls_back_to_openai_then_template(monkeypatch):
    answer, packet = _case()
    monkeypatch.setenv("AI_PROVIDER", "nvidia")
    monkeypatch.setenv("AI_FALLBACK_PROVIDER", "openai")
    monkeypatch.setenv("NVIDIA_API_KEY", "mock-only")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-only")
    calls = []

    def fail_nvidia(self, answer, question, evidence_packet=None):
        calls.append("nvidia")
        raise ProviderError("rate_limit")

    def pass_openai(self, answer, question, evidence_packet=None):
        calls.append("openai")
        return {**answer, "provider": "openai"}

    monkeypatch.setattr(NvidiaProvider, "rephrase", fail_nvidia)
    monkeypatch.setattr(OpenAIProvider, "rephrase", pass_openai)
    assert get_ai_provider().rephrase(answer, "Почему?", packet)["provider"] == "openai"
    assert calls == ["nvidia", "openai"]
    monkeypatch.setattr(OpenAIProvider, "rephrase", fail_nvidia)
    assert get_ai_provider().rephrase(answer, "Почему?", packet)["provider"] == "template"


def test_reverse_route_tries_openai_then_nvidia(monkeypatch):
    answer, packet = _case()
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_FALLBACK_PROVIDER", "nvidia")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-only")
    monkeypatch.setenv("NVIDIA_API_KEY", "mock-only")
    calls = []

    def fail(self, answer, question, evidence_packet=None):
        calls.append("openai")
        raise ProviderError("timeout")

    def succeed(self, answer, question, evidence_packet=None):
        calls.append("nvidia")
        return {**answer, "provider": "nvidia"}

    monkeypatch.setattr(OpenAIProvider, "rephrase", fail)
    monkeypatch.setattr(NvidiaProvider, "rephrase", succeed)
    assert get_ai_provider().rephrase(answer, "Почему?", packet)["provider"] == "nvidia"
    assert calls == ["openai", "nvidia"]


def test_one_normalization_pass_accepts_safe_wrappers(monkeypatch):
    answer, packet = _case()
    monkeypatch.setenv("NVIDIA_API_KEY", "mock-only")
    value = _explanation(packet, why_recommended="Покрывает разрыв.")
    wrapped = "```json\n" + json.dumps(value, ensure_ascii=False) + "\n```"
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
        200, json={"choices": [{"message": {"content": wrapped}}]}
    ))) as client:
        result = NvidiaProvider(client).rephrase(answer, "Почему?", packet)
    assert result["ai_explanation"]["why_recommended"] == ["Покрывает разрыв."]


def test_status_never_exposes_keys(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_FALLBACK_PROVIDER", "nvidia")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-secret-openai")
    monkeypatch.setenv("NVIDIA_API_KEY", "mock-secret-nvidia")
    response = TestClient(app).get("/api/ai/status")
    assert response.status_code == 200
    body = response.json()
    assert body["configured_provider"] == "openai"
    assert body["fallback_provider"] == "nvidia"
    assert body["openai_configured"] and body["nvidia_configured"]
    assert "mock-secret" not in response.text
