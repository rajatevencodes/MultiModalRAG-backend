#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure Homebrew binaries (like tesseract) are on PATH for macOS
export PATH="/opt/homebrew/bin:$PATH"

echo "Starting Celery Worker (foreground)..."
celery -A src.services.celery:celery_app worker --loglevel=info --pool=threads


