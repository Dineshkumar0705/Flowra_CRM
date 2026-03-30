import sys
import os
import logging
import subprocess
from pathlib import Path

# =========================
# 🧠 PROJECT PATH
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# =========================
# 🔥 IMPORT CORE
# =========================
from app.core.config import settings
from app.core.database import engine, Base


# =========================
# 🧠 LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =========================
# ⚠️ SAFETY CHECK
# =========================
def confirm_reset():
    """
    Prevent accidental DB wipe
    """

    if settings.is_prod:
        logger.error("❌ Cannot reset DB in PRODUCTION")
        sys.exit(1)

    print("\n⚠️ WARNING: This will DELETE ALL DATA\n")

    confirm = input("Type 'RESET' to continue: ")

    if confirm != "RESET":
        print("❌ Reset cancelled")
        sys.exit(0)


# =========================
# 🔥 DROP ALL TABLES
# =========================
def drop_all():
    logger.warning("🗑️ Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("✅ All tables dropped")


# =========================
# 🏗️ CREATE TABLES
# =========================
def create_all():
    logger.info("⚙️ Creating tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables created")


# =========================
# 🚀 RUN ALEMBIC MIGRATIONS
# =========================
def run_migrations():
    logger.info("🚀 Running migrations...")

    try:
        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(BASE_DIR / "database"),
            check=True
        )
        logger.info("✅ Migrations applied")

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)


# =========================
# 🌱 RUN SEEDS
# =========================
def run_seeds():
    logger.info("🌱 Seeding data...")

    seed_scripts = [
        "seed_users.py",
        "seed_pipeline.py",
        "seed_demo_data.py",
    ]

    for script in seed_scripts:
        path = BASE_DIR / "database" / "seeds" / script

        if path.exists():
            logger.info(f"➡️ Running {script}")
            subprocess.run(["python", str(path)], check=True)
        else:
            logger.warning(f"⚠️ Missing seed file: {script}")

    logger.info("✅ Seeding completed")


# =========================
# 🔄 FULL RESET FLOW
# =========================
def reset_db(use_migrations=True, seed=True):
    logger.info("🚨 Starting DB Reset Process...")

    confirm_reset()

    drop_all()

    if use_migrations:
        run_migrations()
    else:
        create_all()

    if seed:
        run_seeds()

    logger.info("🎉 Database reset completed successfully!")


# =========================
# 🎯 ENTRYPOINT
# =========================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Flowra DB Reset Tool")

    parser.add_argument(
        "--no-migrations",
        action="store_true",
        help="Skip Alembic, use create_all()"
    )

    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Skip seeding"
    )

    args = parser.parse_args()

    reset_db(
        use_migrations=not args.no_migrations,
        seed=not args.no_seed
    )