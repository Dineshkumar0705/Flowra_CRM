"""
Celery tasks — automation and stale deal scanning.
"""

import logging

log = logging.getLogger("flowra.tasks.automation")


def _get_celery():
    from app.core.background import celery_app
    return celery_app


def scan_all_workspaces_stale_deals():
    """
    Beat task — scan every active workspace for stale deals every 3 hours.
    Fired by Celery Beat on the schedule defined in app.core.background.
    """
    from app.core.database import SessionLocal
    from app.models.workspace import Workspace
    from app.services.automation_service import AutomationService

    db = SessionLocal()
    try:
        workspaces = db.query(Workspace).filter(
            Workspace.deleted_at.is_(None)
        ).all()

        total_flagged = 0
        for ws in workspaces:
            try:
                svc = AutomationService(db, ws.id)
                flagged = svc.check_stale_deals()
                total_flagged += len(flagged)
                if flagged:
                    log.info(
                        "automation.stale_deals_flagged",
                        workspace_id=ws.id,
                        count=len(flagged),
                    )
            except Exception as exc:
                log.error(
                    "automation.stale_scan_failed",
                    workspace_id=ws.id,
                    error=str(exc),
                )

        log.info("automation.stale_scan_complete", total_flagged=total_flagged)
        return {"total_flagged": total_flagged}

    finally:
        db.close()


# Register as Celery task if available
try:
    from app.core.background import celery_app
    if celery_app is not None:
        scan_all_workspaces_stale_deals = celery_app.task(
            name="app.tasks.automation_tasks.scan_all_workspaces_stale_deals",
            bind=True,
            max_retries=2,
            default_retry_delay=60,
        )(scan_all_workspaces_stale_deals)
except ImportError:
    pass
