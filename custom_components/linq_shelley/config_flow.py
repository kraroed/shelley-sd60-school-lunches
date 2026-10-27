from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL

from .const import DOMAIN, DISTRICT_ID, CONF_MEAL, MEAL_LUNCH, MEAL_BREAKFAST


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 3

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(DISTRICT_ID)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Shelley SD60 School Lunches",
                data={
                    "district_id": DISTRICT_ID,
                    **user_input,
                },
            )

        schema = vol.Schema({
            vol.Required(CONF_MEAL, default=MEAL_LUNCH): vol.In([MEAL_LUNCH, MEAL_BREAKFAST]),
            vol.Required(CONF_SCAN_INTERVAL, default=60): vol.All(
                vol.Coerce(int), vol.Range(min=15, max=1440)
            ),
        })
        return self.async_show_form(step_id="user", data_schema=schema)
