"""
Import all SQLAlchemy models here.

This file ensures every model's __tablename__ is registered on Base.metadata
before Alembic autogenerate or init_db() runs.  Always add new models to this
list.

Import order matters for FK resolution:
  1. User (no FKs into other Flowra models)
  2. Workspace / WorkspaceMember (FK to User)
  3. Contact  (FK to Workspace, User)
  4. Pipeline (FK to Workspace)
  5. Deal     (FK to Workspace, Contact, Pipeline, User)
  6. Integrations (FK to Workspace, Contact, User)
  7. Billing  (FK to Workspace)
  8. Notifications (FK to Workspace, User)
"""

from app.models.user import User, UserRole  # noqa: F401
from app.models.workspace import Workspace, WorkspaceMember, WorkspacePlan, MemberRole  # noqa: F401
from app.models.contact import Contact, ContactSource, LeadStatus  # noqa: F401
from app.models.pipeline import Pipeline, PipelineStage, DealPipelineMap  # noqa: F401
from app.models.deal import Deal, DealStage, DealPriority  # noqa: F401
from app.models.whatsapp_message import WhatsAppMessage, MessageDirection, MessageType, MessageStatus  # noqa: F401
from app.models.gmail_integration import GmailIntegration, EmailMessage, EmailDirection  # noqa: F401
from app.models.billing import Subscription, Payment, SubscriptionStatus, PaymentStatus, BillingPlan  # noqa: F401
from app.models.notification import Notification, ActivityLog, NotificationType  # noqa: F401
from app.models.calendar_integration import CalendarIntegration  # noqa: F401
from app.models.task import Task, TaskStatus, TaskPriority  # noqa: F401

__all__ = [
    "User", "UserRole",
    "Workspace", "WorkspaceMember", "WorkspacePlan", "MemberRole",
    "Contact", "ContactSource",
    "Pipeline", "PipelineStage", "DealPipelineMap",
    "Deal", "DealStage", "DealPriority",
    "WhatsAppMessage", "MessageDirection", "MessageType", "MessageStatus",
    "GmailIntegration", "EmailMessage", "EmailDirection",
    "Subscription", "Payment", "SubscriptionStatus", "PaymentStatus", "BillingPlan",
    "Notification", "ActivityLog", "NotificationType",
    "CalendarIntegration",
    "Task", "TaskStatus", "TaskPriority",
]
