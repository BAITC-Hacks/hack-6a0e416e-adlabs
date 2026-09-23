# AI Navigator: состояние интеграции

## Граница ответственности

`ml.engine` рассчитывает skill gap, ranking, top-3, score breakdown, projected impact и roadmap. AI Navigator получает готовый evidence packet и только объясняет результат. Запись и завершение активности остаются демо-симуляцией в памяти API; полноценное обучение проходит во внешней корпоративной LMS.

## Проверено 23 сентября 2026

| Компонент | Состояние |
| --- | --- |
| TemplateAIProvider | Работает offline; браузер и smoke test подтверждены |
| OpenAIProvider | Живой вызов `gpt-4o-mini` прошёл; локально выбран primary |
| NvidiaProvider | Адаптер и mock HTTP тесты прошли; ключа нет, провайдер не выбран |
| Проверка качества | Пять evidence packets прошли schema, ID и numeric validation; фактическую корректность следует оценивать вручную |

Выполнены живой smoke check, пять eval-запросов и запросы к работающему backend. Для вопроса о смене роли API вернул `provider=openai`, а `/api/ai/status` показал `active_provider=openai`. NVIDIA остаётся неподключённым. Локальный `.env` игнорируется Git; ключ в репозитории отсутствует.

## Повторная проверка на другой машине

1. Заполнить только локальный игнорируемый Git файл `.env` из `.env.example`. Не вставлять ключи в чат, логи или Git.
2. Установить `AI_PROVIDER=openai`, `AI_FALLBACK_PROVIDER=template`; NVIDIA не требуется.
3. Запустить `.\.venv\Scripts\python.exe scripts\check_ai_providers.py`: один минимальный живой вызов выбранного API и проверка схемы.
4. Запустить `.\.venv\Scripts\python.exe scripts\eval_ai_providers.py`: пять evidence packets и ответы выбранного провайдера. Просмотреть фактическую точность вручную.
5. При ошибке внешнего API Navigator переключается на TemplateAIProvider.
6. Перезапустить backend, задать вопрос в браузере, сверить badge, `GET /api/ai/status` и `evidence_ids` с исходным packet.

OpenAI smoke check прошёл за 4–6 секунд; пять eval-вызовов заняли примерно 2,3–4,4 секунды каждый. Скрипты пропускают NVIDIA, если он не выбран. У одного из пяти кейсов эвристика `personalized` дала `False`; это не ошибка схемы, а повод проверить формулировку ответа вручную. Demo smoke test: E0100 71,9% → 81,2%.
