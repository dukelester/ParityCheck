-- Create PostgreSQL role and database for ParityCheck (run without Docker)
-- From project root: sudo -u postgres psql -f backend/scripts/setup_db.sql
-- From backend/:   sudo -u postgres psql -f scripts/setup_db.sql

-- Create role (ignore error if exists)
DO $$ BEGIN
  CREATE ROLE paritycheck WITH LOGIN PASSWORD 'paritycheck';
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Create database (ignore error if exists)
SELECT 'CREATE DATABASE paritycheck OWNER paritycheck'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'paritycheck')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE paritycheck TO paritycheck;
