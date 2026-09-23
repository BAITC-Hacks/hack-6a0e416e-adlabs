# Career Quest

Career Quest - hackathon MVP для персонального развития сотрудников. Система помогает сотруднику выбрать карьерную цель, увидеть разрыв навыков до целевой роли и получить объяснимые рекомендации по обучающим активностям. Для HR доступен агрегированный обзор по навыкам и участию без публичного рейтинга сотрудников.

## Что решает проект

В компаниях часто есть данные о сотрудниках, навыках и обучении, но сотруднику сложно понять, какие активности реально приблизят его к следующей роли. HR, в свою очередь, нужен быстрый обзор общих разрывов и участия в обучении.

Career Quest превращает такие данные в понятный сценарий:

- сотрудник выбирает профиль и карьерную цель;
- система считает готовность к цели и критические gaps;
- сотрудник получает ранжированные рекомендации;
- после старта и завершения квеста прогресс пересчитывается;
- AI Coach объясняет рекомендации на RU/EN/KZ;
- HR видит агрегированную картину по команде.

## Что реализовано

- Выбор демо-сотрудника из датасета.
- Личный dashboard с текущей ролью, целевой ролью, readiness, XP, rank progress и достижениями.
- Расчет baseline/effective skills и разрыва до целевого role profile.
- Выбор карьерной цели из валидных комбинаций role/grade.
- Рекомендации обучающих активностей с объяснениями: соответствие цели, влияние на навыки, история участия.
- Quest flow: recommended, active и completed квесты.
- Проверка prerequisites: заблокированные активности показывают цепочку разблокировки.
- Старт и завершение квеста через API с идемпотентной обработкой.
- Пересчет readiness, effective skills, XP и рекомендаций после завершения активности.
- Детерминированный AI Coach на русском, английском и казахском языках.
- HR overview: агрегированные gaps, participation statuses, сотрудники без цели и сотрудники без доступного следующего шага.
- Docker Compose запуск frontend, backend и PostgreSQL.
- Backend и frontend тесты, lint/build проверки, CI workflow.

## Как работает решение

1. Backend загружает датасет из `datasets/career_quest`: сотрудников, навыки, role profiles, обучающие события и историю участия.
2. Пользователь выбирает сотрудника в интерфейсе.
3. Career Engine рассчитывает effective skills: базовые навыки сотрудника плюс завершенные активности из истории.
4. Для выбранной карьерной цели система сравнивает effective skills с требованиями `role_profiles`.
5. Backend возвращает readiness, критические gaps, рекомендации и quest chain.
6. Frontend показывает dashboard, skills, career route, quests и AI Coach.
7. При старте/завершении квеста backend проверяет доступность активности, обновляет демо-состояние и пересчитывает результат.
8. HR режим использует агрегированные данные и не раскрывает приватный рейтинг сотрудников.

## Технологии

### Backend

- Python
- Django 5
- Django REST Framework
- django-cors-headers
- PostgreSQL в Docker Compose
- SQLite для легкого локального запуска и тестов
- Gunicorn для контейнерного запуска

### Frontend

- React
- TypeScript
- Vite
- React Router
- lucide-react
- Vitest
- Testing Library
- ESLint
- Nginx для production-контейнера frontend

### AI и внешние сервисы

- В текущей версии AI Coach реализован как контролируемый детерминированный слой поверх данных Career Engine.
- Внешние LLM/API ключи не требуются.
- Ответы Coach не придумывают новые факты: они строятся на рассчитанных gaps, readiness и рекомендациях.

## Архитектура проекта

```text
datasets/career_quest
        |
        v
backend/career
  Django REST API
  Career Engine
  deterministic AI Coach
        |
        v
frontend/src
  React/Vite UI
  employee mode
  HR mode
```

Основные директории:

| Путь | Назначение |
| --- | --- |
| `backend/` | Django backend, REST API, модели, импорт датасета, Career Engine |
| `backend/career/services/engine.py` | Расчеты readiness, skill gaps, recommendations, quest chains, XP |
| `backend/career/services/coach.py` | Детерминированные ответы AI Coach на RU/EN/KZ |
| `frontend/` | React + TypeScript интерфейс |
| `datasets/career_quest/` | Синтетический датасет проекта |
| `contracts/` | API contract, demo flow и env contract |
| `.github/workflows/ci.yml` | CI проверки backend, frontend и compose smoke |
| `compose.yml` | Docker Compose для PostgreSQL, backend и frontend |

## Данные

Датасет находится в `datasets/career_quest`.

| Файл | Содержимое |
| --- | --- |
| `skills.json` | Каталог навыков, шкала 0-5, требования к ролям и грейдам |
| `employees.json` | 200 синтетических профилей сотрудников |
| `events.json` | 40 обучающих мероприятий |
| `activity_history.csv` | 2 743 записи истории участия |

Дата среза данных: `2026-10-01`.

Все люди и компании в датасете вымышлены. Подробнее структура данных описана в `datasets/career_quest/README.ru.md`.

## Установка и запуск

### Вариант 1: Docker Compose

Нужен Docker с Compose.

```bash
docker compose up --build
```

После запуска откройте:

- Frontend: <http://localhost:5173>
- API health: <http://localhost:8000/api/v1/health/>

Backend при старте применяет миграции и импортирует датасет. PostgreSQL данные сохраняются в volume `career_quest_db`.

Чтобы полностью сбросить локальное состояние Compose:

```bash
docker compose down -v
docker compose up --build
```

### Вариант 2: локальный запуск без Docker

Нужны Python 3 и Node.js.

Backend:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py import_career_dataset
.venv/bin/python backend/manage.py runserver 0.0.0.0:8000
```

Frontend во втором терминале:

```bash
cd frontend
npm ci
npm run dev
```

Откройте <http://localhost:5173>.

## Как проверить решение жюри

Быстрый сценарий на 4-5 минут:

1. Откройте <http://localhost:5173>.
2. Выберите сотрудника `E0001`.
3. На dashboard проверьте целевую роль, readiness, critical gaps, next best quest, XP, rank и achievements.
4. Откройте рекомендованный квест и посмотрите объяснения рекомендации.
5. Перейдите в раздел **Quests**.
6. Найдите пример заблокированной активности: prerequisites показывают цепочку разблокировки.
7. Запустите и завершите `EV_005`.
8. Вернитесь на dashboard и убедитесь, что readiness, effective skills, XP и рекомендации пересчитались.
9. Откройте **AI Coach**, задайте вопрос вроде `Почему рекомендован этот квест?`.
10. Переключите язык RU/EN/KZ и проверьте локализованные ответы.
11. Перейдите в **Career**, выберите другую валидную роль/грейд и сохраните цель.
12. Переключитесь в **HR** и посмотрите aggregate gaps, participation statuses и списки сотрудников без цели/следующего шага.

Готовый demo flow также описан в `contracts/demo-flow.md`.

## API

Base URL:

```text
http://localhost:8000/api/v1
```

Основные endpoint'ы:

| Method | Path | Назначение |
| --- | --- | --- |
| `GET` | `/health/` | Проверка состояния API |
| `GET` | `/employees/` | Поиск и выбор сотрудника |
| `GET` | `/employees/{employee_id}/dashboard/` | Dashboard сотрудника |
| `GET` | `/employees/{employee_id}/skills/` | Навыки и gaps |
| `GET` | `/employees/{employee_id}/career/` | Карьерная цель и route |
| `POST` | `/employees/{employee_id}/career-goal/` | Обновление карьерной цели |
| `GET` | `/employees/{employee_id}/recommendations/` | Рекомендации |
| `GET` | `/employees/{employee_id}/quests/` | Квесты |
| `POST` | `/quests/{event_id}/start/` | Старт квеста |
| `POST` | `/quests/{event_id}/complete/` | Завершение квеста |
| `POST` | `/ai/chat/` | Ответ AI Coach |
| `GET` | `/hr/overview/` | HR overview |

Подробный контракт находится в `contracts/api.md`.

## Проверки и тесты

Backend:

```bash
.venv/bin/python backend/manage.py test career
```

Frontend:

```bash
cd frontend
npm run lint
npm test
npm run build
```

В CI эти проверки повторяются для push и pull request. Также workflow содержит Compose smoke test.

## Конфигурация

Пример переменных окружения лежит в `.env.example`.

Для Docker Compose основные значения уже имеют defaults:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `CAREER_DATASET_PATH`
- `CAREER_SNAPSHOT_DATE`
- `VITE_API_BASE_URL`

Для локальной разработки можно скопировать `.env.example` в `.env` и изменить значения под свою среду.

Если запускаете backend локально без Docker и хотите использовать SQLite, не задавайте `POSTGRES_HOST`. При наличии `POSTGRES_HOST` Django будет пытаться подключиться к PostgreSQL.

## Ограничения текущей версии

- Это hackathon MVP, а не production HRIS/LMS система.
- Данные синтетические; реальные персональные данные не используются.
- Изменения квестов и прогресса предназначены для демо-сценария.
- AI Coach не подключен к внешней LLM и отвечает по детерминированным шаблонам.
- Интеграции с корпоративными LMS, HRIS, SSO и календарями не реализованы.
- Нет deployed-версии, подтвержденной в репозитории; проект запускается локально через Docker Compose или dev-серверы.

## Deployed-версия

В репозитории нет подтвержденной ссылки на deployed-версию.

## Полезные документы

- `contracts/api.md` - API contract
- `contracts/demo-flow.md` - сценарий демонстрации
- `contracts/env.md` - переменные окружения
- `datasets/career_quest/README.ru.md` - описание датасета
- `AGENTS.md` - правила работы команды Codex
- `TEAM_WORKFLOW.md` - командный workflow
