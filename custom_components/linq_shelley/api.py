from __future__ import annotations
from datetime import date, timedelta
from typing import Any
import aiohttp

from .const import API_URL

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
        # LINQ Connect's public API may reject requests that do not resemble a
        # normal browser request. Use a browser-like User-Agent, as used by
        # other working LINQ Connect clients.
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


def _recipe_names(category: dict[str, Any]) -> list[str]:
    return [str(r.get("RecipeName", "")).strip() for r in category.get("Recipes", []) if r.get("RecipeName")]


def parse_menu(payload: dict[str, Any], meal_name: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for session in payload.get("FamilyMenuSessions", []):
        if str(session.get("ServingSession", "")).lower() != meal_name.lower():
            continue
        for plan in session.get("MenuPlans", []):
            for day in plan.get("Days", []):
                day_date = str(day.get("Date", ""))[:10]
                if not day_date:
                    continue
                items: list[str] = []
                for meal in day.get("MenuMeals", []):
                    for category in meal.get("RecipeCategories", []):
                        items.extend(_recipe_names(category))
                # Preserve API order while removing duplicates.
                result[day_date] = list(dict.fromkeys(items))
    return result
