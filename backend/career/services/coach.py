from __future__ import annotations

from typing import Any

from career.models import Employee

from .engine import dashboard, recommendations, skill_gap


COPY = {
    "ru": {
        "no_goal": "Сначала выберите карьерную цель. После этого я смогу рассчитать разрыв навыков и следующий шаг.",
        "ready": "Готовность к цели {goal} сейчас составляет {score}%. Главные зоны роста: {gaps}.",
        "why": "Я рекомендую «{quest}», потому что: {reasons}. Ожидаемое изменение готовности: {before}% → {after}%.",
        "first": "Начните с «{quest}». {lock}",
        "lock": "Сначала нужен путь разблокировки: {chain}.",
        "unlocked": "Все prerequisites выполнены, квест можно начинать сразу.",
        "weak": "Самые заметные разрывы: {gaps}. Критические навыки отмечены отдельно в разделе Skills.",
        "fallback": "Следующий практичный шаг — «{quest}». Он связан с вашей целью и текущими разрывами навыков.",
    },
    "en": {
        "no_goal": "Choose a career goal first. Then I can calculate skill gaps and the next step.",
        "ready": "Readiness for {goal} is {score}%. The main growth areas are {gaps}.",
        "why": "I recommend “{quest}” because {reasons}. Expected readiness change: {before}% → {after}%.",
        "first": "Start with “{quest}”. {lock}",
        "lock": "Unlock it first through: {chain}.",
        "unlocked": "All prerequisites are met, so you can start immediately.",
        "weak": "The clearest skill gaps are {gaps}. Critical skills are marked separately on the Skills page.",
        "fallback": "The next practical step is “{quest}”. It matches your goal and current skill gaps.",
    },
    "kk": {
        "no_goal": "Алдымен мансаптық мақсатты таңдаңыз. Содан кейін дағды алшақтығын және келесі қадамды есептей аламын.",
        "ready": "{goal} мақсатына дайындық деңгейі {score}%. Негізгі даму аймақтары: {gaps}.",
        "why": "«{quest}» квестін ұсынамын, себебі: {reasons}. Дайындықтың болжамды өзгерісі: {before}% → {after}%.",
        "first": "Алдымен «{quest}» квестінен бастаңыз. {lock}",
        "lock": "Алдымен мына жолмен ашу керек: {chain}.",
        "unlocked": "Барлық prerequisites орындалған, квестті бірден бастауға болады.",
        "weak": "Негізгі дағды алшақтықтары: {gaps}. Маңызды дағдылар Skills бөлімінде бөлек белгіленген.",
        "fallback": "Келесі тиімді қадам — «{quest}». Ол мақсатыңызға және ағымдағы дағды алшақтығына сәйкес келеді.",
    },
}


def answer(employee: Employee, question: str, language: str = "ru") -> dict[str, Any]:
    language = language if language in COPY else "ru"
    copy = COPY[language]
    if not employee.career_goal:
        return {"answer": copy["no_goal"], "actions": [{"type": "navigate", "to": "career"}]}

    overview = dashboard(employee)
    recs = recommendations(employee)
    gaps = [item for item in skill_gap(employee) if item["gap"] > 0]
    gap_text = ", ".join(item["name"] for item in gaps[:3]) or "—"
    goal = f"{employee.career_goal['target_role']} / {employee.career_goal['target_grade']}"
    lowered = question.casefold()

    if any(token in lowered for token in ("готов", "readiness", "дайын", "стать", "become")):
        text = copy["ready"].format(goal=goal, score=overview["readiness"], gaps=gap_text)
    elif any(token in lowered for token in ("слаб", "weak", "әлсіз", "навык", "skill", "дағды")):
        text = copy["weak"].format(gaps=gap_text)
    elif not recs:
        text = copy["ready"].format(goal=goal, score=overview["readiness"], gaps=gap_text)
    else:
        quest = recs[0]
        lock_text = copy["unlocked"]
        if quest["locked"]:
            lock_text = copy["lock"].format(
                chain=" → ".join(item["title"] for item in quest["quest_chain"])
            )
        if any(token in lowered for token in ("почему", "why", "неге")):
            text = copy["why"].format(
                quest=quest["title"],
                reasons="; ".join(item["text"] for item in quest["reasons"]),
                before=quest["impact"]["readiness_before"],
                after=quest["impact"]["readiness_after"],
            )
        elif any(token in lowered for token in ("перв", "first", "алдымен", "нач")):
            text = copy["first"].format(quest=quest["title"], lock=lock_text)
        else:
            text = copy["fallback"].format(quest=quest["title"])

    actions = [{"type": "navigate", "to": "skills"}]
    if recs:
        actions.insert(
            0,
            {
                "type": "quest",
                "event_id": recs[0]["event_id"],
                "label": recs[0]["title"],
            },
        )
    return {"answer": text, "actions": actions, "context": {"employee_id": employee.external_id}}
