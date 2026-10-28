from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SCHOOLS
from .coordinator import LinqCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinators = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for school_id, school in SCHOOLS.items():
        coordinator = coordinators[school_id]
        entities.extend([
            LinqTodaySensor(coordinator, school_id, school["name"], 0),
            LinqTomorrowSensor(coordinator, school_id, school["name"], 1),
            LinqMenuSensor(coordinator, school_id, school["name"]),
            LinqNext14Sensor(coordinator, school_id, school["name"]),
        ])
        if coordinator.meal.lower() == "lunch":
            if school_id == "shelley_high":
                groups = ("Main Menu", "Hot n Ready", "Grab N Go", "Shared Items")
            elif school_id == "hobbs_middle":
                groups = ("Main Menu", "Second Line", "Shared Items")
            else:
                groups = ()
            entities.extend(
                LinqMenuGroupSensor(coordinator, school_id, school["name"], group)
                for group in groups
            )
    async_add_entities(entities)


class BaseLinqSensor(CoordinatorEntity[LinqCoordinator], SensorEntity):
    _attr_icon = "mdi:food"

    def __init__(self, coordinator: LinqCoordinator, school_id: str, school_name: str) -> None:
        super().__init__(coordinator)
        self.school_id = school_id
        self.school_name = school_name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, school_id)},
            "name": school_name,
            "manufacturer": "LINQ Connect",
            "model": "School Menu",
        }

    @property
    def extra_state_attributes(self):
        return {
            "school": self.school_name,
            "meal": self.coordinator.meal,
            "building_id": self.coordinator.client.building_id,
            "district_id": self.coordinator.client.district_id,
            "menu_url": f"https://linqconnect.com/public/menu/8MJ46S?buildingId={self.coordinator.client.building_id}",
        }

    def _items(self, offset: int = 0) -> list[str]:
        key = (dt_util.now().date() + timedelta(days=offset)).isoformat()
        return (self.coordinator.data or {}).get(key, [])


class LinqTodaySensor(BaseLinqSensor):
    def __init__(self, coordinator, school_id, school_name, offset):
        super().__init__(coordinator, school_id, school_name)
        self._attr_name = f"{school_name} {coordinator.meal} Today"
        self._attr_unique_id = f"{school_id}_{coordinator.meal.lower()}_today"
        self._offset = offset

    @property
    def native_value(self):
        items = self._items(self._offset)
        # Home Assistant states are limited to 255 characters. Keep the full
        # menu in attributes and expose a short, reliable state value instead.
        return f"{len(items)} items" if items else "No menu"

    @property
    def extra_state_attributes(self):
        a = super().extra_state_attributes
        a.update({"date": dt_util.now().date().isoformat(), "menu": self._items()})
        return a


class LinqTomorrowSensor(BaseLinqSensor):
    def __init__(self, coordinator, school_id, school_name, offset):
        super().__init__(coordinator, school_id, school_name)
        self._attr_name = f"{school_name} {coordinator.meal} Tomorrow"
        self._attr_unique_id = f"{school_id}_{coordinator.meal.lower()}_tomorrow"
        self._offset = offset

    @property
    def native_value(self):
        items = self._items(self._offset)
        return f"{len(items)} items" if items else "No menu"

    @property
    def extra_state_attributes(self):
        a = super().extra_state_attributes
        key = (dt_util.now().date() + timedelta(days=1)).isoformat()
        a.update({"date": key, "menu": self._items(1)})
        return a


class LinqMenuSensor(BaseLinqSensor):
    def __init__(self, coordinator, school_id, school_name):
        super().__init__(coordinator, school_id, school_name)
        self._attr_name = f"{school_name} {coordinator.meal} Menu"
        self._attr_unique_id = f"{school_id}_{coordinator.meal.lower()}_menu"

    @property
    def native_value(self):
        return f"{len(self.coordinator.data or {})} days"

    @property
    def extra_state_attributes(self):
        a = super().extra_state_attributes
        a["menu"] = self.coordinator.data or {}
        return a


class LinqNext14Sensor(BaseLinqSensor):
    def __init__(self, coordinator, school_id, school_name):
        super().__init__(coordinator, school_id, school_name)
        self._attr_name = f"{school_name} {coordinator.meal} 14 Day Menu"
        self._attr_unique_id = f"{school_id}_{coordinator.meal.lower()}_14_day_menu"
        self._attr_icon = "mdi:calendar-week"

    @property
    def native_value(self):
        return f"{len(self.coordinator.data or {})} days"

    @property
    def extra_state_attributes(self):
        a = super().extra_state_attributes
        a["menu"] = self.coordinator.data or {}
        return a


class LinqMenuGroupSensor(BaseLinqSensor):
    """Expose one school's lunch menu group."""

    def __init__(self, coordinator, school_id, school_name, group_name):
        super().__init__(coordinator, school_id, school_name)
        self.group_name = group_name
        slug = group_name.lower().replace(" ", "_").replace("'", "")
        self._attr_name = f"{school_name} Lunch {group_name}"
        self._attr_unique_id = f"{school_id}_lunch_group_{slug}"
        self._attr_icon = "mdi:food"

    def _group_items(self, offset: int = 0) -> list[str]:
        key = (dt_util.now().date() + timedelta(days=offset)).isoformat()
        return (self.coordinator.menu_groups or {}).get(key, {}).get(self.group_name, [])

    @property
    def native_value(self):
        items = self._group_items()
        return f"{len(items)} items" if items else "No menu"

    @property
    def extra_state_attributes(self):
        attrs = super().extra_state_attributes
        attrs.update({
            "menu_group": self.group_name,
            "date": dt_util.now().date().isoformat(),
            "menu": {
                day: groups.get(self.group_name, [])
                for day, groups in (self.coordinator.menu_groups or {}).items()
            },
        })
        return attrs
