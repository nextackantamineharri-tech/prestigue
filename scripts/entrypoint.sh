#!/bin/bash

# Wait for database (Railway handles service readiness, but we'll log attempt)
echo "Initializing Prestige Terminal..."


# Run migrations
echo "Running database migrations..."
flask db upgrade

# Start Gunicorn
echo "Starting Gunicorn server on port ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 4 --threads 2 --access-logfile - --error-logfile - "run:app"
