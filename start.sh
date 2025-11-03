#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Redis Server..."
(cd redis && docker-compose -f docker-compose-up.yaml up -d)

echo "Starting Celery Worker..."
celery -A src.services.celery:celery_app worker --loglevel=info --pool=threads --detach

echo "Starting the server..."
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000


