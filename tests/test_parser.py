from custom_components.linq_shelley.api import parse_menu
from custom_components.linq_shelley.const import DISTRICT_ID, SCHOOLS


def test_parse_menu():
    payload = {
        "FamilyMenuSessions": [{
            "ServingSession": "Lunch",
            "MenuPlans": [{
                "Days": [{
                    "Date": "2026-10-26T00:00:00",
                    "MenuMeals": [{
                        "RecipeCategories": [{
                            "Recipes": [{"RecipeName": "Pizza"}, {"RecipeName": "Pizza"}, {"RecipeName": "Fruit"}]
                        }]
                    }]
                }]
            }]
        }]
    }
    assert parse_menu(payload, "Lunch") == {"2026-10-26": ["Pizza", "Fruit"]}


def test_shelley_school_ids():
    assert DISTRICT_ID == "bff2ebbd-7278-eb11-a2d4-c8076e69fc1e"
    assert len(SCHOOLS) == 6
    assert SCHOOLS["dean_goodsell"]["building_id"] == "cf7f6761-6af8-ec11-a7e3-a802b1d81c75"
    assert SCHOOLS["hobbs_middle"]["building_id"] == "59119a65-dd8b-eb11-a2c4-8a946a189914"
    assert SCHOOLS["riverview"]["building_id"] == "4fd03c34-6f86-eb11-a2c9-ed88345e6dd3"
    assert SCHOOLS["shelley_high"]["building_id"] == "fbdc8282-dd8b-eb11-a2c4-e7b369209732"
    assert SCHOOLS["stuart"]["building_id"] == "5db532bd-6f86-eb11-a2c9-c96fa6243553"
    assert SCHOOLS["sunrise"]["building_id"] == "59fa9ca6-6d86-eb11-a2ca-c30c3b3a6812"
