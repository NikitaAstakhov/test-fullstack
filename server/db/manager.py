import os
import asyncio
import logging
import subprocess
import traceback

from typing import Optional
from .seed import SubmissionSeeder

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def run_alembic_migrations(
    alembic_ini_path: Optional[str] = None,
) -> None:
    def do_upgrade():
        cwd = os.getcwd()
        ini_file = alembic_ini_path or "alembic.ini"
        ini_path = ini_file if os.path.isabs(ini_file) else os.path.join(cwd, ini_file)

        logger.info(f"Using alembic.ini at: {ini_path}")
        if not os.path.exists(ini_path):
            logger.error(f"alembic.ini not found at {ini_path}, skipping migrations")
            return

        env = os.environ.copy()
        env["ALEMBIC_CONFIG"] = ini_path

        db_url = os.getenv("DATABASE_URL")
        if db_url:
            env["DATABASE_URL"] = db_url
            logger.info(f"Environment DATABASE_URL={db_url}")

        logger.info("Starting Alembic migrations (upgrade head) via subprocess...")

        proc = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
        )

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        if stdout:
            logger.info(f"Alembic stdout:\n{stdout}")
        if stderr:
            logger.error(f"Alembic stderr:\n{stderr}")

        if proc.returncode != 0:
            raise RuntimeError(f"Alembic exited with code {proc.returncode}")

        logger.info("Alembic migrations complete.")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, do_upgrade)


async def run_seed_if_needed(
    database_url: str,
    *,
    target_count: int = 2_000_000,
    batch_size: int = 1_000,
    threshold: int = 100_000,
    max_workers: Optional[int] = None,
) -> None:
    seeder = SubmissionSeeder(
        database_url=database_url,
        target_count=target_count,
        batch_size=batch_size,
        threshold=threshold,
        max_workers=max_workers,
    )
    logger.info("Invoking async seeder...")
    try:
        await seeder.run()
    except Exception:
        logger.error("Seeder run failed. Traceback:")
        tb = traceback.format_exc()
        logger.error(tb)
        raise
    logger.info("Seeder finished.")
