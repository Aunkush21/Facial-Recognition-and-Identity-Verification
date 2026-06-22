import uuid

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.services.auth_service import hash_password


class UserError(Exception):
    pass


def create_user(db: Session, username: str, password: str, role: UserRole, label: str | None = None) -> User:
    existing = db.query(User).filter(User.username == username).first()
    if existing is not None:
        raise UserError(f"A user named '{username}' already exists.")
    user = User(
        username=username,
        label=(label.strip() or None) if label else None,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.role, User.username).all()


def set_user_active(db: Session, user_id: uuid.UUID, is_active: bool) -> User | None:
    user = db.get(User, user_id)
    if user is None:
        return None
    user.is_active = is_active
    db.flush()
    return user


def set_user_password(db: Session, user_id: uuid.UUID, password: str) -> User | None:
    user = db.get(User, user_id)
    if user is None:
        return None
    user.hashed_password = hash_password(password)
    db.flush()
    return user
