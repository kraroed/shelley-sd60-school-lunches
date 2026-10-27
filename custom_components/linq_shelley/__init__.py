from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LinqClient
from .const import DOMAIN, DISTRICT_ID, MEAL_LUNCH, CONF_MEAL, SCHOOLS
from .coordinator import LinqCoordinator

PLATFORMS = ["sensor", "calendar"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    meal = entry.data.get(CONF_MEAL, MEAL_LUNCH)
    interval = entry.data.get(CONF_SCAN_INTERVAL, 60)

    coordinators = {}
    for school_id, school in SCHOOLS.items():
        client = LinqClient(session, school["building_id"], DISTRICT_ID)
        coordinators[school_id] = LinqCoordinator(
            hass,
            client,
            school["name"],
            meal,
            interval,
        )

    # Refresh all schools concurrently. If one school is temporarily unavailable,
    # keep the other schools available rather than failing the entire integration.
    results = await asyncio.gather(
        *(coordinator.async_config_entry_first_refresh() for coordinator in coordinators.values()),
        return_exceptions=True,
    )
    for school_id, result in zip(coordinators, results):
        if isinstance(result, Exception):
            coordinators[school_id].last_update_success = False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinators
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
