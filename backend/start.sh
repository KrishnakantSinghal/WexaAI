#!/bin/sh
set -e
echo "Running database migrations..."
alembic upgrade head
echo "Seeding demo data (idempotent)..."
python -m scripts.seed_data || echo "  seed skipped or failed (non-fatal)"
echo "Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 2
