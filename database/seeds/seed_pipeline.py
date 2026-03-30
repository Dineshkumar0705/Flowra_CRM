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
from app.models.pipeline import Pipeline, PipelineStage


# =========================
# ⚙️ CONFIG
# =========================
ORG_ID = 1


# =========================
# 🎯 DEFAULT PIPELINE DATA
# =========================
PIPELINE_NAME = "Sales Pipeline"

STAGES = [
    {"name": "New", "order": 1, "probability": 10, "color": "#94A3B8"},
    {"name": "Contacted", "order": 2, "probability": 25, "color": "#3B82F6"},
    {"name": "Qualified", "order": 3, "probability": 40, "color": "#6366F1"},
    {"name": "Proposal", "order": 4, "probability": 60, "color": "#F59E0B"},
    {"name": "Negotiation", "order": 5, "probability": 80, "color": "#EF4444"},
    {"name": "Won", "order": 6, "probability": 100, "color": "#10B981", "is_won_stage": True},
    {"name": "Lost", "order": 7, "probability": 0, "color": "#6B7280", "is_lost_stage": True},
]


# =========================
# 🔍 CHECK EXISTING
# =========================
def pipeline_exists(db):
    return (
        db.query(Pipeline)
        .filter(Pipeline.org_id == ORG_ID, Pipeline.name == PIPELINE_NAME)
        .first()
    )


# =========================
# 🚀 SEED PIPELINE
# =========================
def seed_pipeline():
    db = SessionLocal()

    try:
        print("🌱 Seeding pipeline...")

        # Prevent duplicates
        existing = pipeline_exists(db)
        if existing:
            print("⚠️ Pipeline already exists. Skipping...")
            return

        # Create pipeline
        pipeline = Pipeline(
            org_id=ORG_ID,
            name=PIPELINE_NAME,
            description="Default sales pipeline",
            is_default=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)

        print(f"✅ Pipeline created: {pipeline.name}")

        # Create stages
        for stage_data in STAGES:
            stage = PipelineStage(
                pipeline_id=pipeline.id,
                name=stage_data["name"],
                order=stage_data["order"],
                probability=stage_data["probability"],
                color=stage_data["color"],
                is_won_stage=stage_data.get("is_won_stage", False),
                is_lost_stage=stage_data.get("is_lost_stage", False),
                created_at=datetime.utcnow(),
            )

            db.add(stage)

        db.commit()

        print(f"✅ {len(STAGES)} stages created!")

    except Exception as e:
        db.rollback()
        print("❌ Error seeding pipeline:", e)

    finally:
        db.close()


# =========================
# 🚀 ENTRYPOINT
# =========================
if __name__ == "__main__":
    seed_pipeline()