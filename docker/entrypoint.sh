#!/bin/sh

set -e

echo "Waiting for database..."

# wait for postgres
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  sleep 1
done

echo "Database ready!"


exec "$@"
