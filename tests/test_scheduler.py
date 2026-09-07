from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.scheduler import _parse_check_times, _seconds_until_next_check


def test_scheduler_uses_product_delivery_times():
    assert _parse_check_times("08:05,12:05,18:05,21:05") == [
        time(8, 5),
        time(12, 5),
        time(18, 5),
        time(21, 5),
    ]


def test_scheduler_waits_until_next_slot_in_product_timezone():
    now = datetime(2026, 9, 7, 8, 1, tzinfo=ZoneInfo("Asia/Shanghai"))

    delay = _seconds_until_next_check(
        now=now,
        check_times=_parse_check_times("08:05,12:05,18:05,21:05"),
    )

    assert delay == 4 * 60
