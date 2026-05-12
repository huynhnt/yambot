#!/bin/bash

# Start the Telegram Bot in the background
echo "Starting Telegram Bot..."
python telegram_bot.py &

# Start the FastAPI server in the foreground
echo "Starting FastAPI Server..."
exec uvicorn main:app --host 0.0.0.0 --port 8080
