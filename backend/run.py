import uvicorn
import multiprocessing
import logging

from app.core.config import settings


# =========================
# 🧠 LOGGER
# =========================
logger = logging.getLogger("flowra.run")


# =========================
# ⚙️ CONFIG BUILDER
# =========================
def get_uvicorn_config():
    """
    Build dynamic config based on environment
    """

    is_dev = settings.is_dev

    return {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": 8000,

        # Dev vs Prod behavior
        "reload": is_dev,
        "log_level": "debug" if is_dev else "info",

        # Production scaling
        "workers": 1 if is_dev else multiprocessing.cpu_count(),

        # Performance
        "loop": "auto",
        "http": "auto",

        # Headers / proxy support
        "proxy_headers": True,
        "forwarded_allow_ips": "*",
    }


# =========================
# 🚀 RUN SERVER
# =========================
def start():
    config = get_uvicorn_config()

    logger.info("🚀 Starting Flowra Server...")
    logger.info(f"🌍 ENV: {settings.ENV}")
    logger.info(f"⚡ Workers: {config['workers']}")
    logger.info(f"🔁 Reload: {config['reload']}")

    uvicorn.run(**config)


# =========================
# 🛡️ ENTRY POINT
# =========================
if __name__ == "__main__":
    try:
        start()

    except Exception as e:
        logger.exception(f"❌ Failed to start server: {e}")