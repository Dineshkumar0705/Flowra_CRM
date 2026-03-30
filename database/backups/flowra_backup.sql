import os
import subprocess
from datetime import datetime
from pathlib import Path

from app.core.config import settings


# =========================
# ⚙️ CONFIG
# =========================
BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

DB_URL = settings.database_url


# =========================
# 🔍 PARSE DATABASE URL
# =========================
def parse_db_url(db_url: str):
    """
    Extract DB credentials from URL
    """
    # Example:
    # postgresql://user:password@localhost:5432/dbname

    from urllib.parse import urlparse

    parsed = urlparse(db_url)

    return {
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "dbname": parsed.path.lstrip("/")
    }


# =========================
# 💾 BACKUP FUNCTION
# =========================
def backup_database():
    creds = parse_db_url(DB_URL)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"flowra_backup_{timestamp}.sql"
    filepath = BACKUP_DIR / filename

    print(f"📦 Creating backup: {filename}")

    env = os.environ.copy()
    env["PGPASSWORD"] = creds["password"]

    command = [
        "pg_dump",
        "-h", creds["host"],
        "-p", str(creds["port"]),
        "-U", creds["user"],
        "-d", creds["dbname"],
        "-F", "c",  # compressed format
        "-f", str(filepath)
    ]

    try:
        subprocess.run(command, check=True, env=env)
        print(f"✅ Backup successful: {filepath}")

    except subprocess.CalledProcessError as e:
        print("❌ Backup failed:", e)


# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    backup_database()