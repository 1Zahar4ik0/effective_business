# Полное развёртывание «Опора АПК»

Инструкция для текущих исходников. Локальный Docker-запуск проверен. Внешнее размещение, публичный сертификат и настоящий MAX пока не настроены: соответствующие шаги ниже являются инструкцией, а не отчётом об успешном запуске.

**Текущее ограничение владельца:** токен MAX хранится только на этом компьютере и передаётся только официальному API MAX. Не переносите `.env` или токен на сервер по инструкции ниже без отдельного изменения этого решения. Что заполнить для текущего запуска — [docs/USER-ACTIONS.md](docs/USER-ACTIONS.md).

## 1. Выберите окружение

| Окружение | Конфигурация | Адрес и вход |
|---|---|---|
| Локальная проверка на Windows | `compose.yaml` | `http://localhost:8000`, учебные кнопки входа |
| Сервер с HTTPS и MAX | `compose.production.yaml` | Ваш HTTPS-домен, только настоящий вход MAX |

Рабочее окружение использует отдельную PostgreSQL и том. Не объединяйте эти два Compose-файла и не переносите демонстрационную БД в production.

FastAPI отдаёт API и собранный React, PostgreSQL хранит анкеты и планы, worker обрабатывает события бота. Python и Node.js на хосте для Docker-запуска не нужны: образ устанавливает зависимости из `backend/requirements.txt` и `frontend/package-lock.json`.

## 2. Локальный запуск на Windows

Установите и запустите [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) в режиме Linux-контейнеров. В PowerShell:

```powershell
Set-Location C:\EffectiveBusiness
docker version
docker compose version
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
docker compose up -d --build --wait
docker compose ps
```

Существующий `.env` не перезаписывается. Локальные параметры: `APP_ENV=demo`, `SEED_DEMO=true`, `PUBLIC_ORIGIN=http://localhost:8000`. Пароль уже созданной БД нельзя сменить только редактированием `.env`: требуется согласованная смена пароля в PostgreSQL.

- Приложение: http://localhost:8000
- Состояние: http://localhost:8000/health
- API: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json

Порты компьютера: `8000` — приложение, `55432` — PostgreSQL; оба привязаны к `127.0.0.1`. Если порт занят, остановите конфликтующий процесс. Не открывайте демонстрационные порты в интернет.

Миграции выполняются автоматически. В пустой каталог добавляются шесть синтетических мер. Вход фермером/редактором без пароля доступен только в демо; аккаунты общие для локальных браузеров, используйте неперсональные ответы.

Проверка: «Войти как фермер» → «Моё хозяйство» → «Заполнить учебный пример» → третий шаг → «Сохранить и подобрать» → карточка → сохранить план → отметить документ → перезагрузить → «Мои планы». Отметка должна сохраниться. Учебные сроки не обновляются при перезапуске и со временем требуют проверки.

Добавить реальные черновики:

```powershell
docker compose exec -T app python backend/import_official.py --apply
```

Импорт сохраняет существующие редакторские изменения и ничего не публикует. Черновики видны после входа редактором в разделе «Редактор».

Остановка и повторный запуск:

```powershell
docker compose stop
docker compose up -d --wait
```

`docker compose down` сохраняет именованный том. Не используйте `down -v` и очистку Docker volumes, если данные нужны.

## 3. Подготовьте сервер, домен и бота

Для внешнего размещения нужны:

1. Отдельный VPS: ориентир для проверки — 2 vCPU, 4 ГБ RAM, 40 ГБ SSD, Ubuntu 24.04 LTS amd64, публичный IPv4 и SSH с ключом. Время сборки измеряется отдельно на выбранном сервере.
2. Домен/поддомен с A-записью на этот IPv4. Подойдёт свободное имя DuckDNS. Неверную AAAA-запись исправьте или удалите, если сервер не обслуживает IPv6.
3. Открытые TCP 80/443. SSH разрешите с адресов администраторов. PostgreSQL и порт приложения 8000 наружу не публикуются.
4. Созданный бот MAX, токен и доступ к настройке мини-приложения. Регистрация и модерация выполняются в кабинете платформы: [инструкция MAX](https://dev.max.ru/docs/chatbots/bots-create/create).

Для предварительной диагностики токен можно сохранить в `C:\EffectiveBusiness\.env`, строка `MAX_BOT_TOKEN=`. Не вставляйте его в `.env.example`, React, README или чат. На сервере используется отдельный `.env.production`.

## 4. Установите Docker на сервере

Подключитесь по SSH. Серверные команды ниже предназначены для Bash на выделенном Ubuntu-сервере. Перейдите в административную оболочку: `sudo -i`.

Если Docker и Compose уже установлены, проверьте `docker version` и `docker compose version`. Для чистого Ubuntu:

```bash
apt-get update
apt-get install -y ca-certificates curl unzip python3 certbot nano
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
printf 'Types: deb\nURIs: https://download.docker.com/linux/ubuntu\nSuites: %s\nComponents: stable\nArchitectures: %s\nSigned-By: /etc/apt/keyrings/docker.asc\n' \
  "$VERSION_CODENAME" "$(dpkg --print-architecture)" > /etc/apt/sources.list.d/docker.sources
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
docker version
docker compose version
```

При конфликтующих пакетах сначала следуйте [официальной инструкции Docker](https://docs.docker.com/engine/install/ubuntu/). Не удаляйте пакеты чужого работающего сервера вслепую. Если Docker был предустановлен, отдельно установите `certbot`, `python3`, `curl` и `nano`. Учитывайте опубликованные Docker-порты в firewall провайдера: одних правил UFW недостаточно.

## 5. Перенесите текущие исходники

Размещайте проект в `/opt/opora-apk`. Комплект `output/submission` зафиксирован 18.09.2026 и не обновляется автоматически при изменениях проекта. Для текущей версии создайте архив на Windows без `.env`, локальной БД, зависимостей и временных файлов:

```powershell
Set-Location C:\EffectiveBusiness
tar.exe -czf "$env:TEMP\opora-apk-deploy.tar.gz" --exclude=__pycache__ --exclude=.pytest_cache --exclude=node_modules --exclude=dist --exclude=*.tsbuildinfo --exclude=data/official/sources backend frontend data deploy docs Dockerfile .dockerignore compose.production.yaml compose.max-ca.yaml DATA-API.yaml README.md AGENTS.md ARCHITECTURE.md
Get-FileHash "$env:TEMP\opora-apk-deploy.tar.gz" -Algorithm SHA256
scp "$env:TEMP\opora-apk-deploy.tar.gz" LOGIN@SERVER_IP:/tmp/opora-apk-deploy.tar.gz
```

Замените `LOGIN` и `SERVER_IP` данными сервера. На сервере сравните SHA-256, осмотрите список файлов и распакуйте в новый каталог:

```bash
sha256sum /tmp/opora-apk-deploy.tar.gz
install -d -m 0755 /opt/opora-apk
tar -tzf /tmp/opora-apk-deploy.tar.gz
tar -xzf /tmp/opora-apk-deploy.tar.gz -C /opt/opora-apk
cd /opt/opora-apk
```

Если проект уже установлен, сначала сделайте резервную копию по разделу 12 и сохраните старую версию исходников. Секреты настраиваются отдельно через защищённый SSH-сеанс.

## 6. Настройте переменные окружения

```bash
cd /opt/opora-apk
umask 077
test -f .env.production || cp deploy/production.env.example .env.production
chmod 600 .env.production
nano .env.production
```

| Переменная | Значение |
|---|---|
| `DOMAIN` | Имя домена без `https://` и пути, например `opora-apk-test.duckdns.org` |
| `POSTGRES_PASSWORD` | Новый случайный URL-safe пароль рабочей БД, например 64 шестнадцатеричных знака |
| `TLS_DIR` | `/etc/opora-apk/tls` |
| `MAX_BOT_TOKEN` | Токен бота без префикса `Bearer` |
| `MAX_WEBHOOK_SECRET` | Отдельная случайная строка, например 64 шестнадцатеричных знака; не токен бота |
| `MAX_APP_URL` | Диплинк `https://max.ru/ИМЯ_БОТА?startapp` |
| `MAX_ADMIN_IDS` | Подтверждённые числовые ID редакторов через запятую; пока неизвестны — оставить пустым |

Создавайте секреты менеджером паролей или локальным генератором и сохраняйте в закрытом файле. Не отправляйте файл в журналы/чат. `APP_ENV=production`, `SEED_DEMO=false`, внутренний `DATABASE_URL` и `PUBLIC_ORIGIN=https://DOMAIN` задаёт Compose.

В текущей Bash-сессии определите функцию:

```bash
cd /opt/opora-apk
dc() { docker compose --env-file .env.production -f compose.production.yaml "$@"; }
dc config --quiet
```

При новом SSH-входе повторите `cd` и определение функции. Не вызывайте `config` без `--quiet`: полный вывод раскрывает окружение.

Если TLS официального API MAX требует дополнительной цепочки доверия, получите проверенный полный CA bundle по [документации MAX](https://dev.max.ru/docs-api/changelog-api), сохраните его на сервере и добавьте `MAX_CA_BUNDLE_HOST=/абсолютный/путь/ca-bundle.pem` в `.env.production`. Замените функцию:

```bash
dc() { docker compose --env-file .env.production -f compose.production.yaml -f compose.max-ca.yaml "$@"; }
```

Не отключайте проверку TLS. Этот дополнительный Compose-файл также включите в обе команды hooks из раздела 7.

## 7. Получите HTTPS-сертификат и настройте продление

Убедитесь, что DNS указывает на VPS, TCP 80 доступен извне и свободен на сервере. Введите имя, совпадающее с `DOMAIN`:

```bash
read -r -p 'Имя домена без https://: ' APP_DOMAIN
getent ahostsv4 "$APP_DOMAIN"
certbot certonly --standalone --cert-name "$APP_DOMAIN" -d "$APP_DOMAIN"
install -d -m 0700 /etc/opora-apk/tls
install -m 0644 "/etc/letsencrypt/live/$APP_DOMAIN/fullchain.pem" /etc/opora-apk/tls/fullchain.pem
install -m 0600 "/etc/letsencrypt/live/$APP_DOMAIN/privkey.pem" /etc/opora-apk/tls/privkey.pem
```

Certbot запросит почту и согласие с условиями центра сертификации. Контейнер получает копии файлов, а не символьные ссылки на недоступные пути. Самоподписанный сертификат для MAX не подходит.

Следующие hooks рассчитаны на **выделенный сервер с единственным сертификатом проекта**. При продлении proxy ненадолго останавливается для standalone-проверки на порту 80. Для сервера с несколькими сайтами сначала адаптируйте hooks к конкретному сертификату. [Документация Certbot](https://eff-certbot.readthedocs.io/en/stable/using.html#renewing-certificates).

```bash
install -d /etc/letsencrypt/renewal-hooks/pre /etc/letsencrypt/renewal-hooks/deploy /etc/letsencrypt/renewal-hooks/post
cat > /etc/letsencrypt/renewal-hooks/pre/opora-apk.sh <<'SH'
#!/bin/sh
set -eu
cd /opt/opora-apk
docker compose --env-file .env.production -f compose.production.yaml stop proxy
SH
cat > /etc/letsencrypt/renewal-hooks/deploy/opora-apk.sh <<'SH'
#!/bin/sh
set -eu
install -m 0644 "$RENEWED_LINEAGE/fullchain.pem" /etc/opora-apk/tls/fullchain.pem
install -m 0600 "$RENEWED_LINEAGE/privkey.pem" /etc/opora-apk/tls/privkey.pem
SH
cat > /etc/letsencrypt/renewal-hooks/post/opora-apk.sh <<'SH'
#!/bin/sh
set -eu
cd /opt/opora-apk
docker compose --env-file .env.production -f compose.production.yaml up -d proxy
SH
chmod 0700 /etc/letsencrypt/renewal-hooks/pre/opora-apk.sh /etc/letsencrypt/renewal-hooks/deploy/opora-apk.sh /etc/letsencrypt/renewal-hooks/post/opora-apk.sh
systemctl enable --now certbot.timer
```

При использовании CA bundle добавьте `-f compose.max-ca.yaml` в обе Compose-команды hooks. При новом SSH-входе снова задайте `APP_DOMAIN`, прежде чем выполнять команды с этой переменной.

## 8. Запустите рабочее окружение

```bash
cd /opt/opora-apk
dc config --quiet
dc up -d --build --wait
dc ps
dc exec -T proxy nginx -t
dc exec -T app alembic -c backend/alembic.ini current
dc exec -T app alembic -c backend/alembic.ini check
curl --fail --show-error "https://$APP_DOMAIN/health"
curl --fail --show-error "https://$APP_DOMAIN/api/config"
```

Ожидаются healthy у приложения/БД, работающий proxy, успешный HTTPS и `demo: false`. Миграции применяются автоматически до запуска API. Откройте адрес с телефона через мобильный интернет и проверьте доверие к сертификату. PostgreSQL не должен иметь опубликованного внешнего порта.

В период допустимой краткой недоступности проверьте продление:

```bash
certbot renew --cert-name "$APP_DOMAIN" --dry-run
dc ps
curl --fail --show-error "https://$APP_DOMAIN/health"
systemctl list-timers certbot.timer
```

Dry-run проверяет получение сертификата и pre/post hooks, но по умолчанию не запускает deploy hook. Контролируйте успешность будущих продлений и срок сертификата: наличие таймера не доказывает успешное обновление.

## 9. Подключите настоящий MAX

В кабинете MAX: «Чат-боты» → нужный бот → настройки мини-приложения. В поле URL укажите **`https://ВАШ_ДОМЕН/`**. В переменной `MAX_APP_URL` должна остаться **ссылка `https://max.ru/ИМЯ_БОТА?startapp`**. [Инструкция MAX](https://dev.max.ru/docs/webapps/introduction).

Примените окружение и запустите обработчик бота:

```bash
dc --profile max up -d --wait
dc exec -T app python backend/max_preflight.py
```

Диагностика выполняет GET /me и GET /subscriptions, выводит только статусы и ничего не регистрирует. До настройки webhook ненулевой код возможен даже при правильном токене. При `network_tls_or_invalid_response` проверьте сеть и CA bundle, не отключайте TLS.

Следующая команда **регистрирует внешний webhook**. Запускайте только для своего бота после проверки адреса и секрета. Метод: [POST /subscriptions](https://dev.max.ru/docs-api/methods/POST/subscriptions); нужен публичный HTTPS на 443.

```bash
dc exec -T app python - <<'PY'
import ssl
import httpx
from app.config import settings
c = settings()
if (c.app_env != 'production' or not c.max_bot_token or not c.max_webhook_secret
        or not c.public_origin.startswith('https://')
        or c.max_api_base.rstrip('/') != 'https://platform-api2.max.ru'):
    raise SystemExit('Проверьте production, origin и настройки MAX')
try:
    with httpx.Client(base_url=c.max_api_base,
                      headers={'Authorization': c.max_bot_token},
                      verify=ssl.create_default_context(cafile=c.max_ca_bundle or None),
                      timeout=30, follow_redirects=False) as client:
        response = client.post('/subscriptions', json={
            'url': c.public_origin.rstrip('/') + '/api/max/webhook',
            'update_types': ['bot_started', 'message_created'],
            'secret': c.max_webhook_secret,
        })
        if response.status_code != 200 or response.json().get('success') is not True:
            raise SystemExit(f'Webhook не подтверждён: HTTP {response.status_code}')
        print('Webhook зарегистрирован')
except (httpx.HTTPError, ValueError, OSError):
    raise SystemExit('Ошибка сети, TLS или ответа MAX; секреты не выведены')
PY
dc exec -T app python backend/max_preflight.py
```

Ожидаются `bot_api: authenticated`, `webhook_registered: true`. Напишите `/start` боту и откройте приложение через MAX. Прямой переход на сайт не содержит подписанных данных запуска.

Если ID редактора неизвестен, сначала войдите через MAX. В ответе `/api/auth/me` своего сеанса найдите `user.id` вида `max:123456789`. Запишите числовую часть в `MAX_ADMIN_IDS` на сервере, выполните `dc --profile max up -d` и заново откройте приложение. Не копируйте cookie/initData в чат или отчёт. Роль назначайте только подтверждённому аккаунту.

## 10. Подготовьте каталог

```bash
dc exec -T app python backend/import_official.py
dc exec -T app python backend/import_official.py --apply
```

Первый вызов проверяет набор без записи, второй добавляет отсутствующие черновики. В текущих данных 10 реальных черновиков, ни один не подтверждён полностью. Пустой публичный каталог после импорта ожидаем.

Войдите редактором через MAX. Проверьте источники, применимую редакцию, правила, документы, даты/часовой пояс и маршрут подачи. Заполните пробелы, выполните проверку и публикацию версии. Не обходите блокировки и не включайте `SEED_DEMO` на сервере. До появления проверенной опубликованной меры путь «подбор → план» в production полностью проверить нельзя; синтетический сценарий проверяется локально.

## 11. Проверьте установленный проект

На сервере:

```bash
dc ps
dc exec -T app alembic -c backend/alembic.ini check
dc exec -T app python backend/max_preflight.py
```

В веб-MAX и отдельно на настоящем телефоне:

1. Войти через бота; учебных кнопок входа быть не должно.
2. Сохранить неперсональную анкету, закрыть и заново открыть приложение: ответы должны сохраниться.
3. Проверить PASS/FAIL/UNKNOWN и отдельный статус приёма заявок.
4. У опубликованной проверенной меры сохранить план и отметить документ; повторно открыть и проверить сохранение отметки.
5. Открыть официальный маршрут без отправки/подписи заявки.
6. Вторым тестовым аккаунтом проверить отсутствие доступа к чужим планам и редактору.

Запишите устройство, ОС, версию MAX, дату и результаты в `docs/MAX-DEVICE-REPORT.md`. Браузер шириной 390 px не заменяет мобильный MAX.

Автотесты запускайте **локально** на отдельной БД:

```powershell
Set-Location C:\EffectiveBusiness
docker compose up -d --build --wait
docker compose exec -T db createdb -U navigator navigator_test
docker compose -f compose.yaml -f compose.test.yaml run --rm tests
```

Если `navigator_test` уже существует, пропустите `createdb`. Тесты очищают только эту тестовую БД. TypeScript и Vite проверяются при сборке Docker.

Для 14 сценариев `DATA-API.yaml` восстановите локальную Python-среду при необходимости (нужен установленный Python 3.12):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/check_data_api.py
```

Проверка обращается к localhost и изменяет общие учебные анкеты/планы; для production она не предназначена.

## 12. Резервное копирование и восстановление

На сервере перед обновлениями и регулярно:

```bash
cd /opt/opora-apk
umask 077
install -d -m 0700 backups
BACKUP_FILE="backups/navigator-$(date +%F-%H%M%S).dump"
dc exec -T db pg_dump -U navigator -d navigator -Fc > "$BACKUP_FILE"
test -s "$BACKUP_FILE"
dc exec -T db pg_restore --list < "$BACKUP_FILE" > /dev/null
```

Копируйте дамп в защищённое хранилище вне VPS. Отдельно сохраняйте `.env.production` и исходники. Настройте ежедневный запуск, контроль ошибок и срок хранения после выбора хранилища: проект не включает эти внешние настройки автоматически. Дампы и секреты не включайте в публичный комплект.

Проверьте восстановление в **новую отдельную БД**:

```bash
RESTORE_DB="navigator_restore_$(date +%Y%m%d%H%M%S)"
dc exec -T db createdb -U navigator "$RESTORE_DB"
dc exec -T db pg_restore -U navigator -d "$RESTORE_DB" --no-owner --exit-on-error < "$BACKUP_FILE"
dc exec -T db psql -U navigator -d "$RESTORE_DB" -c 'SELECT version_num FROM alembic_version;'
```

Сравните нужные записи с исходной БД в закрытом административном сеансе. Список содержимого дампа сам по себе не подтверждает восстановление. Переключение на восстановленную БД выполняется отдельно в согласованное окно обслуживания.

## 13. Остановка, обновление и диагностика

Остановка с сохранением данных и повторный запуск:

```bash
dc --profile max stop
dc --profile max up -d --wait
```

Для обновления сделайте резервную копию, перенесите новые исходники с сохранением `.env.production`, затем:

```bash
dc --profile max up -d --build --wait
dc ps
dc exec -T app alembic -c backend/alembic.ini current
curl --fail --show-error "https://$APP_DOMAIN/health"
```

Изменение переменных требует `up -d`, пересоздающего изменённые контейнеры. Простой `restart` не обновляет окружение. После новых миграций не выполняйте слепой откат схемы без проверки совместимости и данных.

| Симптом | Действие |
|---|---|
| Docker недоступен на Windows | Запустить Docker Desktop, проверить Linux-контейнеры |
| Сертификат не выдаётся | Проверить A/AAAA, TCP 80 и занятость порта |
| HTTPS 502 | Проверить `dc ps`, локально прочитать `dc logs --tail=80 app`; не публиковать необработанные журналы |
| MAX 401 | Проверить токен, время сервера и повторно открыть приложение через бота |
| TLS-ошибка MAX | Подключить проверенный CA bundle без отключения проверки сертификата |
| Редактор отсутствует | Проверить подписанный MAX ID, `MAX_ADMIN_IDS` и пересоздание app |
| Каталог пуст | Требуется содержательная проверка и публикация импортированных черновиков |
| Production не стартует со старой БД | Использовать отдельный рабочий том без демопользователей/мер |

Развёртывание завершено после успешных проверок HTTPS, webhook, настоящего входа и сохранения данных в веб- и мобильном MAX. Наличие конфигурации не заменяет эти проверки.


## Реальные объявления и локальное доверие MAX

После пересборки обновите страницу браузера. В каталоге по умолчанию открываются 10 реальных объявлений из `data/official/notices.json`; API — `/api/official-announcements`. Снимок поставляется с приложением и не требует очистки или перезаписи PostgreSQL. Это проверенные финансовые факты и сроки, а не полностью опубликованные правила подбора. Учебные меры находятся на отдельной вкладке. Для изменения данных сначала сверяйте официальный источник и новую редакцию, затем пересобирайте образ; автоматического обновления нет.

Для MAX нужен проверенный PEM bundle: укажите его абсолютный путь в локальном `MAX_CA_BUNDLE_HOST` и добавьте `-f compose.local-max-ca.yaml` к локальной конфигурации Compose. Подробные шаги приведены в [docs/USER-ACTIONS.md](docs/USER-ACTIONS.md). Без этого текущий контейнер не проверяет TLS-цепочку MAX. Токен повторно передавать или копировать на хостинг не нужно.
