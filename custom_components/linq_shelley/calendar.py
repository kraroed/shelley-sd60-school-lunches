from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SCHOOLS
from .coordinator import LinqCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinators = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            LinqMenuCalendar(coordinators[school_id], school_id, school["name"])
            for school_id, school in SCHOOLS.items()
        ]
    )


class LinqMenuCalendar(CoordinatorEntity[LinqCoordinator], CalendarEntity):
    _attr_icon = "mdi:calendar-account"

    def __init__(self, coordinator: LinqCoordinator, school_id: str, school_name: str) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{school_name} {coordinator.meal} Calendar"
        self._attr_unique_id = f"{school_id}_{coordinator.meal.lower()}_calendar"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, school_id)},
            "name": school_name,
            "manufacturer": "LINQ Connect",
            "model": "School Menu",
        }

    @property
    def event(self) -> CalendarEvent | None:
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []
        data = self.coordinator.data or {}
        current = start_date.date()
        while current < end_date.date():
            key = current.isoformat()
            items = data.get(key, [])
            if items:
                events.append(
                    CalendarEvent(
                        summary=f"{self.coordinator.meal}: {items[0]}",
                        start=current,
                        end=current + timedelta(days=1),
                        description="\n".join(f"• {item}" for item in items),
                        location=self.coordinator.school_name,
                    )
                )
            current += timedelta(days=1)
        return events
