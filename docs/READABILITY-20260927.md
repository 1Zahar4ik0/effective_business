# Читаемость исходного кода — 27.09.2026

По запросу пользователя удалены поясняющие комментарии и docstring из собственного исполняемого кода и конфигураций. Директивы shebang сохранены. Архивы источников, документация, зависимости и прежние резервные копии не очищались. Начальное состояние сохранено в tmp/readability-start-20260927-231543, существовавшие изменения не отменены.

Изменения: backend/**/*.py (44 файла вместе с data/official/build_catalog.py), шаблон миграций backend/migrations/script.py.mako; frontend/src/**/*.{ts,tsx,css}, frontend/index.html, frontend/vite.config.ts; compose*.yaml, .env.example, .gitignore, .gitattributes и deploy. Удалены 27 Python-комментариев и 24 docstring. Справка argparse и описание маршрута OpenAPI сохранены как явные строки. Код отформатирован Black 26.5.1 и Prettier 3.9.9 во временных контейнерах, без добавления зависимостей проекта. В matching.py объединены повторявшиеся сравнения, вложенные выражения заменены последовательными проверками. Новый frontend/scripts/generate-api.mjs подключён через package.json: генерация типов также удаляет комментарии. Дизайн и контракт API сохранены.

Фактически выполнено заново после этих изменений:

- pytest backend/tests -q -p no:cacheprovider: 85 passed, 2 прежних предупреждения библиотек; включая сравнение OpenAPI.
- alembic -c backend/alembic.ini upgrade head и alembic check: PASS на отдельной navigator_test.
- npm run generate:api и npm run build: PASS (TypeScript, Vite 7.3.6).
- docker build -t opora-apk-qa-rules:20260927 .: PASS; образ sha256:2bbec9a4bc4a553f282d9dcdcbd6da38ebceb48a1fc3a93b2261889c6556497b.
- docker compose -f compose.qa-rules.yaml up -d --wait: PASS, только синтетический QA localhost:8002.
- python backend/check_restart.py before/after --base-url http://localhost:8000 --snapshot /tmp/readability-persistence.json внутри QA, снимок скопирован через хост перед заменой контейнера: PASS, профили/планы/версии/полные оценки сохранены.
- docker exec opora-apk-qa-rules-app-1 python backend/check_data_api.py --base-url http://localhost:8000: 20 шагов PASS.
- Аудит относительно резервной копии: 43 Python-файла эквивалентны по AST с учётом намеренного переноса docstring; для изменённого matching.py совпали 379 случаев правил и 720 случаев доступности. Осталось 0 Python-комментариев/docstring. Отчёты tmp/readability-audit.json и tmp/readability-cleanup.json; воспроизводящий аудит tmp/readability-audit.py.

Основной localhost:8000, прежний QA:8001 и VPS не обновлялись. Браузерный/MAX-прогон после форматирования отдельно не повторялся; результаты предыдущего этапа находятся в RULES-PLAN-QA-20260927.md. Проверка размещения, миграция копии рабочей БД и реальные устройства остаются задачами следующего этапа. Реальные версии по-прежнему не опубликованы, редакторские проверки не обходились.
