#!/bin/sh
set -e

host="${POSTGRES_HOST:-db}"
port="${POSTGRES_PORT:-5432}"

echo "⏳ Waiting for PostgreSQL at $host:$port..."
until nc -z "$host" "$port"; do
  sleep 1
done

echo "✅ PostgreSQL is up - starting FastAPI"
exec "$@"
