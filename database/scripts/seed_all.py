import sys
import subprocess
import logging
from pathlib import Path
from typing import List

# =========================
# 🧠 PROJECT PATH
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# =========================
# ⚙️ CONFIG
# =========================
SEEDS_DIR = BASE_DIR / "database" / "seeds"

# Order matters (dependencies)
DEFAULT_SEEDS = [
    "seed_users.py",
    "seed_pipeline.py",
    "seed_demo_data.py",
]

# =========================
# 🧠 LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =========================
# 🚀 RUN SINGLE SEED
# =========================
def run_seed(script_name: str):
    script_path = SEEDS_DIR / script_name

    if not script_path.exists():
        logger.warning(f"⚠️ Seed file not found: {script_name}")
        return

    logger.info(f"🌱 Running {script_name}...")

    try:
        subprocess.run(
            ["python", str(script_path)],
            check=True
        )
        logger.info(f"✅ Completed: {script_name}")

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed: {script_name} → {e}")
        raise


# =========================
# 🔄 RUN MULTIPLE SEEDS
# =========================
def run_seeds(seed_list: List[str]):
    logger.info("🚀 Starting seed process...\n")

    for seed in seed_list:
        run_seed(seed)

    logger.info("\n🎉 All seeds executed successfully!")


# =========================
# 🧪 DRY RUN (NO EXECUTION)
# =========================
def dry_run(seed_list: List[str]):
    logger.info("🧪 Dry run mode (no execution)\n")

    for seed in seed_list:
        logger.info(f"➡️ Would run: {seed}")

    logger.info("\n✅ Dry run completed")


# =========================
# 🔍 LIST AVAILABLE SEEDS
# =========================
def list_seeds():
    logger.info("📦 Available seed files:\n")

    for file in SEEDS_DIR.glob("*.py"):
        logger.info(f" - {file.name}")


# =========================
# 🔥 VALIDATE SEEDS
# =========================
def validate_seeds(seed_list: List[str]) -> bool:
    valid = True

    for seed in seed_list:
        if not (SEEDS_DIR / seed).exists():
            logger.error(f"❌ Missing seed file: {seed}")
            valid = False

    return valid


# =========================
# 🎯 ENTRYPOINT
# =========================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Flowra Seed Manager")

    parser.add_argument(
        "--only",
        nargs="+",
        help="Run only specific seeds (space separated)"
    )

    parser.add_argument(
        "--skip",
        nargs="+",
        help="Skip specific seeds"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview seeds without running"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available seeds"
    )

    args = parser.parse_args()

    if args.list:
        list_seeds()
        sys.exit(0)

    seeds_to_run = DEFAULT_SEEDS.copy()

    if args.only:
        seeds_to_run = args.only

    if args.skip:
        seeds_to_run = [s for s in seeds_to_run if s not in args.skip]

    if not validate_seeds(seeds_to_run):
        logger.error("❌ Seed validation failed")
        sys.exit(1)

    if args.dry_run:
        dry_run(seeds_to_run)
    else:
        run_seeds(seeds_to_run)