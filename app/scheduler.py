import asyncio
import logging
from datetime import datetime, timedelta
from datetime import time as clock_time
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.db import SessionLocal
from app.services import process_due_questions

logger = logging.getLogger(__name__)


def run_due_once() -> int:
    """Process one batch in its own database session."""

    with SessionLocal() as db:
        return len(process_due_questions(db))


def _parse_check_times(value: str) -> list[clock_time]:
    times = []
    for item in value.split(","):
        hour, minute = (int(part) for part in item.strip().split(":", 1))
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError(f"Invalid scheduler time: {item}")
        times.append(clock_time(hour=hour, minute=minute))
    if not times:
        raise ValueError("At least one scheduler time is required")
    return sorted(set(times))


def _seconds_until_next_check(*, now: datetime, check_times: list[clock_time]) -> float:
    for check_time in check_times:
        candidate = now.replace(
            hour=check_time.hour,
            minute=check_time.minute,
            second=0,
            microsecond=0,
        )
        if candidate > now:
            return (candidate - now).total_seconds()

    tomorrow = now + timedelta(days=1)
    candidate = tomorrow.replace(
        hour=check_times[0].hour,
        minute=check_times[0].minute,
        second=0,
        microsecond=0,
    )
    return (candidate - now).total_seconds()


async def run_scheduler() -> None:
    """Check once at startup and then at the product's gentle delivery times."""

    settings = get_settings()
    check_times = _parse_check_times(settings.scheduler_check_times)
    timezone = ZoneInfo(settings.scheduler_timezone)
    while True:
        try:
            processed = await asyncio.to_thread(run_due_once)
            if processed:
                logger.info("Processed %s due DearFuture question(s)", processed)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduled verification run failed")
        delay = _seconds_until_next_check(
            now=datetime.now(timezone),
            check_times=check_times,
        )
        await asyncio.sleep(max(1, delay))
