# Правила, анкета и планы: проверка 27.09.2026

Результат — готовая локальная реализация r5 поверх незавершённой r4.
Это новый фактический запуск: **85 backend-тестов PASS**, 2 прежних предупреждения
Starlette/httpx/anyio; **20 шагов DATA-API PASS**, TypeScript/Vite и Docker PASS.
Исторические 71 тест / 17 шагов здесь не переименованы в новый результат.

## Сохранность и границы

Перед изменениями сохранены все изменённые и новые файлы начального checkout:
tmp/rules-start-20260927-224058. Коммиты/сброс/очистка чужих изменений не выполнялись.
Основная БД, её app, прежний QA app и VPS не пересоздавались. Только выделенная
navigator_test на opora-apk-qa-r4 использовалась для pytest/миграционной проверки.
Новый сквозной стенд: opora-apk-qa-rules, localhost:8002, том
opora-apk-qa-rules_release_data, отдельный образ opora-apk-qa-rules:20260927.

Изменённые/добавленные этим этапом файлы:

backend/app/{schemas,models,matching,catalog,api,questions,seed}.py;
backend/migrations/versions/20260927_round_acceptance.py;
backend/import_official.py, backend/check_restart.py, backend/check_data_api.py,
backend/check_rules_qa.py, backend/check_plan_migrations.py, backend/hash_sources.py;
backend/tests/test_plan_assessment_contract.py и test_{core,release,validity,official}.py;
frontend/src/main.tsx, frontend/src/api/schema.d.ts; docs/openapi.json, DATA-API.yaml;
data/official/reviews/{farm,students}-20260927.json, data/official/catalog.json;
compose.qa-rules.yaml; ARCHITECTURE.md, docs/PROGRESS.md, docs/HANDOFF-20260927.md,
docs/CATALOG-REVIEW.md, docs/RULES-PLAN-QA-20260927.md, docs/qa/rules-*.png,
docs/SOURCE-SHA256.txt.

## Фактически выполненные проверки

1. Полный backend: 85 PASS (последний запуск 3.82 с). Новый набор проверяет
   точные денежные границы; manual UNKNOWN при заполненных косвенных признаках;
   нормализацию денежных ответов; отдельную свежесть приёма; будущую дату проверки;
   неизменный снимок второго отбора при архивировании; чужого владельца;
   старый JSON без новых полей; часовой пояс подтверждения без дубликата импорта.
   Существующие проверки региона, года, состава, версий, подписей, CSRF,
   авторизации, повторных событий и публикации конфликтных записей также пройдены.
2. Проверка старой SQL-схемы: downgrade/upgrade выполнены **только navigator_test**.
   До upgrade создан старый план без assessment с архивной версией и отметкой.
   После двух миграций совпали вся старая строка плана, профиль, владелец, ревизия,
   ID и список документов. assessment=null, acceptance=unconfirmed/null.
   Alembic head=20260927_round_acceptance; check: No new upgrade operations detected.
3. Сборщик каталога: 10 реальных draft, публикации нет. import_official.py
   без --apply: формат валиден, БД не изменена. Две конфликтные версии по-прежнему
   отвергаются штатной публикацией в тестах. Источники заново не исследовались.
4. OpenAPI экспортирован из приложения; тест соответствия docs/openapi.json PASS.
   openapi-typescript 7.13.0; tsc -b и Vite 7.3.6 PASS в Node 24.14.1-alpine.
   JS index-BZHmlymF.js; CSS index-CRVhvWp4.css. Дизайн/CSS не изменялись.
5. Docker build отдельного образа PASS. Финальный image ID:
   sha256:e4617172c50f5e20e40d6f4caf5bd3121eae4af41bba454a0bbac128132999d1.
   Это сборка с кэшем и уже доступными образами, не новое измерение чистой сборки.
6. DATA-API: 20 PASS на финальном образе без bind исходников. Последний шаг
   находит именно сохранённый plan_id и сравнивает весь assessment после правки
   профиля, включая version_id и round.id. Работа только в локальном demo.
7. check_rules_qa.py создаёт полностью вымышленную меру через create → review →
   publish. Проверены 3 динамических вопроса, пустой/2025/2026 год,
   ручной UNKNOWN, выбор второго отбора и URL, неизменность оценки после правки
   анкеты/отметки, запрет второму владельцу. Реальные черновики для этого не
   переводились в verified. После restart db/app сравнение полного состояния PASS.
8. После последней сборки повторены DATA-API и check_restart.py before/after:
   профиль, все планы целиком (включая assessment), документы, версии и ID
   совпали после restart. SHA-снимок: tmp/rules-final-persistence.json и
   /tmp/rules-final-persistence.json внутри текущего QA app.
9. Визуально в отдельном встроенном браузере: вопросы третьего шага, точная
   сумма 3000000.01, сохранение пустого года и UNKNOWN в объяснении; семейное
   FAIL отдельно, документальный UNKNOWN отдельно; предупреждение profile_changed;
   старые ответы/причины; план открывает SYNTHETIC-SECOND и URL портала вместо
   первого отбора. Клавиатурная активация сработала; автоматические клики в этом
   браузере не давали изменения. Это браузерная проверка, не проверка MAX/телефона.
   Снимки: qa/rules-plan-20260927.png, qa/rules-unknown-20260927.png.

Первый backend-запуск: 70 PASS / 4 FAIL — старые фикстуры считали announced
достаточным для open; также выявлено влияние будущей даты подтверждения closed.
Фикстуры и временная проверка исправлены; затем 84 PASS и финально 85 PASS.
Windows npm run generate:api/build первоначально не прошли из-за отсутствия
исполняемого openapi-typescript/несовместимых локальных node_modules. Успешная
генерация и сборка выполнены в штатном Linux Node-контейнере. Старый пользовательский
tsconfig.tsbuildinfo восстановлен из начальной копии; зависимости не менялись.

Автоматическая проверка безопасности отклонила попытку чтения фокуса Vivaldi
с авторизованной вкладкой MAX как риск посторонних данных. Работа с этим окном
прекращена; весь необходимый UI-сценарий выполнен в отдельной QA-вкладке.

## Точные команды

Из корня C:\EffectiveBusiness (PowerShell). Пароль ниже относится только
к заранее выделенной локальной тестовой БД из compose.release-check.yaml.

```powershell
docker run --rm --network opora-apk-qa-r4_default -e APP_ENV=test -e SEED_DEMO=false -e DATABASE_URL=postgresql+psycopg://navigator:isolated-demo-only@db:5432/navigator_test -e TEST_DATABASE_URL=postgresql+psycopg://navigator:isolated-demo-only@db:5432/navigator_test -v C:/EffectiveBusiness/backend:/app/backend:ro -v C:/EffectiveBusiness/data:/app/data:ro -v C:/EffectiveBusiness/docs:/app/docs:ro opora-apk-qa-rules:20260927 sh -c 'python backend/check_plan_migrations.py && python backend/import_official.py && pytest backend/tests -q -p no:cacheprovider'
docker run --rm -v C:/EffectiveBusiness:/project -w /build node:24.14.1-alpine sh -c 'cp /project/frontend/package*.json . && npm ci --no-fund --no-audit && ./node_modules/.bin/openapi-typescript /project/docs/openapi.json -o /project/frontend/src/api/schema.d.ts && cp -r /project/frontend/src /project/frontend/index.html /project/frontend/tsconfig.json /project/frontend/vite.config.ts . && npm run build'
docker build -t opora-apk-qa-rules:20260927 .
docker compose -f compose.qa-rules.yaml up -d --wait
docker compose -f compose.qa-rules.yaml exec -T app alembic -c backend/alembic.ini current
docker compose -f compose.qa-rules.yaml exec -T app alembic -c backend/alembic.ini check
docker cp DATA-API.yaml opora-apk-qa-rules-app-1:/app/DATA-API.yaml
docker compose -f compose.qa-rules.yaml exec -T app python backend/check_data_api.py --base-url http://localhost:8000
# Выполнено один раз на новом QA. Повторное создание намеренно запрещено скриптом:
docker compose -f compose.qa-rules.yaml exec -T app python backend/check_rules_qa.py --base-url http://localhost:8000
# Первая проверка после restart, до последующей пересборки контейнера:
docker compose -f compose.qa-rules.yaml exec -T app python backend/check_rules_qa.py --base-url http://localhost:8000 --verify
# Финальная воспроизводимая проверка текущего образа:
docker compose -f compose.qa-rules.yaml exec -T app python backend/check_restart.py before --base-url http://localhost:8000 --snapshot /tmp/rules-final-persistence.json
docker compose -f compose.qa-rules.yaml restart db app
docker compose -f compose.qa-rules.yaml up -d --wait
docker compose -f compose.qa-rules.yaml exec -T app python backend/check_restart.py after --base-url http://localhost:8000 --snapshot /tmp/rules-final-persistence.json
```

Для сборщика и экспорта OpenAPI фактически использовался прежний opora-apk-app
с read-only backend и writable data/docs: python data/official/build_catalog.py;
python backend/export_openapi.py. Изменения БД применялись лишь к navigator_test.
Первый /tmp/rules-qa.json исчез при последующем **пересоздании** app (не restart);
для текущего стенда используйте финальный check_restart.py и сохранённый SHA-снимок.
Скрипты проверки изменяют только синтетический профиль; не запускать их в рабочей БД.

## Передача проверке/размещению

- Начать с git status, AGENTS, HANDOFF и этого отчёта. Текущий QA localhost:8002
  оставлен доступным; localhost:8000 и VPS остаются r3, localhost:8001 — прежняя r4.
- До миграции рабочей БД: сравнить исходники VPS с r3-манифестом, проверить backup
  и восстановление отдельно. Новая цепочка: 20260918_one_published →
  20260927_plan_assessment → 20260927_round_acceptance. Рабочая миграция здесь
  не выполнялась; проверить реальные старые планы/права двух аккаунтов после неё.
- Real publication-ready = 0. Студенты и семейный грант сохраняют conflict,
  missing_evidence, verified_at=null. Семейный review теперь r5, добавлены лишь
  подтверждённые границы суммы; обе записи имеют отдельный closed по уже
  имеющимся снимкам портала. Не изменять даты проверки ради публикации.
- При готовности доказательств создавать отдельные draft штатным
  import_official.py --apply --stage-revision saratov-farm (или saratov-students),
  затем preview → review → publish. Текущие файлы ещё не stage-импортированы
  ни в обычную локальную БД, ни на VPS. Автоматической публикации нет.
- Перед открытием нового приёма отдельно подтвердить редакцию, регион,
  точные сроки/часовой пояс, официальный маршрут и acceptance_checked_at.
  Действующее календарное окно само по себе больше не означает open.
- Проверить новую сборку в web-MAX и Android, второй реальный аккаунт; iOS
  остаётся непроверенным. Пользовательские результаты прежней r3 не засчитывать.
  Нужны реальная редакторская роль, завершение юридических блокеров и полноценный
  проход плана до официального ресурса после разрешённого размещения.
- Никаких других чатов/агентов не привлекалось; публикации, VPS и Git push не было.

Финальная сверка: git diff --check — PASS (только прежние LF/CRLF warnings); все исходные изменённые/новые пути сохранены; 8 остальных записей каталога побайтно эквивалентны после нормализации JSON. QA healthy: 7 synthetic/published, 0 real. Итоговый viewport-снимок плана заменяет промежуточный full-page со склейкой. SOURCE-SHA256 пересчитан после документации и снимков. Каталог docs/qa уже исключён существующим .gitignore; снимки доступны локально и включены в манифест, передавать их отдельно при Git-only переносе.
