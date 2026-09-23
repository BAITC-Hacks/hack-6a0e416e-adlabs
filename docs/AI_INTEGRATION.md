# AI Navigator: состояние интеграции

## Граница ответственности

`ml.engine` рассчитывает skill gap, ranking, top-3, score breakdown, projected impact и roadmap. AI Navigator получает готовый evidence packet и только объясняет результат. Запись и завершение активности остаются демо-симуляцией в памяти API; полноценное обучение проходит во внешней корпоративной LMS.

## Проверено 23 сентября 2026

| Компонент | Состояние |
| --- | --- |
| TemplateAIProvider | Работает offline; браузер и smoke test подтверждены |
| OpenAIProvider | Адаптер реализован, mock HTTP тесты прошли; живой ключ отсутствует |
| NvidiaProvider | Адаптер реализован, mock HTTP тесты прошли; живой ключ отсутствует |
| A/B и выбор primary | BLOCKED_BY_MISSING_KEY; реальных ответов и latency нет |

Выполнено **0 реальных API-запросов**. Пока нельзя заявлять, что OpenAI или NVIDIA уже работает в демо, или выбирать primary по качеству.

## Проверка после добавления ключей

1. Заполнить только локальный игнорируемый Git файл `.env` из `.env.example`. Не вставлять ключи в чат, логи или Git.
2. Установить `AI_PROVIDER=nvidia`, `AI_FALLBACK_PROVIDER=openai` либо обратный порядок.
3. Запустить `.\.venv\Scripts\python.exe scripts\check_ai_providers.py`: по одному минимальному вызову к каждому API, Pydantic schema и latency.
4. Запустить `.\.venv\Scripts\python.exe scripts\eval_ai_providers.py`: пять evidence packets, один ответ каждого провайдера на кейс, без повторных попыток. Просмотреть факты и русскоязычные ответы вручную вместе с автоматическими метриками.
5. Выбрать primary по достоверности, структуре ответа и задержке. Нестабильный сервис не ставить в основной demo flow. TemplateAIProvider остаётся последним fallback.
6. Перезапустить backend, задать вопрос в браузере, сверить badge, `GET /api/ai/status` и `evidence_ids` с исходным packet.

Финальная проверка кода без live-ключей: 23 backend-теста прошли; frontend typecheck и build прошли; demo smoke test: E0100 71,9% → 81,2%. Оба live-скрипта возвращают `BLOCKED_BY_MISSING_KEY`.
