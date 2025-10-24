#!/bin/bash
echo "Starting the server..."
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
