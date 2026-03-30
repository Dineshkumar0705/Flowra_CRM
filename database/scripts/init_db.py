import sys
import os
import subprocess
import logging
from pathlib import Path

# =========================
# 🧠 ADD PROJECT ROOT PATH
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
# 🔍 DB CONNECTION CHECK
# =========================
def check_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ DB Connection failed: {e}")
        return False


# =========================
# 🏗️ CREATE TABLES (DEV ONLY)
# =========================
def create_tables():
    logger.info("⚙️ Creating tables (DEV MODE)...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables created successfully")


# =========================
# 🔄 RUN ALEMBIC MIGRATIONS
# =========================
def run_migrations():
    logger.info("🚀 Running Alembic migrations...")

    try:
        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(BASE_DIR / "database"),
            check=True
        )
        logger.info("✅ Migrations applied successfully")

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Migration failed: {e}")


# =========================
# 🌱 SEED DATA
# =========================
def run_seeds():
    logger.info("🌱 Running seed scripts...")

    seed_scripts = [
        "seed_users.py",
        "seed_pipeline.py",
        "seed_demo_data.py",
    ]

    for script in seed_scripts:
        script_path = BASE_DIR / "database" / "seeds" / script

        if script_path.exists():
            logger.info(f"➡️ Running {script}...")

            subprocess.run(
                ["python", str(script_path)],
                check=True
            )
        else:
            logger.warning(f"⚠️ Seed file not found: {script}")

    logger.info("✅ Seeding completed")


# =========================
# 🧹 RESET DATABASE (OPTIONAL)
# =========================
def reset_database():
    logger.warning("⚠️ Resetting database (DANGEROUS)...")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    logger.info("✅ Database reset complete")


# =========================
# 🚀 FULL INIT FLOW
# =========================
def init_db():
    logger.info("🚀 Starting DB Initialization...")

    if not check_db_connection():
        logger.error("❌ Cannot proceed without DB connection")
        return

    if settings.is_dev:
        create_tables()   # dev shortcut

    run_migrations()
    run_seeds()

    logger.info("🎉 Database fully initialized!")


# =========================
# 🎯 ENTRYPOINT
# =========================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Flowra DB Manager")

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database completely"
    )

    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Run only seeds"
    )

    args = parser.parse_args()

    if args.reset:
        reset_database()
        run_seeds()

    elif args.seed_only:
        run_seeds()

    else:
        init_db()