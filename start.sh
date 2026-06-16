#!/bin/bash

# Start Redis server in the background
redis-server --daemonize yes

# Wait for redis to start
sleep 2

# Start Celery beat in the background
celery -A tasks.celery_app beat --loglevel=info &

# Start Celery worker in the background
# We use gevent pool because we are on Linux/Docker
celery -A tasks.celery_app worker --loglevel=info --concurrency=1 &

# Start the Flask app using Waitress on port 7860
python -c "from waitress import serve; from app import app; print('Starting server on port 7860...'); serve(app, host='0.0.0.0', port=7860)"
