FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY alembic.ini alembic.ini
COPY backend backend

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m backend.scripts.seed_admin && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
