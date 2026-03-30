import sys
from pathlib import Path
from datetime import datetime

# =========================
# 🧠 PROJECT PATH
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# =========================
# 🔥 IMPORT CORE
# =========================
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, Organization, UserRole


# =========================
# ⚙️ CONFIG
# =========================
ORG_NAME = "Flowra Demo Org"


USERS = [
    {
        "name": "Admin User",
        "email": "admin@flowra.com",
        "password": "admin123",
        "role": UserRole.ADMIN,
        "is_superuser": True
    },
    {
        "name": "Sales User",
        "email": "sales@flowra.com",
        "password": "sales123",
        "role": UserRole.SALES
    },
    {
        "name": "Manager User",
        "email": "manager@flowra.com",
        "password": "manager123",
        "role": UserRole.MANAGER
    }
]


# =========================
# 🔍 CHECK ORG
# =========================
def get_or_create_org(db):
    org = db.query(Organization).filter(Organization.name == ORG_NAME).first()

    if org:
        print("⚠️ Organization already exists")
        return org

    org = Organization(
        name=ORG_NAME,
        plan="pro",
        is_active=True,
        created_at=datetime.utcnow()
    )

    db.add(org)
    db.commit()
    db.refresh(org)

    print(f"✅ Organization created: {org.name}")
    return org


# =========================
# 🔍 CHECK USER
# =========================
def user_exists(db, email):
    return db.query(User).filter(User.email == email).first()


# =========================
# 🚀 SEED USERS
# =========================
def seed_users():
    db = SessionLocal()

    try:
        print("🌱 Seeding users...")

        # Create org
        org = get_or_create_org(db)

        created_count = 0

        for u in USERS:
            existing = user_exists(db, u["email"])

            if existing:
                print(f"⚠️ User exists: {u['email']}")
                continue

            user = User(
                org_id=org.id,
                name=u["name"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),

                role=u.get("role", UserRole.SALES),
                is_active=True,
                is_verified=True,
                is_superuser=u.get("is_superuser", False),

                login_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(user)
            created_count += 1

        db.commit()

        print(f"✅ {created_count} users created!")

        print("\n🔐 LOGIN CREDENTIALS:")
        for u in USERS:
            print(f"{u['email']} / {u['password']}")

    except Exception as e:
        db.rollback()
        print("❌ Error seeding users:", e)

    finally:
        db.close()


# =========================
# 🚀 ENTRYPOINT
# =========================
if __name__ == "__main__":
    seed_users()