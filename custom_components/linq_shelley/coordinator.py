from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import LinqClient, LinqError, parse_menu, parse_menu_groups

_LOGGER = logging.getLogger(__name__)


class LinqCoordinator(DataUpdateCoordinator[dict[str, list[str]]]):
    def __init__(self, hass: HomeAssistant, client: LinqClient, school_name: str, meal: str, update_interval: int) -> None:
        self.client = client
        self.school_name = school_name
        self.meal = meal
        self.menu_groups: dict[str, dict[str, list[str]]] = {}
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{school_name} LINQ menu",
            update_interval=timedelta(minutes=update_interval),
        )

    async def _async_update_data(self) -> dict[str, list[str]]:
        # Use Home Assistant's configured timezone rather than the host OS date.
        today = dt_util.now().date()
        try:
            payload = await self.client.async_get_menu(today, today + timedelta(days=13))
            self.menu_groups = parse_menu_groups(payload, self.meal)
            return parse_menu(payload, self.meal)
        except LinqError as err:
            raise UpdateFailed(f"{self.school_name}: {err}") from err
