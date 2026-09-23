# Подключение AI Career Coach

Career Engine рассчитывает навыки, gaps, readiness и рекомендации на backend. AI Coach получает только готовый контекст выбранного сотрудника и объясняет его; модель не меняет состояние квестов.

## OpenAI API

1. Создайте API key в [OpenAI API dashboard](https://platform.openai.com/api-keys).
2. Скопируйте `.env.example` в `.env` в корне проекта.
3. Впишите `OPENAI_API_KEY=...` **только в локальный .env или secret manager сервера**. Не добавляйте ключ в Git и не используйте переменные `VITE_*`.
4. При необходимости задайте `OPENAI_MODEL=gpt-5.4-mini` или другую модель с поддержкой Responses API, доступную вашему проекту.
5. Запустите `docker compose up --build` или перезапустите backend после изменения переменных.
6. Откройте AI Coach, выберите сотрудника и задайте вопрос. `POST /api/v1/ai/chat/` принимает `{"employee_id":"E0001","message":"Что делать дальше?"}` и возвращает `{"answer":"...","mode":"openai"}`.

Если ключ не задан, тот же endpoint возвращает `mode: "deterministic"` с кратким объяснением readiness, пробелов и следующего мероприятия. Это позволяет показывать демо без внешнего сервиса. Если провайдер недоступен, endpoint возвращает код `AI_PROVIDER_UNAVAILABLE`; ключ и ответ провайдера в ошибку не выводятся.

Реальный запрос выполняет backend через официальный Python SDK `OpenAI().responses.create(...)`, передавая `model`, `instructions`, `input` и `store=False`. Список данных ограничен профилем одного сотрудника и первыми пятью рекомендациями. Вопрос обрезается до 1000 символов; на API действует базовый throttle DRF. Для production следует добавить корпоративную авторизацию, отдельный лимит на AI запросы, аудит доступа и политику хранения данных.

Справка: [официальный OpenAI quickstart](https://developers.openai.com/api/docs/quickstart), [безопасность API ключей](https://developers.openai.com/api/docs/guides/production-best-practices), [модель GPT-5.4 Mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
