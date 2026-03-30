import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# =========================
# 🧠 PROJECT PATH
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# =========================
# 🔥 IMPORT CORE
# =========================
from app.core.database import SessionLocal
from app.models.deal import Deal, DealStage, DealPriority
from app.models.user import User


# =========================
# 🧠 CONFIG
# =========================
ORG_ID = 1
DEMO_DEAL_COUNT = 25


# =========================
# 🎯 SAMPLE DATA
# =========================
TITLES = [
    "Website Development",
    "Mobile App Project",
    "CRM Implementation",
    "AI Chatbot Integration",
    "E-commerce Platform",
    "Marketing Automation Setup",
    "SaaS Dashboard Build",
]

SOURCES = ["website", "ads", "referral", "linkedin", "cold_email"]

TAGS = [["hot"], ["enterprise"], ["startup"], ["priority"], ["upsell"]]


# =========================
# 🎲 RANDOM HELPERS
# =========================
def random_value():
    return random.randint(5000, 200000)


def random_stage():
    return random.choice(list(DealStage))


def random_priority():
    return random.choice(list(DealPriority))


def random_probability(stage):
    mapping = {
        DealStage.NEW: 10,
        DealStage.CONTACTED: 25,
        DealStage.QUALIFIED: 40,
        DealStage.PROPOSAL: 60,
        DealStage.NEGOTIATION: 80,
        DealStage.WON: 100,
        DealStage.LOST: 0,
    }
    return mapping.get(stage, 20)


# =========================
# 🔍 CHECK EXISTING DATA
# =========================
def already_seeded(db):
    existing = db.query(Deal).filter(Deal.org_id == ORG_ID).first()
    return existing is not None


# =========================
# 🚀 SEED FUNCTION
# =========================
def seed_demo_data():
    db = SessionLocal()

    try:
        print("🌱 Seeding demo deals...")

        # Prevent duplicate seed
        if already_seeded(db):
            print("⚠️ Demo data already exists. Skipping...")
            return

        # Get users
        users = db.query(User).filter(User.org_id == ORG_ID).all()

        if not users:
            print("❌ No users found. Run seed_users first.")
            return

        for _ in range(DEMO_DEAL_COUNT):
            stage = random_stage()

            deal = Deal(
                org_id=ORG_ID,
                title=random.choice(TITLES),
                description="Demo deal for testing Flowra CRM",

                value=random_value(),
                currency="INR",

                stage=stage,
                priority=random_priority(),

                probability=random_probability(stage),

                owner_id=random.choice(users).id,
                source=random.choice(SOURCES),

                tags=random.choice(TAGS),
                custom_fields={"demo": True},

                ai_score=random.randint(20, 95),
                ai_notes="AI generated insights placeholder",

                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                updated_at=datetime.utcnow()
            )

            db.add(deal)

        db.commit()

        print(f"✅ {DEMO_DEAL_COUNT} demo deals created!")

    except Exception as e:
        db.rollback()
        print("❌ Error seeding demo data:", e)

    finally:
        db.close()


# =========================
# 🚀 ENTRYPOINT
# =========================
if __name__ == "__main__":
    seed_demo_data()