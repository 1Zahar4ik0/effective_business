# Опора АПК

Мини-приложение MAX для КФХ и сельскохозяйственных ИП Саратовской области. Фермер заполняет анкету, получает предварительный подбор мер господдержки с объяснением по каждому условию, открывает карточку отбора и сохраняет план подготовки документов со ссылкой на официальный маршрут подачи.

Стек: FastAPI, React + TypeScript, PostgreSQL, всё запускается через Docker Compose.

Текущая версия: `opora-apk-20260929-rc2`, подробности и ограничения в [docs/RELEASE-20260929-RC2.md](docs/RELEASE-20260929-RC2.md).

- Стенд: https://opora-apk.159-194-249-97.sslip.io/
- Бот: https://max.ru/t761_hakaton_max_bot
- Доступ владельца к серверу: `ssh effectivebusiness`

На стенде опубликованы 10 реальных справочных карточек, по ним можно сохранять планы. Полной проверки права на поддержку пока нет ни у одной меры (об этом ниже). Локальная демонстрация работает на синтетических данных, и интерфейс это явно показывает.

## Как устроено

FastAPI отдаёт API и собранный React. В PostgreSQL лежат анкеты, версии мер и планы. Отдельный worker отправляет ответы бота. Архитектура описана в [ARCHITECTURE.md](ARCHITECTURE.md), сценарии API в [DATA-API.yaml](DATA-API.yaml), схема в [docs/openapi.json](docs/openapi.json).

```
backend/        FastAPI, миграции Alembic, служебные скрипты, тесты
frontend/       React + Vite
data/demo/      синтетические меры для локального запуска
data/official/  реальные черновики, объявления и снимки официальных источников
deploy/         nginx, продление сертификата, обёртка opora-compose, скрипты релизов
docs/           документация, отчёты о выпусках, контрольные суммы
```

Есть два окружения, и их нельзя смешивать:

| Окружение | Файл | Адрес и вход |
|---|---|---|
| Локальная проверка | `compose.yaml` | `http://localhost:8000`, учебные кнопки входа |
| Сервер с HTTPS и MAX | `compose.production.yaml` | ваш домен, вход только через MAX |

У production своя база и свой том. Демонстрационную БД туда не переносите: приложение откажется стартовать, если найдёт в базе синтетические меры или демо-пользователей.

## Локальный запуск (Windows)

Нужен [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) в режиме Linux-контейнеров. Для запуска Python и Node.js на компьютере не нужны, всё ставится внутри образа. Python 3.12 понадобится только для проверки сценариев `DATA-API.yaml` (раздел «Тесты»). В примерах ниже проект лежит в `C:\EffectiveBusiness`, подставьте свою папку.

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

Существующий `.env` команда не трогает. По умолчанию там `APP_ENV=demo`, `SEED_DEMO=true`, `PUBLIC_ORIGIN=http://localhost:8000`. Пароль уже созданной БД правкой `.env` не меняется, его нужно менять в самом PostgreSQL.

После запуска:

- приложение: http://localhost:8000
- состояние: http://localhost:8000/health
- Swagger: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json

Порты 8000 (приложение) и 55432 (PostgreSQL) слушают только `127.0.0.1`. Наружу их не открывайте.

Миграции применяются сами, в пустой каталог добавляются шесть синтетических мер. Вход фермером или редактором без пароля есть только в демо, и аккаунты общие для всех браузеров на компьютере, так что вводите неперсональные данные.

Быстрая проверка: «Войти как фермер» → «Моё хозяйство» → «Заполнить учебный пример» → третий шаг → «Сохранить и подобрать» → карточка → сохранить план → отметить документ → перезагрузить страницу → «Мои планы». Отметка должна остаться на месте. Сроки учебных отборов при перезапуске не обновляются, со временем они устареют.

Остановка и повторный запуск:

```powershell
docker compose stop
docker compose up -d --wait
```

`docker compose down` оставляет именованный том с данными. `down -v` и очистка томов Docker удалят базу.

### Учебный пример без MAX

Отдельный стенд со своей базой, чтобы посмотреть подбор, не трогая основную локальную БД:

```powershell
docker compose --env-file .env.example -f compose.demo-evaluation.yaml up -d --build --wait
```

Откройте http://localhost:8000, нажмите «Заполнить учебный пример КФХ», затем «3 Ваш проект» → «Сохранить и подобрать» → «Соответствует ответам анкеты». Учебный грант «Развитие фермерского хозяйства» подходит при регионе регистрации 64, статусе КФХ, цели equipment и собственных средствах от 300 000 ₽, а в примере указано 450 000 ₽. Условия вымышленные.

Стенд называется `opora-evaluation`, использует том `evaluation_data` и тот же порт 8000, поэтому основной локальный запуск перед ним нужно остановить. Остановка с сохранением ответов:

```powershell
docker compose --env-file .env.example -f compose.demo-evaluation.yaml stop
```

### Реальные черновики локально

```powershell
docker compose exec -T app python backend/import_official.py --apply
```

Импорт ничего не публикует и не затирает правки редактора. Черновики появятся в разделе «Редактор» после входа редактором.

### MAX на локальной машине

Для проверки токена его можно положить в `.env` строкой `MAX_BOT_TOKEN=`. В `.env.example`, фронтенд, README и чаты токен не попадает. Если цепочка сертификатов MAX не покрыта системными корневыми сертификатами контейнера, запросы к MAX упадут с ошибкой TLS. Проверку при этом никто не отключает, просто нужен CA bundle: укажите абсолютный путь к нему в `MAX_CA_BUNDLE_HOST` и добавьте к команде `-f compose.local-max-ca.yaml`. Подробно в [docs/USER-ACTIONS.md](docs/USER-ACTIONS.md).

## Тесты

Автотесты гоняем локально на отдельной базе `navigator_test`:

```powershell
Set-Location C:\EffectiveBusiness
docker compose up -d --build --wait
docker compose exec -T db createdb -U navigator navigator_test
docker compose -f compose.yaml -f compose.test.yaml run --rm tests
```

Если база уже есть, `createdb` пропустите. Тесты очищают только `navigator_test`. TypeScript и Vite проверяются при сборке образа.

Снимки официальных источников в образ не попадают (их исключает `.dockerignore`), а один тест сверяет по ним SHA-256. Поэтому `compose.test.yaml` подключает `data/official/sources/catalog-20260928` только на чтение. Запускайте тесты из полной копии проекта, где эта папка есть, иначе `test_evidence_hashes_and_retrievals_match_files` упадёт.

Для 20 шагов из `DATA-API.yaml` поднимите отдельный стенд на порту 8001 (образ `opora-apk-app` должен быть уже собран командой выше):

```powershell
docker compose -p opora-apk-qa-20260927 -f compose.release-check.yaml up -d --wait
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/check_data_api.py --base-url http://localhost:8001
```

Скрипт меняет только учебные анкеты этого стенда. На production его не запускайте.

## Развёртывание на сервере

### Что нужно заранее

1. VPS. Мы проверяли на 2 vCPU, 4 ГБ RAM, 40 ГБ SSD, Ubuntu 24.04 LTS amd64, публичный IPv4, SSH по ключу.
2. Домен или поддомен с A-записью на этот IP. Подойдёт бесплатный DuckDNS. Если сервер не обслуживает IPv6, лишнюю AAAA-запись уберите.
3. Открытые TCP 80 и 443. SSH лучше разрешить только с адресов администраторов. PostgreSQL и порт 8000 наружу не публикуются.
4. Бот MAX с токеном и доступ к настройке мини-приложения ([инструкция MAX](https://dev.max.ru/docs/chatbots/bots-create/create)).

Команды ниже выполняются в Bash на сервере от root (`sudo -i`).

### Docker

Если Docker уже стоит, проверьте `docker version` и `docker compose version`. Для чистой Ubuntu:

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

При конфликте пакетов смотрите [официальную инструкцию Docker](https://docs.docker.com/engine/install/ubuntu/) и не удаляйте пакеты на чужом рабочем сервере вслепую. Если Docker был предустановлен, отдельно поставьте `certbot`, `python3`, `curl` и `nano`. Опубликованные Docker порты обходят UFW, поэтому доступ ограничивайте ещё и в firewall провайдера.

### Перенос исходников

Проект живёт в `/opt/opora-apk`. Архив собираем на Windows без `.env`, локальной базы, зависимостей и снимков источников:

```powershell
Set-Location C:\EffectiveBusiness
tar.exe -czf "$env:TEMP\opora-apk-deploy.tar.gz" --exclude=__pycache__ --exclude=.pytest_cache --exclude=node_modules --exclude=dist --exclude=*.tsbuildinfo --exclude=data/official/sources backend frontend data deploy docs Dockerfile .dockerignore compose.production.yaml compose.max-ca.yaml DATA-API.yaml README.md ARCHITECTURE.md
Get-FileHash "$env:TEMP\opora-apk-deploy.tar.gz" -Algorithm SHA256
scp "$env:TEMP\opora-apk-deploy.tar.gz" LOGIN@SERVER_IP:/tmp/opora-apk-deploy.tar.gz
```

На сервере сравните SHA-256, посмотрите список файлов и распакуйте:

```bash
sha256sum /tmp/opora-apk-deploy.tar.gz
install -d -m 0755 /opt/opora-apk
tar -tzf /tmp/opora-apk-deploy.tar.gz
tar -xzf /tmp/opora-apk-deploy.tar.gz -C /opt/opora-apk
cd /opt/opora-apk
```

Если проект уже установлен, сначала сделайте резервную копию (раздел «Резервное копирование») и сохраните старую версию исходников.

### Переменные окружения

Секреты лежат вне исходников, в `/etc/opora-apk/production.env` (права 0600, каталог 0700). На текущем стенде так и сделано с разрешения владельца от 27.09.2026.

```bash
cd /opt/opora-apk
umask 077
install -d -m 0700 /etc/opora-apk
test -f /etc/opora-apk/production.env || cp deploy/production.env.example /etc/opora-apk/production.env
chmod 600 /etc/opora-apk/production.env
nano /etc/opora-apk/production.env
```

| Переменная | Что указать |
|---|---|
| `DOMAIN` | имя домена без `https://`, например `opora-apk-test.duckdns.org` |
| `POSTGRES_PASSWORD` | новый случайный URL-safe пароль, например 64 hex-символа |
| `TLS_DIR` | `/etc/opora-apk/tls` |
| `MAX_BOT_TOKEN` | токен бота без префикса `Bearer` |
| `MAX_WEBHOOK_SECRET` | отдельная случайная строка (не токен), например 64 hex-символа |
| `MAX_APP_URL` | диплинк `https://max.ru/ИМЯ_БОТА?startapp` |
| `MAX_ADMIN_IDS` | числовые ID редакторов через запятую; если пока неизвестны, оставьте пустым |

`APP_ENV=production`, `SEED_DEMO=false`, `DATABASE_URL` и `PUBLIC_ORIGIN=https://DOMAIN` задаёт сам Compose. Файл с секретами в логи и чаты не отправляйте.

Чтобы не писать длинную команду каждый раз, заведите функцию (после нового входа по SSH её нужно определить заново):

```bash
cd /opt/opora-apk
dc() { docker compose --env-file /etc/opora-apk/production.env -f compose.production.yaml "$@"; }
dc config --quiet
```

`dc config` без `--quiet` печатает всё окружение вместе с секретами.

Если TLS API MAX требует дополнительной цепочки доверия, возьмите проверенный CA bundle по [документации MAX](https://dev.max.ru/docs-api/changelog-api), положите его на сервер, пропишите `MAX_CA_BUNDLE_HOST=/абсолютный/путь/ca-bundle.pem` в `production.env` и подключите второй файл:

```bash
dc() { docker compose --env-file /etc/opora-apk/production.env -f compose.production.yaml -f compose.max-ca.yaml "$@"; }
```

На текущем стенде bundle взят с официального CDN Госуслуг и подключён только к клиентам MAX (см. [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)). Отключать проверку TLS не нужно ни в каком случае.

### HTTPS-сертификат

DNS должен уже указывать на сервер, а порт 80 должен быть свободен и доступен снаружи.

```bash
read -r -p 'Имя домена без https://: ' APP_DOMAIN
getent ahostsv4 "$APP_DOMAIN"
certbot certonly --standalone --cert-name "$APP_DOMAIN" -d "$APP_DOMAIN"
install -d -m 0700 /etc/opora-apk/tls
install -m 0644 "/etc/letsencrypt/live/$APP_DOMAIN/fullchain.pem" /etc/opora-apk/tls/fullchain.pem
install -m 0600 "/etc/letsencrypt/live/$APP_DOMAIN/privkey.pem" /etc/opora-apk/tls/privkey.pem
install -d -m 0755 /var/www/certbot
```

Certbot спросит почту и согласие с условиями. В контейнер попадают копии файлов, а не симлинки. Самоподписанный сертификат MAX не примет.

Для продления без остановки сайта пропишите в `production.env` строку `ACME_WEBROOT=/var/www/certbot`. Nginx отдаёт `/.well-known/acme-challenge/` из этого каталога, остальной HTTP перенаправляет на HTTPS.

### Запуск

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

Приложение и база должны быть healthy, proxy запущен, `/api/config` возвращает `demo: false`. Миграции применяются до старта API. Откройте сайт с телефона через мобильный интернет и убедитесь, что сертификат доверенный.

Теперь переключите продление на webroot и поставьте hook, который копирует новый сертификат и перезагружает nginx:

```bash
# opora-compose всегда подключает compose.max-ca.yaml, поэтому нужен MAX_CA_BUNDLE_HOST.
install -m 0755 deploy/opora-compose /usr/local/sbin/opora-compose
install -m 0755 deploy/renew-certificate.sh /etc/letsencrypt/renewal-hooks/deploy/opora-apk
certbot reconfigure --cert-name "$APP_DOMAIN" --webroot -w /var/www/certbot --non-interactive
systemctl enable --now certbot.timer
certbot renew --cert-name "$APP_DOMAIN" --dry-run
RENEWED_LINEAGE="/etc/letsencrypt/live/$APP_DOMAIN" /etc/letsencrypt/renewal-hooks/deploy/opora-apk
```

`reconfigure` проверяет webroot тестовым выпуском, последняя команда проверяет сам hook. Срок сертификата всё равно стоит иногда проверять.

### Подключение MAX

Для бота хакатона капитан отправляет HTTPS-адрес сайта через [форму организаторов](https://sbor-ssylok-dlya-mini-prilojeniy.testograf.ru/): ФИО капитана, email регистрации, название команды и URL. Токен там не нужен. Подробности в [docs/USER-ACTIONS.md](docs/USER-ACTIONS.md).

Если у вас есть доступ к бизнес-кабинету: «Чат-боты» → бот → настройки мини-приложения, в поле URL укажите `https://ВАШ_ДОМЕН/` ([инструкция MAX](https://dev.max.ru/docs/webapps/introduction)). В `MAX_APP_URL` при этом остаётся ссылка вида `https://max.ru/ИМЯ_БОТА?startapp`.

Запустите worker бота и диагностику:

```bash
dc --profile max up -d --wait
dc exec -T app python backend/max_preflight.py
```

Диагностика делает `GET /me` и `GET /subscriptions` и печатает статусы и публичную ссылку бота, ничего не регистрируя. `webhook_registered` смотрите в выводе, код завершения его не отражает. При `network_tls_or_invalid_response` проверьте сеть и CA bundle.

Следующий скрипт регистрирует webhook через [POST /subscriptions](https://dev.max.ru/docs-api/methods/POST/subscriptions). Запускайте его только для своего бота, когда адрес и секрет уже проверены. Нужен публичный HTTPS на 443.

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
                      timeout=30, follow_redirects=False, trust_env=False) as client:
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

В выводе должно быть `bot_api: authenticated` и `webhook_registered: true`. Напишите боту `/start` и откройте приложение из MAX. Если открыть сайт напрямую в браузере, подписанных данных запуска не будет и войти не получится.

Как назначить редактора: войдите через MAX, в ответе `/api/auth/me` найдите `user.id` вида `max:123456789`, допишите числовую часть в `MAX_ADMIN_IDS`, выполните `dc --profile max up -d` и откройте приложение заново. Cookie и initData никому не пересылайте, роль давайте только подтверждённому аккаунту.

### Каталог

```bash
dc exec -T app python backend/import_official.py
dc exec -T app python backend/import_official.py --apply
```

Первый вызов только проверяет набор, второй добавляет недостающие черновики. Сейчас их 10, и ни один не подтверждён полностью, так что после импорта публичный каталог пуст. Это нормально.

Дальше редактор через MAX сверяет источники, редакцию актов, правила, документы, сроки с часовым поясом и маршрут подачи, заполняет пробелы и проводит версию через draft → review → publish. Блокировки публикации обходить не надо, `SEED_DEMO` на сервере не включайте. Пока нет ни одной полностью проверенной опубликованной меры, путь «подбор → план» в production до конца не проверить, его проверяем локально на синтетике.

Справочные карточки (rc2) проходят тот же draft/review/publish, но с `publication_scope=reference`. Такая карточка никогда не даёт общий PASS и не считается открытым приёмом. FAIL возможен только по отдельно сверенным правилам из `reference_rule_ids`, документы в плане помечены как требующие уточнения. У старых версий scope по умолчанию `full`.

```bash
opora-compose exec -T app python backend/publish_reference.py
# применить от имени уже назначенного редактора:
opora-compose exec -T app python backend/publish_reference.py --apply --actor-max-id <MAX_ID>
```

Без `--apply` данные не меняются, повторный запуск ничего не дублирует, полные публикации справочными не заменяются. Токены в аргументах не передаются. Если запускать скрипт из исходников вне контейнера, кроме `DATABASE_URL` и `MAX_ADMIN_IDS` задайте `APP_ENV` и `PUBLIC_ORIGIN`: по умолчанию `APP_ENV=production`, и с http-адресом настройки просто не загрузятся. Для локальной базы берите значения из `.env`.

### Проверка на устройствах

На сервере:

```bash
dc ps
dc exec -T app alembic -c backend/alembic.ini check
dc exec -T app python backend/max_preflight.py
```

Потом в веб-версии MAX и отдельно на настоящем телефоне:

1. Вход через бота, учебных кнопок входа нет.
2. Анкета сохраняется: закрыть приложение, открыть снова, ответы на месте.
3. Статусы PASS/FAIL/UNKNOWN и отдельно статус приёма заявок.
4. План по опубликованной мере сохраняется, отметка документа переживает повторное открытие.
5. Официальный маршрут открывается (без подачи и подписи заявки).
6. Второй тестовый аккаунт не видит чужие планы и редактор.

Устройство, ОС, версию MAX, дату и результат записывайте в [docs/MAX-DEVICE-REPORT.md](docs/MAX-DEVICE-REPORT.md). Окно браузера шириной 390 px мобильный MAX не заменяет.

## Обслуживание сервера

На уже настроенном сервере вместо `dc` используется `opora-compose` (ставится из `deploy/opora-compose`). Он объединяет production и MAX CA и сразу включает worker.

```bash
opora-compose ps
opora-compose exec -T app python backend/max_preflight.py
# перезапуск уже проверенного образа:
opora-compose up -d --no-build --wait
opora-compose exec -T proxy nginx -s reload
```

`config` без `--quiet` здесь тоже не вызывайте.

### Обновление из исходников

Сначала резервная копия. Потом перенесите новые исходники, `/etc/opora-apk/production.env` оставьте как есть:

```bash
dc --profile max up -d --build --wait
dc ps
dc exec -T app alembic -c backend/alembic.ini current
curl --fail --show-error "https://$APP_DOMAIN/health"
```

Новые переменные окружения применяются только через `up -d`, простой `restart` их не подхватит. Откатывать схему после новых миграций вслепую нельзя.

Сейчас рабочий `/opt/opora-apk` на сервере содержит старый checkout, а запускается готовый образ rc2. Перед следующей сборкой на сервере разверните `source.zip` из rc2, старый checkout поверх рабочего образа не собирайте.

### Обновление готовым образом (rc2)

Перед обновлением сверьте файлы сервера с последним манифестом `docs/DEPLOYED-SOURCE-*`, сохраните пользовательские правки, выполните `deploy/check-restore.sh` и прогоните upgrade на восстановленной копии базы. Тесты с TRUNCATE и downgrade запускаются только в QA. У старых планов `assessment` может быть `null`, задним числом его не заполняем.

В production работает образ `opora-apk-reference-final:20260929` с тегом `opora-apk-production-app`. SHA-256 архива исходников и образа сверяйте с VERSION.json и SHA256SUMS.txt из комплекта rc2. Переключение с сохранением предыдущего тега:

```bash
docker load -i /path/to/verified/image.tar
docker tag opora-apk-production-app opora-apk-rollback:$(date +%Y%m%d%H%M%S)
docker tag opora-apk-reference-final:20260929 opora-apk-production-app
opora-compose up -d --no-build --wait
opora-compose exec -T proxy nginx -s reload
opora-compose exec -T app alembic -c backend/alembic.ini current
opora-compose exec -T app alembic -c backend/alembic.ini check
```

Это только само переключение, резервную копию и QA оно не заменяет. Файлы сервера, которые расходятся с манифестом, не перезаписывайте.

### Откат

Откатываться можно только на образ, который понимает `publication_scope`:

```bash
docker tag opora-apk-rollback:20260929-before-reference-final opora-apk-production-app
opora-compose up -d --no-build --wait
```

Образы 20260928 и r3 про справочные карточки не знают и оценят их неверно. Вернуться на них можно, только сняв справочные версии с публикации. Старый `/etc/opora-apk/deploy-20260928/rollback.sh` как раз возвращает r3, для rc2 он не годится. После отката запускайте только с `--no-build`, пока не договоритесь о возврате новой версии. Downgrade схемы и восстановление старого дампа поверх новых данных не делайте.

### Резервное копирование

Перед каждым обновлением и регулярно:

```bash
cd /opt/opora-apk
umask 077
install -d -m 0700 backups
BACKUP_FILE="backups/navigator-$(date +%F-%H%M%S).dump"
dc exec -T db pg_dump -U navigator -d navigator -Fc > "$BACKUP_FILE"
test -s "$BACKUP_FILE"
dc exec -T db pg_restore --list < "$BACKUP_FILE" > /dev/null
```

Дамп копируйте в защищённое хранилище вне VPS, отдельно храните `production.env` и исходники. Ежедневный запуск, контроль ошибок и срок хранения настраиваются после выбора хранилища, в проекте их нет. В публичный комплект дампы и секреты не кладите.

Восстановление проверяйте только в новую отдельную базу:

```bash
RESTORE_DB="navigator_restore_$(date +%Y%m%d%H%M%S)"
dc exec -T db createdb -U navigator "$RESTORE_DB"
dc exec -T db pg_restore -U navigator -d "$RESTORE_DB" --no-owner --exit-on-error < "$BACKUP_FILE"
dc exec -T db psql -U navigator -d "$RESTORE_DB" -c 'SELECT version_num FROM alembic_version;'
```

Одного списка содержимого дампа для уверенности мало, сравните нужные записи с рабочей базой. Переключение на восстановленную базу делается отдельно, в согласованное окно.

То же самое автоматически делает `deploy/check-restore.sh`:

```bash
cd /opt/opora-apk
bash deploy/check-restore.sh
```

Скрипт через `opora-compose` снимает дамп в `/etc/opora-apk/backups`, восстанавливает его в новую временную базу и сравнивает SHA-256 всех строк публичных таблиц. Рабочую базу он не трогает. Если исходная база изменилась во время копирования, проверка останавливается без вердикта. При успехе удаляется только временная база (дамп остаётся), при ошибке она сохраняется для разбора. Расписание и внешнее хранилище скрипт не настраивает.

### Остановка

```bash
dc --profile max stop
dc --profile max up -d --wait
```

### Если что-то не работает

| Симптом | Что проверить |
|---|---|
| Docker недоступен на Windows | запущен ли Docker Desktop, включены ли Linux-контейнеры |
| Сертификат не выдаётся | записи A/AAAA, доступность порта 80, не занят ли он |
| HTTPS 502 | `dc ps`, затем `dc logs --tail=80 app` (журналы наружу не выкладывайте) |
| MAX 401 | токен, время на сервере; откройте приложение из бота заново |
| TLS-ошибка MAX | подключён ли проверенный CA bundle |
| Нет редактора | MAX ID, `MAX_ADMIN_IDS`, пересоздан ли app |
| Каталог пуст | импортированные черновики ещё не проверены и не опубликованы |
| Production не стартует со старой БД | нужен отдельный том без демо-пользователей и синтетических мер |
| 429 при входе | лимит nginx на вход через `/api/auth/` (30 запросов в минуту с IP); `/api/auth/me` идёт по общему лимиту API |

Развёртывание считаем законченным, когда прошли HTTPS, webhook, настоящий вход и сохранение данных в веб- и мобильном MAX. Одного наличия конфигурации для этого недостаточно.

## Официальные данные

В каталоге по умолчанию открываются 10 реальных объявлений из `data/official/notices.json` (API: `/api/official-announcements`). Снимок едет вместе с образом, база для него не нужна. Это сверенные суммы и сроки, а не правила подбора. Учебные меры вынесены на отдельную вкладку. Автообновления нет: чтобы поменять данные, сверяем новую редакцию с официальным источником и пересобираем образ.

Обычный `import_official.py --apply` уже созданные записи не меняет. Новую версию проверенного набора создаёт отдельный флаг:

```powershell
docker compose exec -T app python backend/import_official.py --apply --stage-revision saratov-farm
```

На сервере то же самое через `opora-compose exec -T app`. Повторный запуск дубликат не создаст, существующие версии и правки пользователей не перезаписываются. Если у меры поменялись название или категория, импорт остановится и попросит сопоставить вручную. Новая версия остаётся черновиком. Её удобно проверить так: вход редактором → «Реальные меры» → новая версия → «Проверить правила на тестовой анкете» (личный профиль при этом не меняется). Опубликовать можно только после проверки источников, а у текущего гранта в источниках есть нерешённые противоречия.

## Локальные копии выпусков

`compose.deployed-local.yaml` запускает локально образ дизайн-выпуска `opora-apk-design:20260929`, его нужно заранее загрузить:

```powershell
Set-Location C:\EffectiveBusiness
docker compose -f compose.yaml -f compose.deployed-local.yaml up -d --no-build --wait
docker compose -f compose.yaml -f compose.deployed-local.yaml stop
```

Override берёт публичный CA bundle из `tmp/max-ca-bundle.pem`. Если его нет, скопируйте с настроенного VPS по SSH. Существующий `.env` сохраняйте.

QA поставки 20260928 живёт отдельно на http://localhost:8004: `docker compose -f compose.qa-deploy-20260928.yaml up -d --wait`. Для нового QA, который меняет данные, берите новый проект, новый том и свободный порт, старый стенд не очищайте.

## Материалы сдачи

Папка `output` в Git не входит. Комплект для жюри (презентация, архив исходников, API и инструкция) лежит отдельно в `D:\toResult`, секретов в нём нет.
