# Передача правил и планов — 28.09.2026

## Результат

Технический сценарий локально проверен на синтетических данных: анкета → объяснимый подбор → карточка конкретного отбора → сохранённый план документов → официальный маршрут. Доработка продолжает существующую r5, не создаёт повторных полей requested_grant, expense_year, family_kfh_members, assessment, profile_changed или подтверждения приёма.

Реальный каталог **не готов к публикации: 0 готовых мер**, согласно завершённому чату каталога и HANDOFF-CATALOG.md от 28.09. Исследование юридических условий не завершено. Реальные черновики, reviews, notices и источники этим этапом не изменены и в рабочие БД не импортированы. VPS, рабочие БД, дизайн и зависимости приложения не изменялись. Новых полей анкеты нет: спецификация страховых фактов, партий зерна и ветвей кооперативных затрат пока требует завершённого источника.

## Изменения

- `Document.condition` — необязательное дерево существующего `Rule` с обязательным source_ref. Используется тот же серверный PASS/FAIL/UNKNOWN, без вычислений в React. Проверяются глубина и уникальность ID внутри дерева документа. Условия участия и применимости документа различаются: FAIL условия документа означает `not_applicable`, а не отказ в поддержке. UNKNOWN не скрывает документ.
- `evaluate_documents` возвращает `required` / `not_applicable` / `unknown`, полный `check` с дочерними причинами и исходное условие. Без condition документ сохраняет прежнее поведение обязательного пункта списка. Добровольность и межведомственный режим не выводятся из текста автоматически.
- `MatchView.documents` содержит эту оценку. Дополнительные вопросы читают также условия документов только опубликованных видимых версий, не раскрывая черновики.
- В новом плане список документов сохраняется вместе с применимостью и полными причинами; assessment содержит `engine_version=rules-20260928.1`. Ранее реализованные снимки версии, редакции, выбранного отбора, маршрута, времени, анкеты и причин сохранены. Оценка документов относится к тому же профилю/версии и моменту assessment.
- Повтор POST, новая анкета, PATCH отметки и новый подбор не переписывают старый план. `profile_changed` сохраняет прежнюю семантику; новый подбор даёт новый Evaluation с актуальными документами. Кнопка сохранения уже существующего отбора возвращает старый план — отдельного интерфейса замены/переоценки плана нет.
- UI показывает применимость, условие и ссылку на пункт, объясняет исторический характер ответов и счётчика. Пункты не скрываются и могут быть отмечены как подготовленные даже при неизвестной применимости; это только отметка пользователя, которая не доказывает право или обязательность документа.

Файлы: backend/app/{schemas,matching,api,questions}.py; backend/check_rules_qa.py; backend/tests/test_conditional_documents_20260928.py; frontend/src/main.tsx и api/schema.d.ts; docs/openapi.json; compose.qa-rules-20260928.yaml; backend/hash_sources.py; ARCHITECTURE.md, PROGRESS.md, этот файл, docs/qa/rules-plan-20260928.png и SOURCE-SHA256.txt. frontend/tsconfig.tsbuildinfo проверен сборкой и совпал с исходным файлом.

## Совместимость и миграции

Новой SQL-миграции нет: additions хранятся в существующих JSON документов/плана. Поля condition, check, applicability и engine_version совместимы с отсутствием значения в старых записях. Старые JSON не дополняются при чтении; отдельный тест сверяет данные непосредственно в PostgreSQL. Не запускать массовое заполнение снимков задним числом.

При последующем размещении остаётся необходимой ранее созданная цепочка:
`20260918_one_published` → `20260927_plan_assessment` → `20260927_round_acceptance`.
Голова проверена через upgrade/check. Старые ответы, владельцы, ID, архивный отбор, ревизия и отметки сохранились при проверке старой схемы; старый приём остался unconfirmed, assessment не выдуман.

## Фактические новые проверки

Это запуски **28.09.2026**, не повторение прежних отчётов.

1. Полный pytest: **111 PASS**, 2 предупреждения существующих Starlette/httpx и anyio. Включает 7 новых случаев условных документов, прежние проверки PASS/FAIL/UNKNOWN, Decimal requested_grant, другого региона, специальной категории, точной временной границы, устаревших/будущих подтверждений приёма, редакций, запрета неполной публикации, авторизации, чужих планов, ревизий и повторного webhook.
2. `alembic upgrade head`, `alembic check`, `check_plan_migrations.py`: PASS на отдельной `navigator_test`. В тестах нет доступа к пользовательской БД.
3. Экспорт OpenAPI, проверка контрактного теста, `npm run generate:api`, `npm run build` (tsc/Vite): PASS. Новых npm/Python-зависимостей нет.
4. `docker build -t opora-apk-qa-rules:20260928 .`: PASS, 6.40 секунды с существующим кешем. Это не измерение чистой сборки без кеша.
5. **20 шагов DATA-API.yaml PASS** против нового работающего QA. Первый запуск через exec остановился на отсутствии `/app/DATA-API.yaml` в runtime-образе; корректный прогон выполнен отдельным контейнером с read-only mount сценария и network контейнера приложения. Не меняли Dockerfile ради тестового файла.
6. `check_rules_qa.py`: PASS; синтетическая мера штатно создана через draft → review → publish, динамические вопросы, Decimal, UNKNOWN/FAIL/PASS, manual UNKNOWN, второй отбор и маршрут, условный документ, новая анкета без перезаписи снимка, защита чужого плана. Затем перезапущены **только QA app и QA db**, `--verify` подтвердил полное равенство плана, профиля, отметок, версии, отбора, маршрута и снимка. Контрольный JSON: tmp/rules-20260928.json (синтетические данные).
7. IAB браузер: учебный вход, сохранение кооператива отдельно от is_kfh=false и ЕСХН, неизвестные ответы, подбор со всеми тремя статусами, карточка с ручной проверкой UNKNOWN, создание плана первого отбора, отметка документа, reload с сохранением отметки, открытие второго отбора из прежнего плана и правильный href `https://promote.budget.gov.ru/`. Реальная заявка не отправлялась. Снимок: docs/qa/rules-plan-20260928.png. На 390 и 1440 px scrollWidth не больше innerWidth. Клики IAB не давали эффекта; основной путь проверен доступными кнопками через Enter/Space и select/fill. Это не тест touch и не реальное мобильное MAX.
8. Перед сдачей прочитана актуальная официальная [валидация MAX](https://dev.max.ru/docs/webapps/validation): серверный HMAC WebAppData и запрет повторяющихся параметров соответствуют описанному алгоритму. MAX-код не менялся, токены не читались, новые реальные входы MAX не выполнялись.

## Воспроизводимые команды

Из `C:\EffectiveBusiness`. В этом compose явно новые имя проекта, сеть, том и порт **8003**. Никогда не направлять тесты с TRUNCATE или check_plan_migrations на рабочую БД.

```powershell
docker compose -f compose.qa-rules-20260928.yaml up -d --wait db testdb
docker run --rm --network opora-rules-20260928_default --mount type=bind,source=C:\EffectiveBusiness\backend,target=/app/backend,readonly --mount type=bind,source=C:\EffectiveBusiness\data,target=/app/data,readonly --mount type=bind,source=C:\EffectiveBusiness\docs,target=/app/docs -e APP_ENV=test -e SEED_DEMO=false -e DATABASE_URL=postgresql+psycopg://navigator:synthetic-test-only@testdb:5432/navigator_test -e TEST_DATABASE_URL=postgresql+psycopg://navigator:synthetic-test-only@testdb:5432/navigator_test opora-apk-qa-rules:20260927 sh -c 'python backend/export_openapi.py && alembic -c backend/alembic.ini upgrade head && pytest backend/tests -q -p no:cacheprovider && alembic -c backend/alembic.ini check && python backend/check_plan_migrations.py'
docker run --rm --mount type=bind,source=C:\EffectiveBusiness\frontend,target=/work/frontend --mount type=bind,source=C:\EffectiveBusiness\docs,target=/work/docs,readonly --mount type=volume,target=/work/frontend/node_modules --workdir /work/frontend node:24.14.1-alpine sh -c 'npm ci --no-fund --no-audit && npm run generate:api && npm run build'
docker build -t opora-apk-qa-rules:20260928 .
docker compose -f compose.qa-rules-20260928.yaml up -d --wait app
docker run --rm --network container:opora-rules-20260928-app-1 --mount type=bind,source=C:\EffectiveBusiness\DATA-API.yaml,target=/app/DATA-API.yaml,readonly opora-apk-qa-rules:20260928 python backend/check_data_api.py --base-url http://localhost:8000
docker compose -f compose.qa-rules-20260928.yaml exec -T app python backend/check_rules_qa.py --base-url http://localhost:8000 --snapshot /tmp/rules-20260928.json
docker cp opora-rules-20260928-app-1:/tmp/rules-20260928.json tmp/rules-20260928.json
docker compose -f compose.qa-rules-20260928.yaml restart db app
docker compose -f compose.qa-rules-20260928.yaml up -d --wait app
docker compose -f compose.qa-rules-20260928.yaml exec -T app python backend/check_rules_qa.py --base-url http://localhost:8000 --snapshot /tmp/rules-20260928.json --verify
```

Первый запуск check_rules_qa требует свежий синтетический том: повторное создание fixture намеренно отклоняется. После интерактивной проверки анкета менялась, поэтому первоначальный snapshot уже не должен совпадать с текущей анкетой. Для повторного QA используйте новый явно изолированный проект/том или проверку нового снимка; не удаляйте существующие пользовательские данные. DATA-API тоже изменяет учебный профиль.

## Оставшиеся ограничения и передача на размещение

1. Сначала завершить адресные блокеры HANDOFF-CATALOG по основным мерам. Реальные условия документов пока остаются текстом в черновиках: не переводить их массово в condition без проверенной ветви, определений и пункта первоисточника. Наличие manual UNKNOWN не разрешает публикацию неполного источника.
2. Сохранить резервную копию рабочей БД и проверить восстановление отдельно; на копии прогнать ранее созданные миграции. Сверить фактическую голову рабочей схемы — в этом чате VPS не читался и не обновлялся.
3. Зафиксировать исходники/образ и контрольные суммы, выполнить deployment только в отдельно разрешённом этапе. Из QA не переносить БД, пользователей, синтетические меры, demo-настройки и секреты. Проверить APP_ENV=production, SEED_DEMO=false.
4. Реальные меры публиковать исключительно через draft → review → publish после закрытия пробелов; связывать новый отбор с применимой редакцией. Подтверждение приёма получать отдельно; будущий страховой 0153 не становится open от календаря. Кооперативный грант 0140 не подменяет возмещение 0141.
5. После размещения выполнить новый smoke, проверку двух реальных владельцев, сценарий в web-MAX и Android/iOS, повторный вход и сохранность данных после restart. Старое подтверждение пользователя по web/Android не считать проверкой этой сборки. Условные документы, расчёты страхования/зерна и полнота реального каталога остаются зависимыми от исследования.

Начальная резервная копия 325 изменённых/новых файлов: `tmp/rules-start-20260928/manifest.json`. Исторические правки не откатывались. Полезный результат этого этапа — проверяемая локальная реализация и контракт условных документов, а не завершённая публикация реального каталога или обновлённый VPS.


## Окончательный образ и повторная проверка

После удаления лишнего пустого разделителя в schemas.py и добавления QA-compose
в hash_sources образ собран повторно. Image ID:
`sha256:3ecd303a5b24bf473b9f279c31e389871d3e5dc0dee4c502a013269a1b9dffdb` (docker image inspect; config digest: 0c94c506030d95c78e726e7a0b99e0d4336d99a0aec84491b0d9babbbaef387b).
Повторный тест непосредственно кода окончательного образа: **111 PASS**, Alembic
check PASS. Это повторный прогон тех же 111 случаев, не ещё 111 разных тестов.
Сначала тестовый каталог отсутствовал (0 запущено), затем без архива источников
было 110 PASS/1 FAIL (FileNotFoundError retrieval.jsonl); с обоими read-only mounts
весь прогон успешен. Runtime и архивы не изменялись ради устранения этих ошибок.

```powershell
docker run --rm --network opora-rules-20260928_default --mount type=bind,source=C:\EffectiveBusiness\backend\tests,target=/app/backend/tests,readonly --mount type=bind,source=C:\EffectiveBusiness\data\official\sources,target=/app/data/official/sources,readonly --mount type=bind,source=C:\EffectiveBusiness\docs,target=/app/docs,readonly -e APP_ENV=test -e SEED_DEMO=false -e DATABASE_URL=postgresql+psycopg://navigator:synthetic-test-only@testdb:5432/navigator_test -e TEST_DATABASE_URL=postgresql+psycopg://navigator:synthetic-test-only@testdb:5432/navigator_test opora-apk-qa-rules:20260928 sh -c 'pytest backend/tests -q -p no:cacheprovider && alembic -c backend/alembic.ini check'
docker compose -f compose.qa-rules-20260928.yaml exec -T app python backend/check_restart.py before --base-url http://localhost:8000 --snapshot /tmp/rules-all-plans.json
docker cp opora-rules-20260928-app-1:/tmp/rules-all-plans.json tmp/rules-all-plans.json
docker compose -f compose.qa-rules-20260928.yaml up -d --wait --force-recreate app
docker cp tmp/rules-all-plans.json opora-rules-20260928-app-1:/tmp/rules-all-plans.json
docker compose -f compose.qa-rules-20260928.yaml exec -T app python backend/check_restart.py after --base-url http://localhost:8000 --snapshot /tmp/rules-all-plans.json
```

Проверка before/after PASS: совпала контрольная сумма **всех трёх** планов,
полных assessment/items/отборов/версий/маршрутов и профиля после замены контейнера.
before изменяет только синтетическую анкету фермера, поэтому не запускать на рабочей БД.
QA app/db оставлены доступными на localhost:8003, тестовый testdb остановлен.
Первоначально запущенных Docker-контейнеров не было; прежние окружения не поднимались.

Финальный аудит: из 325 исходных файлов отсутствующих и неожиданно изменённых — 0; изменены только 12 перечисленных существующих файлов. Результат tmp/rules-final-audit-20260928.json. Git diff --check с настройками репозитория PASS; экспериментальный запуск с принудительным core.autocrlf=false ошибочно трактовал существующие CRLF как whitespace, файлы ради него не нормализовались.
