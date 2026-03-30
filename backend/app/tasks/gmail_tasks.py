"""
Celery tasks — Gmail sync.
"""

import logging

log = logging.getLogger("flowra.tasks.gmail")


def sync_all_connected_gmails():
    """
    Beat task — pull latest emails for every connected Gmail account every 15 minutes.
    """
    from app.core.database import SessionLocal
    from app.models.gmail_integration import GmailIntegration
    from app.services.gmail_service import GmailService

    db = SessionLocal()
    try:
        integrations = db.query(GmailIntegration).filter(
            GmailIntegration.is_active == True,  # noqa: E712
        ).all()

        total_synced = 0
        for integration in integrations:
            try:
                svc = GmailService(db, integration.workspace_id, integration.user_id)
                count = svc.sync_emails(max_results=50)
                total_synced += count
                log.info(
                    "gmail.sync_complete",
                    workspace_id=integration.workspace_id,
                    user_id=integration.user_id,
                    new_emails=count,
                )
            except Exception as exc:
                log.error(
                    "gmail.sync_failed",
                    workspace_id=integration.workspace_id,
                    user_id=integration.user_id,
                    error=str(exc),
                )

        log.info("gmail.sync_all_complete", total_synced=total_synced)
        return {"total_synced": total_synced}

    finally:
        db.close()


def sync_single_gmail(workspace_id: str, user_id: str, max_results: int = 100):
    """
    On-demand Celery task — sync a single Gmail account.
    Called from the /gmail/sync endpoint as a background job.
    """
    from app.core.database import SessionLocal
    from app.services.gmail_service import GmailService

    db = SessionLocal()
    try:
        svc = GmailService(db, workspace_id, user_id)
        count = svc.sync_emails(max_results=max_results)
        log.info("gmail.sync_single_complete", workspace_id=workspace_id, synced=count)
        return {"synced": count}
    finally:
        db.close()


# Register as Celery tasks if available
try:
    from app.core.background import celery_app
    if celery_app is not None:
        sync_all_connected_gmails = celery_app.task(
            name="app.tasks.gmail_tasks.sync_all_connected_gmails",
            bind=True,
            max_retries=1,
        )(sync_all_connected_gmails)

        sync_single_gmail = celery_app.task(
            name="app.tasks.gmail_tasks.sync_single_gmail",
            bind=True,
            max_retries=2,
            default_retry_delay=30,
        )(sync_single_gmail)
except ImportError:
    pass
