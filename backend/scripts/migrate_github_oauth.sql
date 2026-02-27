-- Run this if you have an existing database before GitHub OAuth
-- PostgreSQL

-- Add github_id column (nullable, unique)
ALTER TABLE users ADD COLUMN IF NOT EXISTS github_id VARCHAR(64) UNIQUE;

-- Make hashed_password nullable for OAuth-only users
ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;

-- Create index for github_id lookups (optional, UNIQUE already creates one)
-- CREATE INDEX IF NOT EXISTS ix_users_github_id ON users (github_id);
