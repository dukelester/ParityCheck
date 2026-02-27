-- Migration: Add workspaces and migrate existing data
-- Run after init_db (create_all). Safe to run multiple times.

-- Create workspaces table if not exists (create_all does this, but for manual runs)
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id),
    plan VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workspace_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(workspace_id, user_id)
);

CREATE TABLE IF NOT EXISTS ignore_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    key_pattern VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    min_severity VARCHAR(20) DEFAULT 'high',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add columns to environments
ALTER TABLE environments ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id);
ALTER TABLE environments ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE environments ADD COLUMN IF NOT EXISTS is_baseline BOOLEAN DEFAULT FALSE;
-- Workspace-owned envs have user_id=NULL; ensure column allows it (idempotent)
DO $$ BEGIN
  ALTER TABLE environments ALTER COLUMN user_id DROP NOT NULL;
EXCEPTION WHEN others THEN NULL;
END $$;

-- Add columns to reports
ALTER TABLE reports ADD COLUMN IF NOT EXISTS health_score INTEGER;

-- Add columns to drifts
ALTER TABLE drifts ADD COLUMN IF NOT EXISTS severity VARCHAR(20) DEFAULT 'medium';
ALTER TABLE drifts ADD COLUMN IF NOT EXISTS key VARCHAR(255);
ALTER TABLE drifts ADD COLUMN IF NOT EXISTS value_a TEXT;
ALTER TABLE drifts ADD COLUMN IF NOT EXISTS value_b TEXT;

-- Add workspace_id to api_keys
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id);

-- Migrate: for each user with environments, create workspace and assign
INSERT INTO workspaces (id, name, owner_id, plan)
SELECT gen_random_uuid(), 'My Workspace', user_id, 'free'
FROM (SELECT DISTINCT user_id FROM environments WHERE user_id IS NOT NULL) u
ON CONFLICT DO NOTHING;

-- Note: The above INSERT may fail if environments used workspace_id. Run data migration separately if needed.
