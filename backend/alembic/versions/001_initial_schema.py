"""initial_schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-01-01 00:00:00.000000

Pure-SQL migration — bypasses SQLAlchemy's ENUM auto-create behaviour entirely.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # ENUM types (idempotent PL/pgSQL block — works on all PG versions)
    # -----------------------------------------------------------------------
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('super_admin','admin','manager','sales','viewer');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE workspaceplan AS ENUM ('starter','growth','agency');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE memberrole AS ENUM ('owner','admin','member');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE contactsource AS ENUM ('manual','import','whatsapp','gmail','web_form','referral');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE dealstage AS ENUM ('new','contacted','qualified','proposal','negotiation','won','lost');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE dealpriority AS ENUM ('low','medium','high');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE messagedirection AS ENUM ('inbound','outbound');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE messagetype AS ENUM ('text','image','document','audio','video','template','interactive');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE messagestatus AS ENUM ('queued','sent','delivered','read','failed');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE emaildirection AS ENUM ('inbound','outbound');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE subscriptionstatus AS ENUM ('created','authenticated','active','halted','cancelled','expired');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE paymentstatus AS ENUM ('pending','captured','failed','refunded');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE billingplan AS ENUM ('starter','growth','agency');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE notificationtype AS ENUM (
                'deal_won','new_lead','overdue_task','payment_failed',
                'team_mention','whatsapp_received','email_received',
                'autopilot_completed','system'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # -----------------------------------------------------------------------
    # 1. users
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id                  VARCHAR(36)   PRIMARY KEY,
            created_at          TIMESTAMPTZ   NOT NULL,
            updated_at          TIMESTAMPTZ   NOT NULL,
            deleted_at          TIMESTAMPTZ,
            name                VARCHAR(255)  NOT NULL,
            email               VARCHAR(255)  NOT NULL,
            hashed_password     VARCHAR(255)  NOT NULL,
            avatar_url          VARCHAR(500),
            role                userrole      NOT NULL DEFAULT 'sales',
            is_active           BOOLEAN       NOT NULL DEFAULT TRUE,
            is_verified         BOOLEAN       NOT NULL DEFAULT FALSE,
            is_superuser        BOOLEAN       NOT NULL DEFAULT FALSE,
            last_login          TIMESTAMPTZ,
            login_count         INTEGER       NOT NULL DEFAULT 0,
            failed_attempts     INTEGER       NOT NULL DEFAULT 0,
            locked_until        TIMESTAMPTZ,
            password_updated_at TIMESTAMPTZ,
            preferences         JSONB         NOT NULL DEFAULT '{}',
            CONSTRAINT uq_user_email UNIQUE (email)
        );
        CREATE INDEX IF NOT EXISTS idx_user_email      ON users (email);
        CREATE INDEX IF NOT EXISTS idx_user_role       ON users (role);
        CREATE INDEX IF NOT EXISTS idx_user_deleted_at ON users (deleted_at);
    """)

    # -----------------------------------------------------------------------
    # 2. workspaces
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id              VARCHAR(36)     PRIMARY KEY,
            created_at      TIMESTAMPTZ     NOT NULL,
            updated_at      TIMESTAMPTZ     NOT NULL,
            deleted_at      TIMESTAMPTZ,
            name            VARCHAR(255)    NOT NULL,
            slug            VARCHAR(100)    NOT NULL UNIQUE,
            logo_url        VARCHAR(500),
            plan            workspaceplan   NOT NULL DEFAULT 'starter',
            plan_expires_at TIMESTAMPTZ,
            owner_id        VARCHAR(36)     NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            settings        JSONB           NOT NULL DEFAULT '{}',
            is_active       BOOLEAN         NOT NULL DEFAULT TRUE
        );
        CREATE INDEX IF NOT EXISTS idx_workspace_slug       ON workspaces (slug);
        CREATE INDEX IF NOT EXISTS idx_workspace_owner      ON workspaces (owner_id);
        CREATE INDEX IF NOT EXISTS idx_workspace_plan       ON workspaces (plan);
        CREATE INDEX IF NOT EXISTS idx_workspace_deleted_at ON workspaces (deleted_at);
    """)

    # -----------------------------------------------------------------------
    # 3. workspace_members
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS workspace_members (
            id           VARCHAR(36)  PRIMARY KEY,
            created_at   TIMESTAMPTZ  NOT NULL,
            updated_at   TIMESTAMPTZ  NOT NULL,
            workspace_id VARCHAR(36)  NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            user_id      VARCHAR(36)  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role         memberrole   NOT NULL DEFAULT 'member',
            is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
            CONSTRAINT uq_workspace_member UNIQUE (workspace_id, user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_member_workspace ON workspace_members (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_member_user      ON workspace_members (user_id);
    """)

    # -----------------------------------------------------------------------
    # 4. contacts
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id                VARCHAR(36)    PRIMARY KEY,
            created_at        TIMESTAMPTZ    NOT NULL,
            updated_at        TIMESTAMPTZ    NOT NULL,
            deleted_at        TIMESTAMPTZ,
            workspace_id      VARCHAR(36)    NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            first_name        VARCHAR(100)   NOT NULL,
            last_name         VARCHAR(100),
            email             VARCHAR(255),
            phone             VARCHAR(30),
            whatsapp_number   VARCHAR(30),
            avatar_url        VARCHAR(500),
            company_name      VARCHAR(255),
            job_title         VARCHAR(255),
            source            contactsource  NOT NULL DEFAULT 'manual',
            lead_score        INTEGER        NOT NULL DEFAULT 0,
            tags              JSONB          NOT NULL DEFAULT '[]',
            custom_fields     JSONB          NOT NULL DEFAULT '{}',
            last_contacted_at TIMESTAMPTZ,
            created_by        VARCHAR(36)    REFERENCES users(id) ON DELETE SET NULL,
            CONSTRAINT uq_contact_email_per_workspace UNIQUE (workspace_id, email)
        );
        CREATE INDEX IF NOT EXISTS idx_contact_workspace   ON contacts (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_contact_email       ON contacts (email);
        CREATE INDEX IF NOT EXISTS idx_contact_phone       ON contacts (phone);
        CREATE INDEX IF NOT EXISTS idx_contact_company     ON contacts (workspace_id, company_name);
        CREATE INDEX IF NOT EXISTS idx_contact_lead_score  ON contacts (workspace_id, lead_score);
        CREATE INDEX IF NOT EXISTS idx_contact_deleted_at  ON contacts (deleted_at);
    """)

    # -----------------------------------------------------------------------
    # 5. pipelines
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS pipelines (
            id           VARCHAR(36)  PRIMARY KEY,
            created_at   TIMESTAMPTZ  NOT NULL,
            updated_at   TIMESTAMPTZ  NOT NULL,
            deleted_at   TIMESTAMPTZ,
            workspace_id VARCHAR(36)  NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name         VARCHAR(255) NOT NULL,
            description  TEXT,
            is_default   BOOLEAN      NOT NULL DEFAULT FALSE,
            is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
            settings     JSONB        NOT NULL DEFAULT '{}',
            CONSTRAINT uq_pipeline_name_per_workspace UNIQUE (workspace_id, name)
        );
        CREATE INDEX IF NOT EXISTS idx_pipeline_workspace ON pipelines (workspace_id);
    """)

    # -----------------------------------------------------------------------
    # 6. pipeline_stages
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_stages (
            id               VARCHAR(36) PRIMARY KEY,
            created_at       TIMESTAMPTZ NOT NULL,
            updated_at       TIMESTAMPTZ NOT NULL,
            pipeline_id      VARCHAR(36) NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
            name             VARCHAR(100) NOT NULL,
            "order"          INTEGER     NOT NULL,
            probability      FLOAT       NOT NULL DEFAULT 0.0,
            color            VARCHAR(20) NOT NULL DEFAULT '#3B82F6',
            is_won_stage     BOOLEAN     NOT NULL DEFAULT FALSE,
            is_lost_stage    BOOLEAN     NOT NULL DEFAULT FALSE,
            automation_rules JSONB       NOT NULL DEFAULT '{}',
            CONSTRAINT uq_stage_order UNIQUE (pipeline_id, "order"),
            CONSTRAINT uq_stage_name  UNIQUE (pipeline_id, name)
        );
        CREATE INDEX IF NOT EXISTS idx_stage_pipeline ON pipeline_stages (pipeline_id);
    """)

    # -----------------------------------------------------------------------
    # 7. deals
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id                  VARCHAR(36)   PRIMARY KEY,
            created_at          TIMESTAMPTZ   NOT NULL,
            updated_at          TIMESTAMPTZ   NOT NULL,
            deleted_at          TIMESTAMPTZ,
            workspace_id        VARCHAR(36)   NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            title               VARCHAR(255)  NOT NULL,
            description         TEXT,
            value               FLOAT         NOT NULL DEFAULT 0.0,
            currency            VARCHAR(10)   NOT NULL DEFAULT 'INR',
            stage               dealstage     NOT NULL DEFAULT 'new',
            priority            dealpriority  NOT NULL DEFAULT 'medium',
            probability         FLOAT         NOT NULL DEFAULT 0.0,
            expected_close_date TIMESTAMPTZ,
            owner_id            VARCHAR(36)   REFERENCES users(id) ON DELETE SET NULL,
            created_by          VARCHAR(36)   REFERENCES users(id) ON DELETE SET NULL,
            contact_id          VARCHAR(36)   REFERENCES contacts(id) ON DELETE SET NULL,
            pipeline_id         VARCHAR(36)   REFERENCES pipelines(id) ON DELETE SET NULL,
            source              VARCHAR(100),
            tags                JSONB         NOT NULL DEFAULT '[]',
            custom_fields       JSONB         NOT NULL DEFAULT '{}',
            ai_score            FLOAT,
            ai_notes            TEXT,
            won_at              TIMESTAMPTZ,
            lost_at             TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS idx_deal_workspace   ON deals (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_deal_stage       ON deals (stage);
        CREATE INDEX IF NOT EXISTS idx_deal_owner       ON deals (owner_id);
        CREATE INDEX IF NOT EXISTS idx_deal_contact     ON deals (contact_id);
        CREATE INDEX IF NOT EXISTS idx_deal_deleted_at  ON deals (deleted_at);
    """)

    # -----------------------------------------------------------------------
    # 8. deal_pipeline_map
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS deal_pipeline_map (
            id               VARCHAR(36) PRIMARY KEY,
            created_at       TIMESTAMPTZ NOT NULL,
            updated_at       TIMESTAMPTZ NOT NULL,
            deal_id          VARCHAR(36) NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            pipeline_id      VARCHAR(36) NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
            stage_id         VARCHAR(36) REFERENCES pipeline_stages(id) ON DELETE SET NULL,
            position         INTEGER     NOT NULL DEFAULT 0,
            entered_at       TIMESTAMPTZ NOT NULL,
            exited_at        TIMESTAMPTZ,
            duration_seconds FLOAT,
            CONSTRAINT uq_deal_pipeline UNIQUE (deal_id, pipeline_id)
        );
        CREATE INDEX IF NOT EXISTS idx_dpm_deal     ON deal_pipeline_map (deal_id);
        CREATE INDEX IF NOT EXISTS idx_dpm_pipeline ON deal_pipeline_map (pipeline_id);
    """)

    # -----------------------------------------------------------------------
    # 9. whatsapp_messages
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_messages (
            id            VARCHAR(36)       PRIMARY KEY,
            created_at    TIMESTAMPTZ       NOT NULL,
            updated_at    TIMESTAMPTZ       NOT NULL,
            workspace_id  VARCHAR(36)       NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            contact_id    VARCHAR(36)       REFERENCES contacts(id) ON DELETE SET NULL,
            wa_message_id VARCHAR(128)      UNIQUE,
            direction     messagedirection  NOT NULL,
            message_type  messagetype       NOT NULL DEFAULT 'text',
            status        messagestatus     NOT NULL DEFAULT 'queued',
            from_number   VARCHAR(30)       NOT NULL,
            to_number     VARCHAR(30)       NOT NULL,
            body          TEXT,
            media_url     VARCHAR(500),
            template_name VARCHAR(100),
            raw_payload   JSONB,
            sent_at       TIMESTAMPTZ,
            delivered_at  TIMESTAMPTZ,
            read_at       TIMESTAMPTZ,
            failed_reason VARCHAR(255)
        );
        CREATE INDEX IF NOT EXISTS idx_wa_workspace ON whatsapp_messages (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_wa_contact   ON whatsapp_messages (contact_id);
        CREATE INDEX IF NOT EXISTS idx_wa_status    ON whatsapp_messages (status);
    """)

    # -----------------------------------------------------------------------
    # 10. gmail_integrations
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS gmail_integrations (
            id                     VARCHAR(36)  PRIMARY KEY,
            created_at             TIMESTAMPTZ  NOT NULL,
            updated_at             TIMESTAMPTZ  NOT NULL,
            deleted_at             TIMESTAMPTZ,
            workspace_id           VARCHAR(36)  NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            user_id                VARCHAR(36)  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            google_email           VARCHAR(255) NOT NULL,
            access_token_enc       TEXT         NOT NULL,
            refresh_token_enc      TEXT,
            token_expiry           TIMESTAMPTZ,
            is_active              BOOLEAN      NOT NULL DEFAULT TRUE,
            last_sync_at           TIMESTAMPTZ,
            synced_messages_count  INTEGER      NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_gmail_workspace ON gmail_integrations (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_gmail_user      ON gmail_integrations (user_id);
    """)

    # -----------------------------------------------------------------------
    # 11. email_messages
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS email_messages (
            id                   VARCHAR(36)     PRIMARY KEY,
            created_at           TIMESTAMPTZ     NOT NULL,
            updated_at           TIMESTAMPTZ     NOT NULL,
            workspace_id         VARCHAR(36)     NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            contact_id           VARCHAR(36)     REFERENCES contacts(id) ON DELETE SET NULL,
            gmail_integration_id VARCHAR(36)     REFERENCES gmail_integrations(id) ON DELETE SET NULL,
            gmail_message_id     VARCHAR(128)    UNIQUE,
            gmail_thread_id      VARCHAR(128),
            direction            emaildirection  NOT NULL,
            from_email           VARCHAR(255)    NOT NULL,
            to_email             VARCHAR(255)    NOT NULL,
            subject              VARCHAR(500),
            body_text            TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_email_workspace ON email_messages (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_email_contact   ON email_messages (contact_id);
        CREATE INDEX IF NOT EXISTS idx_email_thread    ON email_messages (gmail_thread_id);
    """)

    # -----------------------------------------------------------------------
    # 12. subscriptions
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id                       VARCHAR(36)          PRIMARY KEY,
            created_at               TIMESTAMPTZ          NOT NULL,
            updated_at               TIMESTAMPTZ          NOT NULL,
            workspace_id             VARCHAR(36)          NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            razorpay_subscription_id VARCHAR(100)         UNIQUE,
            razorpay_plan_id         VARCHAR(100),
            plan                     billingplan          NOT NULL,
            status                   subscriptionstatus   NOT NULL DEFAULT 'created',
            current_start            TIMESTAMPTZ,
            current_end              TIMESTAMPTZ,
            next_charge_at           TIMESTAMPTZ,
            charge_at                TIMESTAMPTZ,
            ended_at                 TIMESTAMPTZ,
            raw_payload              JSONB
        );
        CREATE INDEX IF NOT EXISTS idx_sub_workspace ON subscriptions (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_sub_status    ON subscriptions (status);
    """)

    # -----------------------------------------------------------------------
    # 13. payments
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id                   VARCHAR(36)    PRIMARY KEY,
            created_at           TIMESTAMPTZ    NOT NULL,
            updated_at           TIMESTAMPTZ    NOT NULL,
            workspace_id         VARCHAR(36)    NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            subscription_id      VARCHAR(36)    REFERENCES subscriptions(id) ON DELETE SET NULL,
            razorpay_payment_id  VARCHAR(100)   UNIQUE,
            razorpay_order_id    VARCHAR(100),
            amount               FLOAT          NOT NULL,
            currency             VARCHAR(10)    NOT NULL DEFAULT 'INR',
            status               paymentstatus  NOT NULL DEFAULT 'pending',
            gst_number           VARCHAR(20),
            invoice_pdf_url      VARCHAR(500),
            invoice_number       VARCHAR(50)    UNIQUE,
            paid_at              TIMESTAMPTZ,
            raw_payload          JSONB
        );
        CREATE INDEX IF NOT EXISTS idx_pay_workspace ON payments (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_pay_status    ON payments (status);
    """)

    # -----------------------------------------------------------------------
    # 14. notifications
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id                VARCHAR(36)       PRIMARY KEY,
            created_at        TIMESTAMPTZ       NOT NULL,
            updated_at        TIMESTAMPTZ       NOT NULL,
            workspace_id      VARCHAR(36)       NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            user_id           VARCHAR(36)       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            notification_type notificationtype  NOT NULL,
            title             VARCHAR(255)      NOT NULL,
            body              TEXT,
            action_url        VARCHAR(500),
            metadata          JSONB,
            read_at           TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS idx_notif_workspace ON notifications (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_notif_user      ON notifications (user_id);
        CREATE INDEX IF NOT EXISTS idx_notif_type      ON notifications (notification_type);
    """)

    # -----------------------------------------------------------------------
    # 15. activity_logs
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id           VARCHAR(36) PRIMARY KEY,
            created_at   TIMESTAMPTZ NOT NULL,
            updated_at   TIMESTAMPTZ NOT NULL,
            workspace_id VARCHAR(36) NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            user_id      VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
            entity_type  VARCHAR(50) NOT NULL,
            entity_id    VARCHAR(36),
            action       VARCHAR(50) NOT NULL,
            old_value    JSONB,
            new_value    JSONB,
            ip_address   VARCHAR(45),
            user_agent   VARCHAR(255),
            description  TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_log_workspace ON activity_logs (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_log_entity    ON activity_logs (entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_log_action    ON activity_logs (action);
    """)

    # -----------------------------------------------------------------------
    # 16. calendar_integrations
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS calendar_integrations (
            id                      VARCHAR(36)  PRIMARY KEY,
            created_at              TIMESTAMPTZ  NOT NULL,
            updated_at              TIMESTAMPTZ  NOT NULL,
            deleted_at              TIMESTAMPTZ,
            workspace_id            VARCHAR(36)  NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            user_id                 VARCHAR(36)  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            google_email            VARCHAR(255),
            encrypted_access_token  TEXT,
            encrypted_refresh_token TEXT,
            token_expiry            TIMESTAMPTZ,
            primary_calendar_id     VARCHAR(255),
            is_active               BOOLEAN      NOT NULL DEFAULT TRUE
        );
        CREATE INDEX IF NOT EXISTS idx_cal_workspace ON calendar_integrations (workspace_id);
        CREATE INDEX IF NOT EXISTS idx_cal_user      ON calendar_integrations (user_id);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS calendar_integrations CASCADE;
        DROP TABLE IF EXISTS activity_logs CASCADE;
        DROP TABLE IF EXISTS notifications CASCADE;
        DROP TABLE IF EXISTS payments CASCADE;
        DROP TABLE IF EXISTS subscriptions CASCADE;
        DROP TABLE IF EXISTS email_messages CASCADE;
        DROP TABLE IF EXISTS gmail_integrations CASCADE;
        DROP TABLE IF EXISTS whatsapp_messages CASCADE;
        DROP TABLE IF EXISTS deal_pipeline_map CASCADE;
        DROP TABLE IF EXISTS deals CASCADE;
        DROP TABLE IF EXISTS pipeline_stages CASCADE;
        DROP TABLE IF EXISTS pipelines CASCADE;
        DROP TABLE IF EXISTS contacts CASCADE;
        DROP TABLE IF EXISTS workspace_members CASCADE;
        DROP TABLE IF EXISTS workspaces CASCADE;
        DROP TABLE IF EXISTS users CASCADE;

        DROP TYPE IF EXISTS notificationtype;
        DROP TYPE IF EXISTS paymentstatus;
        DROP TYPE IF EXISTS billingplan;
        DROP TYPE IF EXISTS subscriptionstatus;
        DROP TYPE IF EXISTS emaildirection;
        DROP TYPE IF EXISTS messagestatus;
        DROP TYPE IF EXISTS messagetype;
        DROP TYPE IF EXISTS messagedirection;
        DROP TYPE IF EXISTS dealpriority;
        DROP TYPE IF EXISTS dealstage;
        DROP TYPE IF EXISTS contactsource;
        DROP TYPE IF EXISTS memberrole;
        DROP TYPE IF EXISTS workspaceplan;
        DROP TYPE IF EXISTS userrole;
    """)
