# Career Quest

Career Quest — демонстрационная внутренняя платформа развития сотрудников. Она показывает, каких навыков не хватает до выбранной карьерной цели, предлагает подходящие обучающие мероприятия и объясняет, как их прохождение меняет готовность к роли.

## Проблема и аудитория

Сотруднику сложно связать оценку навыков с конкретным планом роста. Career Quest превращает данные о навыках, требования к роли и каталог обучения в понятный маршрут. В версии для хакатона пользователь выбирает одного из синтетических сотрудников; реального SSO нет.

## Что реализовано

- Поиск и выбор сотрудника по имени, ID или роли.
- Dashboard с текущей позицией, целью, readiness, следующей рекомендацией, пробелами и XP.
- Effective Skills: baseline последней оценки плюс gains завершённых мероприятий после `last_review_date`, с `max_level`.
- Skill Gap, Critical Gap и weighted readiness с двойным весом критических навыков.
- Объяснимые рекомендации с фильтрами mandatory, completed, роли/грейда, prerequisites, причинами выбора и цепочками.
- Страницы «Карьера», «Навыки», «Квесты», «AI наставник», «Профиль»; смена цели в demo режиме.
- Start/Complete квеста, пересчёт навыков, readiness, XP, рангов и достижений. Повторное завершение отклоняется.
- Адаптивный интерфейс RU/EN/KK. Исходные англоязычные названия dataset остаются на исходном языке.
- AI Coach на основе структурированного контекста одного сотрудника; без API ключа действует детерминированное объяснение.

## Как работает решение

1. Импорт загружает `skills.json`, `employees.json`, `events.json` и `activity_history.csv` в базу, проверяя связи и внешние ID.
2. После выбора сотрудника backend вычисляет Effective Skills из последней оценки и истории.
3. Career Engine сравнивает навыки с профилем целевой роли, считает gaps и weighted readiness.
4. Recommendation Engine ранжирует мероприятия, возвращает причины и маршрут для заблокированных prerequisites.
5. Пользователь запускает доступный квест и завершает его в demo режиме. Backend атомарно записывает результат и XP; следующий запрос показывает обновлённые навыки и рекомендации.
6. AI Coach объясняет уже вычисленный результат и не выполняет действия с квестами.

## Технологии и архитектура

| Компонент | Реализация |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, React Router, CSS, словари RU/EN/KK |
| Backend | Python 3.12, Django 5.2, Django REST Framework |
| Данные | PostgreSQL в Docker Compose; SQLite локально без `DATABASE_URL` |
| AI | OpenAI Python SDK и Responses API, модель через `OPENAI_MODEL` (по умолчанию `gpt-5.4-mini`); без ключа — детерминированный режим |
| Проверка | pytest, pytest-django, TypeScript compiler, Vite build |

Поток: **браузер → REST API Django → Career Engine → ORM/база**. Импорт расположен в management command. AI получает ограниченный контекст из Career Engine и обращается к провайдеру только с backend. Формулы и ранжирование находятся в `backend/core/services.py`.

## Установка и запуск

### Docker Compose

Нужны Docker и Docker Compose.

```bash
cp .env.example .env
# Укажите в .env свой DJANGO_SECRET_KEY.
docker compose up --build
```

Откройте [http://localhost:8080](http://localhost:8080). Backend применяет миграции и импортирует dataset. PostgreSQL поднимается рядом. Для AI добавьте `OPENAI_API_KEY` в `.env` и перезапустите backend; подробности в [AI_SETUP.md](AI_SETUP.md).

### Без Docker

Нужны Python 3.12+, Node.js и pnpm.

```bash
cd backend
python -m venv .venv
# Активируйте .venv для своей ОС.
pip install -r requirements.txt
python manage.py migrate
python manage.py import_career_dataset --path ../datasets/career_quest
DEMO_MODE=1 python manage.py runserver
```

В другом терминале:

```bash
cd frontend
corepack enable
pnpm install
pnpm dev
```

Откройте [http://localhost:5173](http://localhost:5173). В PowerShell задайте demo переменную командой `$env:DEMO_MODE='1'` перед запуском Django.

## Как проверить решение

1. Выберите **Marat Yessenov (E0001)**.
2. На Dashboard посмотрите цель Backend Engineer / Middle и рассчитанный readiness. Точное значение зависит от состояния demo базы.
3. В «Навыках» сравните current и required. В «Квестах» найдите заблокированное мероприятие, его prerequisite и цепочку.
4. Запустите доступный **System Design Fundamentals** и нажмите «Завершить». Результат покажет XP, изменение навыков и readiness.
5. Посмотрите обновлённые рекомендации: завершённое мероприятие исключено, следующий шаг пересчитан.
6. Спросите AI наставника «Что мне делать дальше и почему?». Без ключа он даст детерминированный ответ.
7. Переключите RU → ҚАЗ → EN и проверьте мобильную ширину.

Для повторения demo с нуля выполните `python manage.py reset_demo` в `backend/`. Для проверки кода:

```bash
cd backend && pytest -q
cd ../frontend && pnpm build
```

## Данные, API и интеграции

Синтетический dataset Case 1 находится в `datasets/career_quest/`: 200 сотрудников, 60 навыков, 32 профиля ролей/грейдов, 40 мероприятий и 2743 записи истории. Импорт повторяем по внешним ID. Новые записи того же формата не требуют хардкода employee ID.

REST API начинается с `/api/v1/`. Основные endpoint: `employees/`, `employees/{id}/dashboard/`, `employees/{id}/skills/`, `employees/{id}/career/`, `employees/{id}/recommendations/`, `employees/{id}/quests/`, `quests/{event_id}/start/`, `quests/{event_id}/complete/`, `ai/chat/`, `health/`. POST действий передаёт `employee_id` в JSON. Единственный внешний сервис AI режима — OpenAI API; без ключа приложение работает локально.

## Ограничения

- Demo Employee Selector заменяет авторизацию. Для production необходимо связать сотрудника с Django authentication/SSO и запретить запросы по произвольному `employee_id`. `DEMO_MODE=0` блокирует demo завершение и смену цели, но selector остаётся демонстрационным.
- Завершение квеста симулирует обучение; внешней LMS, реальной сертификации и HRIS интеграции нет.
- Тексты мероприятий и названия ролей приходят из англоязычного dataset и не переводятся автоматически.
- Достижения вычисляются из текущего прогресса без отдельной истории награждения. Произвольный повтор repeatable мероприятий через demo action пока не поддержан.
- Публичной deployed версии нет. Адрес `localhost` доступен только на машине, где запущен проект.

Командные правила и исходные материалы сохранены в `AGENTS.md`, `TEAM_WORKFLOW.md`, `datasets/` и `docs/`.
