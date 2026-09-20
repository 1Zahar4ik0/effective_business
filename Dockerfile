FROM node:24.14.1-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --no-fund --no-audit
COPY frontend/ ./
RUN npm run build

FROM python:3.12.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt && useradd --create-home --uid 10001 navigator
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY --from=frontend /build/dist /app/frontend/dist
USER navigator
EXPOSE 8000
CMD ["python", "-m", "app.bootstrap"]
