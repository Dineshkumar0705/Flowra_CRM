"""User repository."""

import logging
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.user import User

log = logging.getLogger("flowra.repo.user")


class UserRepository:
    """CRUD for the User table."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _active_q(self):
        return self.db.query(User).filter(
            User.deleted_at.is_(None),
            User.is_active == True,
        )

    def create(self, data: dict) -> User:
        user = User(**data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.email == email.lower(), User.deleted_at.is_(None))
            .first()
        )

    def email_exists(self, email: str) -> bool:
        return self.db.query(User.id).filter(User.email == email.lower()).first() is not None

    def update(self, user: User, data: dict) -> User:
        from datetime import datetime, timezone
        for k, v in data.items():
            if hasattr(user, k):
                setattr(user, k, v)
        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete(self, user: User) -> None:
        user.soft_delete()
        self.db.commit()

    def list(self, skip: int = 0, limit: int = 20) -> Tuple[List[User], int]:
        q = self._active_q()
        total = q.count()
        items = q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        return items, total
