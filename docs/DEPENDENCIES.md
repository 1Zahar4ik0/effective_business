# Зависимости

Основные библиотеки: FastAPI (MIT), Pydantic (MIT), SQLAlchemy (MIT), Alembic (MIT), Uvicorn (BSD-3-Clause), HTTPX (BSD-3-Clause), Psycopg (LGPL-3.0), React (MIT), TypeScript (Apache-2.0), Vite (MIT), Lucide (ISC), openapi-typescript (MIT), pytest (MIT). PostgreSQL — PostgreSQL License. Точные LICENSE/NOTICE поставляются в дистрибутивах зависимостей; при распространении образа их необходимо сохранять. Это инвентаризация, не юридическое заключение.

Фактические версии: backend/requirements.txt и frontend/package-lock.json. Прямые frontend-диапазоны разрешаются только через зафиксированный lock-файл; воспроизводимая установка — npm ci.

Официальные материалы для реализации:

- https://fastapi.tiangolo.com/deployment/docker/
- https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- https://alembic.sqlalchemy.org/en/latest/tutorial.html
- https://react.dev/learn/build-a-react-app-from-scratch
- https://vite.dev/guide/
- MAX: docs/MAX.md.

Не используются платные API, OpenAI/LLM, Redis или внешние аналитические счётчики. В демо интерфейс не загружает MAX Bridge, пока токен не настроен. Иллюстрация главного экрана создана CSS и иконками Lucide.

Для подготовленного production proxy используется официальный nginx:1.30.5-alpine, лицензия BSD-2-Clause. Требования и ссылки — docs/DEPLOYMENT.md. PostgreSQL и приложение в production используют те же фиксированные версии, что локальный MVP.

Исследовательский `backend/extract_official_sources.py` выполнялся отдельно через bundled Python с pypdf; визуальная проверка сканов — pypdfium2. Эти инструменты не нужны для запуска сервиса, импорта подготовленного catalog.json или сборки Docker. Оригиналы и извлечённые тексты уже включены в исходный комплект; в образ входят только подготовленные данные, без тяжёлых архивов sources.

Презентации подготовлены по навыку Presentations через `@oai/artifact-tool` из среды Codex; PDF — ReportLab, проверка — pypdf, pypdfium2 и Pillow по навыку PDF. Это инструменты подготовки материалов, а не зависимости приложения. Для повторного выполнения авторских скриптов требуется соответствующая среда Codex и пути к её библиотекам. Переданный PPTX можно редактировать обычным редактором презентаций. PDF содержит растровые страницы. Готовые артефакты находятся в комплекте `output/submission`, отдельно от архива исходников.
