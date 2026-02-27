#!/usr/bin/env bash
# Create PostgreSQL role and database for ParityCheck (run without Docker)
# Run: sudo -u postgres psql -f scripts/setup_db.sql
# Or: bash scripts/setup_db.sh
set -e

echo "Creating PostgreSQL role and database for ParityCheck..."

if command -v psql &>/dev/null; then
  sudo -u postgres psql -v ON_ERROR_STOP=1 <<'SQL'
-- Create role if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'paritycheck') THEN
    CREATE ROLE paritycheck WITH LOGIN PASSWORD 'paritycheck';
    RAISE NOTICE 'Created role paritycheck';
  ELSE
    RAISE NOTICE 'Role paritycheck already exists';
  END IF;
END
$$;

-- Create database
SELECT 'CREATE DATABASE paritycheck OWNER paritycheck'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'paritycheck')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE paritycheck TO paritycheck;
\c paritycheck
GRANT ALL ON SCHEMA public TO paritycheck;

\echo 'Done! Connect with: postgresql+asyncpg://paritycheck:paritycheck@localhost:5432/paritycheck'
SQL
else
  echo "psql not found. Run this manually as postgres user:"
  echo ""
  echo "  sudo -u postgres psql -c \"CREATE ROLE paritycheck WITH LOGIN PASSWORD 'paritycheck';\""
  echo "  sudo -u postgres psql -c \"CREATE DATABASE paritycheck OWNER paritycheck;\""
  echo ""
fi
