# Полное развёртывание «Опора АПК»

Актуальная проверенная версия: **opora-apk-20260929-rc2**. [Отчёт сборки и ограничения](docs/RELEASE-20260929-RC2.md).
Навигатор для КФХ и сельскохозяйственных ИП Саратовской области: анкета, объяснимый подбор, карточка отбора, план документов и официальный маршрут. FastAPI + React/TypeScript + PostgreSQL, запуск Docker Compose. Опубликованы 10 реальных справочных карточек с сохранением планов. Полный допуск остаётся предметом проверки; локальная демонстрация явно синтетическая.


Инструкция полного развёртывания. Действующий стенд: https://opora-apk.159-194-249-97.sslip.io/ .
Бот: https://max.ru/t761_hakaton_max_bot . Доступ владельца: `ssh effectivebusiness`.
Шаги привязки мини-приложения — [docs/USER-ACTIONS.md](docs/USER-ACTIONS.md).

По разрешению владельца от 27.09.2026 секреты рабочего стенда хранятся на его VPS
в `/etc/opora-apk/production.env` (0600, каталог 0700), вне исходников и сборки.
Токен отправляется только официальному API MAX. Локальный `.env` не изменён.

Для уже установленного сервера после SSH используйте:

```bash
opora-compose ps
opora-compose exec -T app python backend/max_preflight.py
# Повторный запуск уже проверенного образа:
opora-compose up -d --no-build --wait
opora-compose exec -T proxy nginx -s reload
```

Команда `opora-compose` установлена из `deploy/opora-compose`; объединяет только
production и MAX CA, включает worker. Не выводите `config` без `--quiet`.
Для нового сервера выполните шаги ниже.

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

Для предварительной диагностики токен можно сохранить в `C:\EffectiveBusiness\.env`, строка `MAX_BOT_TOKEN=`. Не вставляйте его в `.env.example`, React, README или чат. На сервере используется отдельный `/etc/opora-apk/production.env`.

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
install -d -m 0700 /etc/opora-apk
test -f /etc/opora-apk/production.env || cp deploy/production.env.example /etc/opora-apk/production.env
chmod 600 /etc/opora-apk/production.env
nano /etc/opora-apk/production.env
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
dc() { docker compose --env-file /etc/opora-apk/production.env -f compose.production.yaml "$@"; }
dc config --quiet
```

При новом SSH-входе повторите `cd` и определение функции. Не вызывайте `config` без `--quiet`: полный вывод раскрывает окружение.

Если TLS официального API MAX требует дополнительной цепочки доверия, получите проверенный полный CA bundle по [документации MAX](https://dev.max.ru/docs-api/changelog-api), сохраните его на сервере и добавьте `MAX_CA_BUNDLE_HOST=/абсолютный/путь/ca-bundle.pem` в `/etc/opora-apk/production.env`. Замените функцию:

```bash
dc() { docker compose --env-file /etc/opora-apk/production.env -f compose.production.yaml -f compose.max-ca.yaml "$@"; }
```

Не отключайте проверку TLS. На действующем сервере bundle уже получен с официального CDN Госуслуг и подключён только MAX-клиентам; см. docs/DEPLOYMENT.md.

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

Для последующего продления без остановки сайта создайте webroot:

```bash
install -d -m 0755 /var/www/certbot
```

В `production.env` укажите `ACME_WEBROOT=/var/www/certbot`. Compose подключает его
к Nginx; HTTP-путь `/.well-known/acme-challenge/` доступен центру сертификации.
Остальные HTTP-запросы перенаправляются на HTTPS. После запуска раздела 8
переключите Certbot на webroot и установите hook, как указано ниже.

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

После запуска HTTPS настройте и проверьте продление без остановки proxy:

```bash
# Этот wrapper требует настроенного CA bundle из раздела 6.
install -m 0755 deploy/opora-compose /usr/local/sbin/opora-compose
install -m 0755 deploy/renew-certificate.sh /etc/letsencrypt/renewal-hooks/deploy/opora-apk
certbot reconfigure --cert-name "$APP_DOMAIN" --webroot -w /var/www/certbot --non-interactive
systemctl enable --now certbot.timer
certbot renew --cert-name "$APP_DOMAIN" --dry-run
RENEWED_LINEAGE="/etc/letsencrypt/live/$APP_DOMAIN" /etc/letsencrypt/renewal-hooks/deploy/opora-apk
```

Reconfigure проверяет webroot через тестовый выпуск сертификата. Последняя команда
отдельно проверяет копирование действующего сертификата и reload Nginx.
Контролируйте срок сертификата и результат будущих продлений.

## 9. Подключите настоящий MAX

**Для текущего бота хакатона:** капитан передаёт HTTPS-адрес сайта через
[форму организаторов](https://sbor-ssylok-dlya-mini-prilojeniy.testograf.ru/).
Нужны ФИО капитана, регистрационный email, название команды и URL сайта;
токен не требуется. Подробности — docs/USER-ACTIONS.md.
Ниже описан общий способ для владельцев доступа к бизнес-кабинету, а не
подтверждённый доступ участника к выданному боту.


В кабинете MAX: «Чат-боты» → нужный бот → настройки мини-приложения. В поле URL укажите **`https://ВАШ_ДОМЕН/`**. В переменной `MAX_APP_URL` должна остаться **ссылка `https://max.ru/ИМЯ_БОТА?startapp`**. [Инструкция MAX](https://dev.max.ru/docs/webapps/introduction).

Примените окружение и запустите обработчик бота:

```bash
dc --profile max up -d --wait
dc exec -T app python backend/max_preflight.py
```

Диагностика выполняет GET /me и GET /subscriptions, выводит статусы и публичную ссылку бота; ничего не регистрирует. Признак webhook_registered проверяйте отдельно от кода завершения. При `network_tls_or_invalid_response` проверьте сеть и CA bundle, не отключайте TLS.

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

Для 16 сценариев `DATA-API.yaml` сначала запустите отдельный стенд, чтобы
не менять сохранённые данные обычной локальной версии:

```powershell
docker compose -p opora-apk-qa-20260927 -f compose.release-check.yaml up -d --wait
```

Затем восстановите локальную Python-среду при необходимости (нужен установленный Python 3.12):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/check_data_api.py --base-url http://localhost:8001
```

Проверка с указанным --base-url обращается к localhost:8001 и изменяет только учебные анкеты отдельного стенда. Для production она не предназначена.

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

Копируйте дамп в защищённое хранилище вне VPS. Отдельно сохраняйте `/etc/opora-apk/production.env` и исходники. Настройте ежедневный запуск, контроль ошибок и срок хранения после выбора хранилища: проект не включает эти внешние настройки автоматически. Дампы и секреты не включайте в публичный комплект.

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

Для обновления сделайте резервную копию, перенесите новые исходники с сохранением `/etc/opora-apk/production.env`, затем:

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


## Обновление существующих официальных черновиков

Обычный `import_official.py --apply` сохраняет ранее созданные записи без изменений.
После проверки подготовленного набора используйте явное создание новой версии:

```powershell
docker compose exec -T app python backend/import_official.py --apply --stage-revision saratov-farm
```

На VPS команда аналогична, но начинается с `opora-compose exec -T app`.
Повтор одного набора не создаёт дубликат. Существующие версии и пользовательские
правки не перезаписываются. При изменённом названии / категории импорт останавливается
для ручного сопоставления. Новая версия остаётся черновиком. Для проверки откройте
локальный вход редактора → Реальные меры → новая версия → «Проверить правила
на тестовой анкете». Тестовая анкета не меняет личный профиль. Публикация требует
завершённой проверки источников; у текущего гранта есть нерешённые противоречия.

## Проверка полного восстановления на настроенном VPS

После копирования исходников на VPS:

```bash
cd /opt/opora-apk
bash deploy/check-restore.sh
```

Скрипт использует существующий `opora-compose`, сохраняет закрытый дамп в
`/etc/opora-apk/backups`, создаёт отдельную новую БД, восстанавливает её и сравнивает
SHA-256 всех строк публичных таблиц. Рабочая БД не очищается и не переключается.
При изменении исходной базы во время копирования проверка прекращается без
утверждения успеха. При успешном сравнении удаляется только созданная этим запуском
временная БД; дамп остаётся. При ошибке временная БД сохраняется для разбора.
Скрипт не настраивает ежедневное копирование или внешнее хранилище.


## Обновление существующего VPS проверенным артефактом

Перед обновлением сверяйте файлы сервера с последним DEPLOYED-SOURCE-манифестом,
сохраняйте пользовательские правки, выполняйте deploy/check-restore.sh и испытывайте
upgrade на восстановленной отдельной БД. Тесты с TRUNCATE/downgrade — только в QA.
При сравнении старого плана допускайте assessment=null: не заполняйте историю задним числом.

После QA сверяйте SHA-256 source.tar.gz и image.tar с
docs/DEPLOYMENT-20260928.json и docs/ARTIFACT-20260928-SHA256.txt. На существующем VPS
используйте проверенный образ, сохраняя предыдущий тег и текущую БД:

```bash
docker load -i /path/to/verified/image.tar
docker tag opora-apk-deploy:20260928 opora-apk-production-app
opora-compose up -d --no-build --wait
opora-compose exec -T proxy nginx -s reload
opora-compose exec -T app alembic -c backend/alembic.ini current
opora-compose exec -T app alembic -c backend/alembic.ini check
```

Это команды переключения после обязательных предварительных проверок, а не
замена backup/QA. Не перезаписывайте расходящиеся с манифестом файлы сервера.
Процедура и границы текущего отката: docs/HANDOFF-DEPLOY.md. Для подготовленного
отката этой поставки: `bash /etc/opora-apk/deploy-20260928/rollback.sh`.
Он сохраняет актуальную БД, предварительно делает новый dump и возвращает образ r3.
Не выполняйте downgrade или восстановление старого dump поверх новых данных.
После такого отката запускайте только --no-build до согласованного возврата новой версии.

Основной локальный запуск закреплён за тем же проверенным образом:

```powershell
Set-Location C:\EffectiveBusiness
docker compose -f compose.yaml -f compose.deployed-local.yaml up -d --no-build --wait
docker compose -f compose.yaml -f compose.deployed-local.yaml stop
```

Override использует публичный CA bundle tmp/max-ca-bundle.pem. При восстановлении
окружения получите его с уже настроенного VPS по SSH; не отключайте TLS-проверку
и не заменяйте bundle приватным ключом. Существующий .env сохраняйте. QA этой поставки
запускается отдельно: `docker compose -f compose.qa-deploy-20260928.yaml up -d --wait`;
адрес http://localhost:8004. Для нового повторного изменяющего QA используйте новый
проект/том и свободный порт, не очищайте прежний стенд.

Реальные редакции импортируйте через `import_official.py --apply --stage-revision ID`.
Публикация — только после проверки источников через draft → review → publish
с явно подтверждёнными правами редактора. Состояние каталога и инструкция web-MAX/
Android находятся в docs/HANDOFF-DEPLOY.md; старые проверки устройств не заменяют новые.

## Проверка подбора на учебном примере

Для оценки интерфейса без токена MAX и без изменения рабочей базы:

```powershell
docker compose --env-file .env.example -f compose.demo-evaluation.yaml up -d --build --wait
```

Откройте http://localhost:8000. На главной нажмите «Заполнить учебный пример КФХ», затем «3 Ваш проект» → «Сохранить и подобрать» → «Соответствует ответам анкеты». Учебный грант «Развитие фермерского хозяйства» подходит при регионе регистрации 64, статусе КФХ, цели equipment и собственных средствах от 300000 рублей. Готовый пример задаёт 450000 рублей. Это вымышленные условия для проверки программы, а не условия настоящего гранта.

Окружение opora-evaluation использует отдельный том evaluation_data, порт 8000 только на 127.0.0.1 и пустые настройки MAX. Если порт занят другим локальным приложением, сначала остановите именно его; не удаляйте тома с данными. Остановка демо с сохранением ответов:

```powershell
docker compose --env-file .env.example -f compose.demo-evaluation.yaml stop
```


## Справочная публикация rc2

Справочные карточки проходят обычные draft/review/publish и сохраняют ограничения
исследования. Поле publication_scope=reference не разрешает общий PASS и открытый
приём. Отдельно сверенные правила reference_rule_ids могут дать FAIL. Документы
справочного плана требуют уточнения. Старые версии по умолчанию имеют scope full.

После переноса исходников rc2 и развёртывания нового образа команда публикации:

```bash
python backend/publish_reference.py
# Для применения укажите реальный MAX ID уже назначенного редактора:
python backend/publish_reference.py --apply --actor-max-id <MAX_ID>
```

В контейнере рабочего сервера используйте `opora-compose exec -T app` перед python.
Без --apply команда не меняет данные. Повторный запуск идемпотентен.
Существующие полные публикации не заменяются справочными. Токены не передаются
в аргументах. Для работы из исходников нужен настроенный DATABASE_URL и MAX_ADMIN_IDS.
Текущий сервер запускает готовый образ; его старый checkout не является исходниками rc2.
Сначала разверните новый source.zip перед следующей сборкой на сервере.
