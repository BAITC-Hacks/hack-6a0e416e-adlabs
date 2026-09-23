from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.models import ChatTurn, Employee


@pytest.fixture
def employees(db, settings, monkeypatch):
    settings.ALLOWED_HOSTS = ["testserver"]
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return [Employee.objects.create(external_id=f"CHAT-{i}", full_name=f"Employee {i}",
            role="Engineer", grade="Junior", last_review_date=date.today(), baseline_skills={})
            for i in range(2)]


def history_url(employee):
    return f"/api/v1/employees/{employee.external_id}/chat-history/"


def ask(client, employee, message="Что делать дальше?"):
    return client.post("/api/v1/ai/chat/", {"employee_id": employee.external_id,
                       "message": message, "language": "ru"}, content_type="application/json")


def test_chat_survives_reload_and_is_scoped_to_employee(client, employees):
    first, second = employees
    response = ask(client, first)
    assert response.status_code == 200
    turn = response.json()["turn"]
    assert turn["mode"] == "deterministic"
    assert turn["question"] == "Что делать дальше?"
    assert turn["answer"] and turn["created_at"]
    assert client.get(history_url(first)).json()["turns"] == [turn]
    assert client.get(history_url(second)).json()["turns"] == []
    ask(client, second, "Моя цель?")
    assert client.delete(history_url(first)).status_code == 200
    assert client.get(history_url(first)).json()["turns"] == []
    assert second.chat_turns.count() == 1


def test_history_paginates_without_duplicates_and_validates_cursor(client, employees):
    first, second = employees
    for i in range(28):
        ChatTurn.objects.create(employee=first, question=str(i), answer="Reply", mode="deterministic")
    ChatTurn.objects.create(employee=second, question="Private", answer="Other", mode="deterministic")
    newest = client.get(history_url(first)).json()
    assert [t["question"] for t in newest["turns"]] == [str(i) for i in range(3, 28)]
    assert newest["has_more"] is True
    older = client.get(history_url(first), {"before": newest["next_before"]}).json()
    assert [t["question"] for t in older["turns"]] == ["0", "1", "2"]
    assert older["has_more"] is False and older["next_before"] is None
    for cursor in ("bad", "-1", "0", "9" * 30):
        assert client.get(history_url(first), {"before": cursor}).status_code == 400
    assert client.get("/api/v1/employees/unknown/chat-history/").status_code == 404


def test_openai_receives_recent_history_for_selected_employee(client, employees, monkeypatch):
    first, second = employees
    for i in range(12):
        ChatTurn.objects.create(employee=first, question=f"Question {i}", answer=f"Answer {i}", mode="openai")
    ChatTurn.objects.create(employee=second, question="Other employee", answer="Private", mode="openai")
    create = Mock(return_value=SimpleNamespace(output_text="Follow-up answer"))
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(create=create)))
    response = ask(client, first, "Расскажи подробнее")
    assert response.status_code == 200
    inputs = create.call_args.kwargs["input"]
    assert len(inputs) == 21
    assert inputs[0] == {"role": "user", "content": "Question 2"}
    assert inputs[-2] == {"role": "assistant", "content": "Answer 11"}
    assert "Расскажи подробнее" in inputs[-1]["content"]
    assert "Other employee" not in str(inputs) and "Private" not in str(inputs)
    assert create.call_args.kwargs["store"] is False
    assert first.chat_turns.last().answer == "Follow-up answer"
    assert first.chat_turns.count() == 13


@pytest.mark.parametrize("provider_result", [RuntimeError("provider failed"), SimpleNamespace(output_text="")])
def test_provider_failures_do_not_save_incomplete_turn(client, employees, monkeypatch, provider_result):
    create = Mock(side_effect=provider_result) if isinstance(provider_result, Exception) else Mock(return_value=provider_result)
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(create=create)))
    assert ask(client, employees[0]).status_code == 503
    assert employees[0].chat_turns.count() == 0
    assert ask(client, employees[0], "   ").status_code == 400
    assert create.call_count == 1
