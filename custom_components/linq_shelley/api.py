from __future__ import annotations

from datetime import date, datetime
import logging
from typing import Any

import aiohttp

from .const import API_URL

_LOGGER = logging.getLogger(__name__)


class LinqError(Exception):
    pass


class LinqClient:
    def __init__(self, session: aiohttp.ClientSession, building_id: str, district_id: str) -> None:
        self._session = session
        self.building_id = building_id
        self.district_id = district_id

    async def async_get_menu(self, start: date, end: date) -> dict[str, Any]:
        params = {
            "buildingId": self.building_id,
            "districtId": self.district_id,
            "startDate": start.strftime("%-m-%-d-%Y"),
            "endDate": end.strftime("%-m-%-d-%Y"),
        }
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) "
                "Gecko/20100101 Firefox/128.0"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://linqconnect.com/",
        }
        try:
            async with self._session.get(
                API_URL,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status >= 400:
                    detail = (await response.text())[:250].replace("\n", " ")
                    raise LinqError(
                        f"LINQ returned HTTP {response.status}; response: {detail or '(empty)'}"
                    )
                try:
                    payload = await response.json(content_type=None)
                except (ValueError, aiohttp.ContentTypeError) as err:
                    detail = (await response.text())[:250]
                    raise LinqError(
                        f"LINQ returned a non-JSON response (possibly bot protection): {detail}"
                    ) from err
                if not isinstance(payload, dict) or "FamilyMenuSessions" not in payload:
                    raise LinqError(
                        "LINQ response did not contain FamilyMenuSessions; "
                        "the API response format may have changed or the request was blocked"
                    )
                return payload
        except (aiohttp.ClientError, TimeoutError) as err:
            raise LinqError(f"Could not connect to LINQ Connect: {err}") from err


def _normalize_date(value: Any) -> str | None:
    """Convert the date formats returned by LINQ to YYYY-MM-DD."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    iso_candidate = text.replace("Z", "+00:00")
    try:
        return date.fromisoformat(iso_candidate[:10]).isoformat()
    except ValueError:
        pass

    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue

    return None


def _collect_recipe_names(value: Any) -> list[str]:
    """Recursively collect recipe names from a LINQ menu object."""
    names: list[str] = []
    if isinstance(value, dict):
        if value.get("RecipeName"):
            names.append(str(value["RecipeName"]).strip())
        for child in value.values():
            names.extend(_collect_recipe_names(child))
    elif isinstance(value, list):
        for child in value:
            names.extend(_collect_recipe_names(child))
    return names


def _session_name(session: dict[str, Any]) -> str:
    """Return the most likely serving-session name from a LINQ object."""
    for key in ("ServingSession", "SessionName", "MealName", "Name"):
        value = session.get(key)
        if value:
            return str(value).strip()
    return ""


def _iter_days(value: Any):
    """Yield menu-day objects recursively, wherever LINQ nests them."""
    if isinstance(value, dict):
        if "Date" in value and any(
            key in value for key in ("MenuMeals", "RecipeCategories", "Recipes", "Meals")
        ):
            yield value
        for child in value.values():
            yield from _iter_days(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_days(child)


def parse_menu(payload: dict[str, Any], meal_name: str) -> dict[str, list[str]]:
    """Parse LINQ FamilyMenuSessions into {YYYY-MM-DD: [menu items]}."""
    result: dict[str, list[str]] = {}
    sessions = payload.get("FamilyMenuSessions", [])
    matched_sessions = 0

    for session in sessions:
        if not isinstance(session, dict):
            continue

        name = _session_name(session)
        if name and name.lower() != meal_name.lower():
            continue
        matched_sessions += 1

        for day in _iter_days(session):
            day_date = _normalize_date(day.get("Date"))
            if not day_date:
                continue

            items = _collect_recipe_names(day)
            result[day_date] = list(dict.fromkeys(item for item in items if item))

    _LOGGER.debug(
        "Parsed LINQ %s menu: %d sessions matched, %d days with menu data",
        meal_name,
        matched_sessions,
        len(result),
    )
    if not result:
        session_names = [_session_name(s) for s in sessions if isinstance(s, dict)]
        _LOGGER.debug("LINQ serving sessions returned: %s", session_names)

    return result
