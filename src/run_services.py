import os
import signal
import subprocess
import sys
import threading
import time
import logging

from src.database import engine, Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("Supervisor")


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# ---------------------------------------------------------------------------
# Runtime configuration (all driven by environment variables)
# ---------------------------------------------------------------------------
RUN_API = _env_bool("RUN_API", True)
RUN_DASHBOARD = _env_bool("RUN_DASHBOARD", True)
# Scraping scheduler is OFF by default. In the public demo we serve a seeded,
# read-only database and never scrape e-commerce sites from the server.
RUN_SCHEDULER = _env_bool("RUN_SCHEDULER", False)

API_PORT = os.getenv("API_PORT", "8000")
DASHBOARD_PORT = os.getenv("DASHBOARD_PORT", "8501")
SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "21600"))  # 6h


def init_db() -> None:
    """Ensure tables exist (safe on an empty persistent volume)."""
    logger.info("Ensuring database schema exists...")
    Base.metadata.create_all(bind=engine)


def run_scheduler() -> None:
    # Imported lazily so the demo image never touches scraping code unless asked.
    from src.tracker import track_prices

    logger.info("Scheduler started. Waiting before first cycle...")
    time.sleep(60)
    while True:
        logger.info("Running scheduled tracking...")
        try:
            track_prices()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Error in scheduled tracking: {exc}")
        logger.info(f"Sleeping for {SCHEDULER_INTERVAL_SECONDS} seconds...")
        time.sleep(SCHEDULER_INTERVAL_SECONDS)


def main() -> None:
    init_db()

    processes: list[subprocess.Popen] = []

    if RUN_API:
        logger.info(f"Starting FastAPI on 0.0.0.0:{API_PORT}")
        processes.append(
            subprocess.Popen(
                ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", API_PORT]
            )
        )

    if RUN_DASHBOARD:
        logger.info(f"Starting Streamlit dashboard on 0.0.0.0:{DASHBOARD_PORT}")
        processes.append(
            subprocess.Popen(
                [
                    "streamlit",
                    "run",
                    "src/dashboard/app.py",
                    f"--server.port={DASHBOARD_PORT}",
                    "--server.address=0.0.0.0",
                ]
            )
        )

    if RUN_SCHEDULER:
        threading.Thread(target=run_scheduler, daemon=True).start()
    else:
        logger.info("Scheduler disabled (RUN_SCHEDULER=false) - serving seeded data only.")

    if not processes:
        logger.error("Nothing to run: enable RUN_API and/or RUN_DASHBOARD.")
        sys.exit(1)

    def _shutdown(*_args):
        logger.info("Stopping services...")
        for proc in processes:
            proc.terminate()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    # If any child dies, tear everything down so Docker can restart the container.
    while True:
        for proc in processes:
            code = proc.poll()
            if code is not None:
                logger.error(f"Process {proc.args} exited with code {code}. Shutting down.")
                _shutdown()
                sys.exit(code or 1)
        time.sleep(2)


if __name__ == "__main__":
    main()
