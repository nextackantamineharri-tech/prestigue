#!/bin/bash

# Wait for database (Railway handles service readiness, but we'll log attempt)
echo "Initializing Prestige Terminal..."


# Run migrations
echo "Running database migrations..."
flask db upgrade

# Start Gunicorn
PORT="${PORT:-8080}"
export PORT
echo "Starting Gunicorn server on port ${PORT}..."
exec gunicorn --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY:-2} --threads ${GUNICORN_THREADS:-2} --timeout ${GUNICORN_TIMEOUT:-120} --access-logfile - --error-logfile - "run:app"
