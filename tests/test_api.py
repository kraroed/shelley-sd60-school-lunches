from __future__ import annotations

from datetime import date

import aiohttp
import pytest

from custom_components.linq_shelley.api import (
    LinqClient,
    LinqError,
    _normalize_date,
    parse_menu,
    parse_menu_groups,
)
from custom_components.linq_shelley.const import DISTRICT_ID, SCHOOLS


def _payload():
    return {
        "FamilyMenuSessions": [
            {
                "ServingSession": "Lunch",
                "MenuPlans": [
                    {
                        "Days": [
                            {
                                "Date": "2026-10-26T00:00:00",
                                "MenuMeals": [
                                    {
                                        "MenuMealName": "Week 4 Monday",
                                        "RecipeCategories": [
                                            {"Recipes": [{"RecipeName": "Pizza"}, {"RecipeName": "Fruit"}]}
                                        ],
                                    },
                                    {
                                        "MenuMealName": "Hot n Ready",
                                        "Recipes": [{"RecipeName": "Chicken Sandwich"}],
                                    },
                                ],
                            }
                        ]
                    }
                ],
            },
            {
                "ServingSession": "Breakfast",
                "MenuPlans": [
                    {
                        "Days": [
                            {
                                "Date": "10/26/2026",
                                "MenuMeals": [{"Recipes": [{"RecipeName": "Pancakes"}]}],
                            }
                        ]
                    }
                ],
            },
        ]
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-10-26", "2026-10-26"),
        ("2026-10-26T00:00:00", "2026-10-26"),
        ("2026-10-26T00:00:00Z", "2026-10-26"),
        ("10/26/2026", "2026-10-26"),
        ("10-26-2026", "2026-10-26"),
        ("10/26/26", "2026-10-26"),
        ("10-26-26", "2026-10-26"),
        ("", None),
        (None, None),
        ("not-a-date", None),
    ],
)
def test_normalize_date(value, expected):
    assert _normalize_date(value) == expected


def test_parse_menu_filters_meal_and_deduplicates_items():
    payload = _payload()
    payload["FamilyMenuSessions"][0]["MenuPlans"][0]["Days"][0]["MenuMeals"][0][
        "RecipeCategories"
    ][0]["Recipes"].append({"RecipeName": "Pizza"})

    assert parse_menu(payload, "Lunch") == {
        "2026-10-26": ["Pizza", "Fruit", "Chicken Sandwich"]
    }
    assert parse_menu(payload, "Breakfast") == {"2026-10-26": ["Pancakes"]}


def test_parse_menu_groups_preserves_known_lunch_groups():
    payload = _payload()
    groups = parse_menu_groups(payload, "Lunch")

    assert groups == {
        "2026-10-26": {
            "Main Menu": ["Pizza", "Fruit"],
            "Hot n Ready": ["Chicken Sandwich"],
        }
    }


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("2nd Line", "Second Line"),
        ("Second Line", "Second Line"),
        ("Grab N Go", "Grab N Go"),
        ("Shared Items", "Shared Items"),
        ("Hot n Ready", "Hot n Ready"),
        ("Week 4 Tuesday", "Main Menu"),
    ],
)
def test_menu_group_label_normalization(label, expected):
    payload = {
        "FamilyMenuSessions": [
            {
                "ServingSession": "Lunch",
                "Days": [
                    {
                        "Date": "2026-10-27",
                        "MenuMeals": [
                            {"MenuMealName": label, "Recipes": [{"RecipeName": "Test Item"}]}
                        ],
                    }
                ],
            }
        ]
    }
    assert parse_menu_groups(payload, "Lunch")["2026-10-27"][expected] == ["Test Item"]


def test_parser_handles_empty_or_malformed_session_entries():
    assert parse_menu({"FamilyMenuSessions": []}, "Lunch") == {}
    assert parse_menu({"FamilyMenuSessions": [None, "invalid"]}, "Lunch") == {}
    assert parse_menu_groups({"FamilyMenuSessions": [None, "invalid"]}, "Lunch") == {}


def test_shelley_school_ids():
    assert DISTRICT_ID == "bff2ebbd-7278-eb11-a2d4-c8076e69fc1e"
    assert len(SCHOOLS) == 6
    assert SCHOOLS["dean_goodsell"]["building_id"] == "cf7f6761-6af8-ec11-a7e3-a802b1d81c75"
    assert SCHOOLS["hobbs_middle"]["building_id"] == "59119a65-dd8b-eb11-a2c4-8a946a189914"
    assert SCHOOLS["riverview"]["building_id"] == "4fd03c34-6f86-eb11-a2c9-ed88345e6dd3"
    assert SCHOOLS["shelley_high"]["building_id"] == "fbdc8282-dd8b-eb11-a2c4-e7b369209732"
    assert SCHOOLS["stuart"]["building_id"] == "5db532bd-6f86-eb11-a2c9-c96fa6243553"
    assert SCHOOLS["sunrise"]["building_id"] == "59fa9ca6-6d86-eb11-a2ca-c30c3b3a6812"


class _FakeResponse:
    def __init__(self, status=200, payload=None, text=""):
        self.status = status
        self.payload = payload
        self.body = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def text(self):
        return self.body

    async def json(self, content_type=None):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class _FakeSession:
    def __init__(self, response):
        self.response = response
        self.request = None

    def get(self, url, **kwargs):
        self.request = (url, kwargs)
        return self.response


@pytest.mark.asyncio
async def test_client_requests_expected_building_and_date_range():
    session = _FakeSession(_FakeResponse(payload={"FamilyMenuSessions": []}))
    client = LinqClient(session, "building-123", DISTRICT_ID)

    result = await client.async_get_menu(date(2026, 10, 2), date(2026, 10, 15))

    assert result == {"FamilyMenuSessions": []}
    url, kwargs = session.request
    assert url.endswith("/api/FamilyMenu")
    assert kwargs["params"] == {
        "buildingId": "building-123",
        "districtId": DISTRICT_ID,
        "startDate": "10-2-2026",
        "endDate": "10-15-2026",
    }
    assert kwargs["timeout"].total == 20
    assert kwargs["headers"]["Referer"] == "https://linqconnect.com/"


@pytest.mark.asyncio
async def test_client_reports_http_errors():
    client = LinqClient(_FakeSession(_FakeResponse(status=403, text="blocked")), "b", "d")
    with pytest.raises(LinqError, match="HTTP 403.*blocked"):
        await client.async_get_menu(date(2026, 1, 1), date(2026, 1, 14))


@pytest.mark.asyncio
async def test_client_reports_non_json_response():
    client = LinqClient(
        _FakeSession(_FakeResponse(payload=ValueError("invalid json"), text="<html>blocked</html>")),
        "b",
        "d",
    )
    with pytest.raises(LinqError, match="non-JSON response"):
        await client.async_get_menu(date(2026, 1, 1), date(2026, 1, 14))


@pytest.mark.asyncio
async def test_client_rejects_unexpected_response_shape():
    client = LinqClient(_FakeSession(_FakeResponse(payload={"unexpected": []})), "b", "d")
    with pytest.raises(LinqError, match="FamilyMenuSessions"):
        await client.async_get_menu(date(2026, 1, 1), date(2026, 1, 14))


@pytest.mark.asyncio
async def test_client_rejects_non_list_sessions():
    client = LinqClient(
        _FakeSession(_FakeResponse(payload={"FamilyMenuSessions": {}})), "b", "d"
    )
    with pytest.raises(LinqError, match="must be a list"):
        await client.async_get_menu(date(2026, 1, 1), date(2026, 1, 14))


@pytest.mark.asyncio
async def test_client_wraps_connection_errors():
    class BrokenSession:
        def get(self, *_args, **_kwargs):
            raise aiohttp.ClientConnectionError("offline")

    client = LinqClient(BrokenSession(), "b", "d")
    with pytest.raises(LinqError, match="Could not connect"):
        await client.async_get_menu(date(2026, 1, 1), date(2026, 1, 14))
