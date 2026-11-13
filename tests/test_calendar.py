from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest

from custom_components.linq_shelley.calendar import LinqMenuCalendar


@pytest.mark.asyncio
async def test_calendar_returns_all_day_events_only_for_days_with_menu():
    calendar = object.__new__(LinqMenuCalendar)
    calendar._coordinator = SimpleNamespace(
        data={
            "2026-10-26": ["Pizza", "Fruit"],
            "2026-10-28": [],
            "2026-10-29": ["Pasta"],
        },
        school_name="Shelley High School",
        meal="Lunch",
    )

    events = await calendar.async_get_events(
        None,
        datetime(2026, 10, 26),
        datetime(2026, 10, 30),
    )

    assert len(events) == 2
    assert events[0].summary == "Lunch: Pizza"
    assert events[0].start.isoformat() == "2026-10-26"
    assert events[0].end.isoformat() == "2026-10-27"
    assert events[0].description == "• Pizza\n• Fruit"
    assert events[0].location == "Shelley High School"
    assert events[1].summary == "Lunch: Pasta"


@pytest.mark.asyncio
async def test_calendar_respects_exclusive_end_date():
    calendar = object.__new__(LinqMenuCalendar)
    calendar._coordinator = SimpleNamespace(
        data={"2026-10-26": ["Pizza"], "2026-10-27": ["Tacos"]},
        school_name="Hobbs Middle School",
        meal="Lunch",
    )

    events = await calendar.async_get_events(
        None,
        datetime(2026, 10, 26),
        datetime(2026, 10, 27),
    )

    assert [event.summary for event in events] == ["Lunch: Pizza"]
