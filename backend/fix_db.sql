-- ============================================================
-- Flowra CRM — Database Fix Script
-- Run this once from your backend folder:
--   psql -U flowra -d flowra_db -f fix_db.sql
-- ============================================================

-- 1. leadstatus ENUM
DO $$ BEGIN
    CREATE TYPE leadstatus AS ENUM ('new','contacted','qualified','converted','lost');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 2. lead_status column on contacts
ALTER TABLE contacts
    ADD COLUMN IF NOT EXISTS lead_status leadstatus NOT NULL DEFAULT 'new';

CREATE INDEX IF NOT EXISTS idx_contacts_workspace_lead_status
    ON contacts (workspace_id, lead_status);

-- 3. taskstatus / taskpriority ENUMs
DO $$ BEGIN
    CREATE TYPE taskstatus AS ENUM ('todo','in_progress','done','cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE taskpriority AS ENUM ('low','medium','high','urgent');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 4. tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id              VARCHAR(36)  PRIMARY KEY,
    workspace_id    VARCHAR(36)  NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    status          taskstatus   NOT NULL DEFAULT 'todo',
    priority        taskpriority NOT NULL DEFAULT 'medium',
    due_at          TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    contact_id      VARCHAR(36)  REFERENCES contacts(id) ON DELETE SET NULL,
    deal_id         VARCHAR(36)  REFERENCES deals(id)    ON DELETE SET NULL,
    assigned_to     VARCHAR(36)  REFERENCES users(id)    ON DELETE SET NULL,
    created_by      VARCHAR(36)  REFERENCES users(id)    ON DELETE SET NULL,
    deleted_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_workspace_id       ON tasks (workspace_id);
CREATE INDEX IF NOT EXISTS idx_task_workspace_status   ON tasks (workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_task_workspace_assignee ON tasks (workspace_id, assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_task_contact_id         ON tasks (contact_id)  WHERE contact_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_task_deal_id            ON tasks (deal_id)     WHERE deal_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_task_deleted_at         ON tasks (deleted_at)  WHERE deleted_at IS NULL;

-- Done!
SELECT 'Migration complete ✓' AS status;
