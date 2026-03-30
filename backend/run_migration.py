#!/usr/bin/env python3
"""
Flowra CRM — One-shot DB migration runner
Run from the backend directory:
    python run_migration.py
"""

import subprocess
import sys
import os

DB_URL = os.getenv("DATABASE_URL", "postgresql://localhost/flowra_db")

# Strip psycopg2 driver prefix for psql connection string parsing
# postgresql://localhost/flowra_db  →  dbname=flowra_db host=localhost
def url_to_psql_args(url: str) -> list[str]:
    from urllib.parse import urlparse
    p = urlparse(url)
    args = []
    if p.hostname:  args += ["-h", p.hostname]
    if p.port:      args += ["-p", str(p.port)]
    if p.username:  args += ["-U", p.username]
    if p.path:      args += [p.path.lstrip("/")]   # dbname
    return args

SQL = """
DO $$ BEGIN
    CREATE TYPE leadstatus AS ENUM ('new','contacted','qualified','converted','lost');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

ALTER TABLE contacts
    ADD COLUMN IF NOT EXISTS lead_status leadstatus NOT NULL DEFAULT 'new';

CREATE INDEX IF NOT EXISTS idx_contacts_workspace_lead_status
    ON contacts (workspace_id, lead_status);

DO $$ BEGIN
    CREATE TYPE taskstatus AS ENUM ('todo','in_progress','done','cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE taskpriority AS ENUM ('low','medium','high','urgent');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

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

SELECT 'Migration complete' AS result;
"""

def run_via_psycopg2():
    try:
        import psycopg2
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(SQL)
        # fetch SELECT result if any
        try:
            row = cur.fetchone()
            if row:
                print(f"✓ {row[0]}")
        except Exception:
            pass
        cur.close()
        conn.close()
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"psycopg2 error: {e}")
        return False

def run_via_psql():
    args = ["psql"] + url_to_psql_args(DB_URL) + ["-c", SQL]
    try:
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Migration complete via psql")
            if "Migration complete" in result.stdout:
                print("  Tables and columns created successfully")
            return True
        else:
            print(f"psql error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("psql not found in PATH")
        return False

if __name__ == "__main__":
    print("🔧 Flowra CRM — Running DB migration...")
    print(f"   Database: {DB_URL}")
    print()

    if run_via_psycopg2():
        print("\n✅ Done! Restart the backend server now.")
    elif run_via_psql():
        print("\n✅ Done! Restart the backend server now.")
    else:
        print("\n❌ Automatic migration failed. Run this manually:")
        print(f"   psql {' '.join(url_to_psql_args(DB_URL))} -f fix_db.sql")
        sys.exit(1)
