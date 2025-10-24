#!/bin/bash
echo "Stopping the server..."
pkill -f "uvicorn src.server:app"
echo "Server stopped"
