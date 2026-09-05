import asyncio
import logging
import time

from app.config import get_settings
from app.db import SessionLocal
from app.services import process_due_questions

logger = logging.getLogger(__name__)


def run_due_once() -> int:
    """Process one batch in its own database session."""

    with SessionLocal() as db:
        return len(process_due_questions(db))


async def run_scheduler() -> None:
    """Check once at startup and then on aligned interval boundaries."""

    interval = max(1, get_settings().scheduler_interval_seconds)
    while True:
        try:
            processed = await asyncio.to_thread(run_due_once)
            if processed:
                logger.info("Processed %s due DearFuture question(s)", processed)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduled verification run failed")
        await asyncio.sleep(interval - time.time() % interval)
