from __future__ import annotations

from datetime import date, timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LinqClient, LinqError, parse_menu

_LOGGER = logging.getLogger(__name__)


class LinqCoordinator(DataUpdateCoordinator[dict[str, list[str]]]):
    def __init__(self, hass: HomeAssistant, client: LinqClient, school_name: str, meal: str, update_interval: int) -> None:
        self.client = client
        self.school_name = school_name
        self.meal = meal
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{school_name} LINQ menu",
            update_interval=timedelta(minutes=update_interval),
        )

    async def _async_update_data(self) -> dict[str, list[str]]:
        today = date.today()
        try:
            payload = await self.client.async_get_menu(today, today + timedelta(days=13))
            return parse_menu(payload, self.meal)
        except LinqError as err:
            raise UpdateFailed(f"{self.school_name}: {err}") from err
