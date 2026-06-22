"""Bootstraps the first admin user. There is no public signup endpoint by
design — admin accounts must be seeded via this script, run directly against
the database (`python scripts/create_admin.py <username>`)."""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.services.auth_service import hash_password  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/create_admin.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)

    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first() is not None:
            print(f"User '{username}' already exists.")
            sys.exit(1)

        user = User(username=username, hashed_password=hash_password(password), role=UserRole.ADMIN)
        db.add(user)
        db.commit()
        print(f"Created admin user '{username}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
