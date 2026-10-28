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



def _log_menu_structure(value: Any, path: str = "root", depth: int = 0) -> None:
    """Log nested LINQ menu keys and group labels for diagnosing menu layouts."""
    if depth > 12:
        return

    label_keys = {
        "Name", "MenuName", "MenuType", "MenuTitle", "MenuPlanName",
        "MenuMealName", "MenuPlanId", "MenuMealId", "CategoryName",
        "RecipeCategoryName", "ServingSession", "SessionName", "MealName",
        "GroupName", "Label", "Title", "Description", "RecipeName",
    }
    if isinstance(value, dict):
        # Include null/empty values and their types: LINQ may return the
        # group-name fields with unexpected types or without populated values.
        labels = {
            key: {"value": repr(item)[:100], "type": type(item).__name__}
            for key, item in value.items()
            if key in label_keys
        }
        # Log each nested object's keys, even if its labels use an unexpected name.
        _LOGGER.debug(
            "LINQ menu structure at %s: keys=%s labels=%s",
            path,
            list(value.keys())[:50],
            labels,
        )
        for key, child in value.items():
            if isinstance(child, (dict, list)):
                _log_menu_structure(child, f"{path}.{key}", depth + 1)
    elif isinstance(value, list):
        _LOGGER.debug("LINQ menu structure at %s: list length=%d", path, len(value))
        for index, child in enumerate(value[:30]):
            if isinstance(child, (dict, list)):
                _log_menu_structure(child, f"{path}[{index}]", depth + 1)

def _log_menu_group_summary(value: Any) -> None:
    """Log a concise inventory of every menu-group label found in the response."""
    groups: dict[str, dict[str, Any]] = {}

    def walk(item: Any, path: str = "root") -> None:
        if isinstance(item, dict):
            if "MenuMealName" in item or "MenuMealId" in item:
                name = item.get("MenuMealName")
                group_name = str(name).strip() if name is not None and str(name).strip() else "(blank MenuMealName)"
                groups.setdefault(group_name, {
                    "MenuMealId": item.get("MenuMealId"),
                    "MenuPlanName": item.get("MenuPlanName"),
                    "example_path": path,
                })
            for key, child in item.items():
                if isinstance(child, (dict, list)):
                    walk(child, f"{path}.{key}")
        elif isinstance(item, list):
            for index, child in enumerate(item):
                if isinstance(child, (dict, list)):
                    walk(child, f"{path}[{index}]")

    walk(value)
    _LOGGER.debug("LINQ menu group summary: %s", groups)


def parse_menu_groups(payload: dict[str, Any], meal_name: str) -> dict[str, dict[str, list[str]]]:
    """Parse LINQ items into date -> menu group -> recipe names."""
    result: dict[str, dict[str, list[str]]] = {}
    sessions = payload.get("FamilyMenuSessions", [])

    for session in sessions:
        if not isinstance(session, dict):
            continue
        session_name = _session_name(session)
        if session_name and session_name.lower() != meal_name.lower():
            continue

        for day in _iter_days(session):
            day_date = _normalize_date(day.get("Date"))
            if not day_date:
                continue
            meals = day.get("MenuMeals", [])
            if not isinstance(meals, list):
                continue

            for menu_meal in meals:
                if not isinstance(menu_meal, dict):
                    continue
                raw_name = menu_meal.get("MenuMealName")
                name = str(raw_name).strip() if raw_name is not None else ""
                normalized = name.casefold()
                if normalized == "hot n ready":
                    group = "Hot n Ready"
                elif normalized == "grab n go":
                    group = "Grab N Go"
                elif normalized == "second line":
                    group = "Second Line"
                elif normalized == "shared items":
                    group = "Shared Items"
                else:
                    # Main offerings have dynamic labels such as "Week 4 Tuesday".
                    group = "Main Menu"

                items = _collect_recipe_names(menu_meal)
                if not items:
                    continue
                day_groups = result.setdefault(day_date, {})
                existing = day_groups.setdefault(group, [])
                existing.extend(item for item in items if item and item not in existing)

    _LOGGER.debug(
        "Parsed LINQ %s grouped menu: %d days, groups found=%s",
        meal_name,
        len(result),
        sorted({group for groups in result.values() for group in groups}),
    )
    return result


def parse_menu(payload: dict[str, Any], meal_name: str) -> dict[str, list[str]]:
    """Parse LINQ FamilyMenuSessions into {YYYY-MM-DD: [menu items]}."""
    result: dict[str, list[str]] = {}
    sessions = payload.get("FamilyMenuSessions", [])
    matched_sessions = 0

    # Diagnostic output is intentionally limited to the LINQ menu's labels and
    # object keys; it does not dump the complete API payload.
    _log_menu_structure(sessions)
    _log_menu_group_summary(sessions)

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
