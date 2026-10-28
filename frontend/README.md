# Shelley SD60 Lunch Card

A standalone Home Assistant Lovelace custom card for the [Shelley SD60 School Lunches integration](https://github.com/kraroed/shelley-sd60-school-lunches).

## Features

- School selector for all six Shelley SD60 schools.
- Today, Tomorrow, and 14 Days views.
- Uses live Home Assistant sensor states and the integration's `menu`, `date`, and `school` attributes.
- Separate menu-group sections for Hobbs Middle School (Main Menu, Second Line, Shared Items) and Shelley High School (Main Menu, Hot n Ready, Grab N Go, Shared Items).
- Responsive styling that follows Home Assistant theme variables.
- No external JavaScript dependencies.

## Important HACS note

This source currently lives alongside the integration for development. HACS classifies repositories as either an Integration or a Dashboard plugin; a clean standalone HACS Dashboard release should be published in its own repository named `lovelace-shelley-sd60-lunch-card`, with this file at the repository root and named `shelley-sd60-lunch-card.js`, plus a `hacs.json` containing `{"name":"Shelley SD60 Lunch Card"}`. Do not change the integration repository's existing HACS category just to install this card.

## Manual test install

1. Copy `shelley-sd60-lunch-card.js` to `/config/www/shelley-sd60-lunch-card.js`.
2. In Home Assistant, open **Settings → Dashboards → Resources** and add `/local/shelley-sd60-lunch-card.js` with resource type **JavaScript Module**.
3. Add a Manual card to a dashboard using the YAML below.
4. Hard-refresh the browser if the resource was already cached.

```yaml
type: custom:shelley-sd60-lunch-card
title: Shelley SD60 Lunch Menu
default_school: hobbs_middle
```

## Entity mapping

The card uses the integration's standard entity IDs by default:

- `sensor.dean_goodsell_elementary_lunch_today`
- `sensor.hobbs_middle_school_lunch_today`
- `sensor.riverview_elementary_lunch_today`
- `sensor.shelley_high_school_lunch_today`
- `sensor.stuart_elementary_lunch_today`
- `sensor.sunrise_elementary_lunch_today`

The Tomorrow and 14 Day sensors use the same prefix with `_tomorrow` and `_14_day_menu` suffixes. Because Home Assistant may preserve existing IDs or add suffixes, any entity can be overridden:

```yaml
type: custom:shelley-sd60-lunch-card
entities:
  hobbs_middle:
    today: sensor.hobbs_middle_school_lunch_today
    tomorrow: sensor.hobbs_middle_school_lunch_tomorrow
    14days: sensor.hobbs_middle_school_lunch_14_day_menu
    groups:
      Second Line: sensor.hobbs_middle_school_lunch_second_line
```

## Integration attributes verified

The integration source exposes `school`, `meal`, `building_id`, `district_id`, `menu_url`, `date`, and `menu` on daily sensors. The daily `menu` attribute is a list of items. The 14-day `menu` attribute is a date-to-items mapping. Group sensors expose `menu_group`, `date`, and a date-to-items mapping under `menu`; this card handles the current group list when supplied by the integration.
