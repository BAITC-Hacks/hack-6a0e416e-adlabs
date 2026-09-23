# Перед защитой

- [ ] Из корня: `.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`.
- [ ] Во втором терминале: `npm --prefix frontend run dev`; открыть `http://127.0.0.1:5173/`.
- [x] Использовать `AI_PROVIDER=template` (режим по умолчанию). GPT/OpenAI и NVIDIA API-ключи не подключены; Navigator работает без них. Не заявлять внешние LLM-вызовы в демо.
- [ ] После локального добавления ключей запустить `scripts/check_ai_providers.py` и `scripts/eval_ai_providers.py`, выбрать primary по проверенному качеству и задержке.
- [ ] После live-проверки перезапустить backend, задать вопрос в браузере и сверить фактический provider и evidence IDs.
- [x] Перезапустить API для чистой симуляции; E0100 выбран по умолчанию.
- [x] Проверить `GET /api/health` и открыть профиль E0100.
- [x] Запустить `.\.venv\Scripts\python.exe -m pytest backend/tests tests -q --basetemp .pytest_local`.
- [x] Запустить `npm --prefix frontend run typecheck` и `npm --prefix frontend run build`.
- [x] Запустить `.\.venv\Scripts\python.exe scripts\demo_smoke_test.py`.
- [ ] Проверить браузер 100% на 1366×768 (также 1440×900 и 1920×1080); нет горизонтального скролла, консоль чистая.
- [ ] Пройти `Войти → Активности → Подробнее → Записаться → Начать → Отметить выполненным`; готовность 71,9→81,2%.
- [x] Проверить новый вопрос сравнения и вопрос про четыре часа в Navigator **после перезапуска backend**; оба отвечают без 422.
- [ ] Открыть HR-обзор перед показом.
- [ ] Резерв: API JSON, smoke test, сохранённые скриншоты; прямо назвать симуляцию.
