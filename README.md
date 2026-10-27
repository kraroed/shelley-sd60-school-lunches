# Shelley SD60 School Lunches

Home Assistant custom integration for the public **LINQ Connect** school meal menus used by Shelley School District 60 in Idaho.

[![Validate](https://github.com/kraroed/shelley-sd60-school-lunches/actions/workflows/test.yml/badge.svg)](https://github.com/kraroed/shelley-sd60-school-lunches/actions/workflows/test.yml)

## Supported schools

- Dean Goodsell Elementary
- Hobbs Middle School
- Riverview Elementary
- Shelley High School
- Stuart Elementary
- Sunrise Elementary

The integration uses the district's public LINQ Connect menu API. No LINQ account, student credentials, or personal information are required.

## Features

- Breakfast or lunch menu selection during setup
- Today's menu sensor for every school
- Tomorrow's menu sensor for every school
- 14-day menu sensor for every school
- Calendar entity for every school
- Full menu data in entity attributes
- Automatic polling with a configurable interval
- Separate Home Assistant device for each school
- HACS-compatible repository layout

## Installation with HACS

### Custom repository

1. Open **HACS → Integrations**.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add `https://github.com/kraroed/shelley-sd60-school-lunches`.
4. Select **Integration** as the category.
5. Install **Shelley SD60 School Lunches**.
6. Restart Home Assistant.
7. Go to **Settings → Devices & services → Add Integration**.
8. Search for **Shelley SD60 School Lunches**.
9. Choose **Lunch** or **Breakfast** and the polling interval.

### Manual installation

Copy the `custom_components/linq_shelley` directory into:

```text
/config/custom_components/linq_shelley
```

Restart Home Assistant and add the integration from **Settings → Devices & services**.

## Dashboard example

A simple entities card:

```yaml
type: entities
title: Shelley School Lunch
show_header_toggle: false
entities:
  - entity: sensor.dean_goodsell_elementary_lunch_today
    name: Dean Goodsell
  - entity: sensor.hobbs_middle_school_lunch_today
    name: Hobbs Middle
  - entity: sensor.riverview_elementary_lunch_today
    name: Riverview
  - entity: sensor.shelley_high_school_lunch_today
    name: Shelley High
  - entity: sensor.stuart_elementary_lunch_today
    name: Stuart
  - entity: sensor.sunrise_elementary_lunch_today
    name: Sunrise
```

Entity IDs can vary slightly depending on existing entities and Home Assistant's naming rules; use the entity picker if necessary.

A more complete dashboard example is included in [`examples/lunch-dashboard.yaml`](examples/lunch-dashboard.yaml).

## Sensors

Each school receives:

- `<School> <Meal> Today` – comma-separated menu items for today
- `<School> <Meal> Tomorrow` – comma-separated menu items for tomorrow
- `<School> <Meal> Menu` – number of days returned, with the full menu in attributes
- `<School> <Meal> 14 Day Menu` – number of days returned, with the full menu in attributes
- `<School> <Meal> Calendar` – calendar events for days with menu items

The daily sensors also expose the menu as a `menu` attribute. The menu sensors expose a date-to-items mapping under `menu`.

## LINQ configuration

The integration is preconfigured for Shelley School District 60:

- District ID: `bff2ebbd-7278-eb11-a2d4-c8076e69fc1e`
- Six LINQ building IDs are stored in `const.py`.

These identifiers are public menu identifiers, not credentials.

## Development

Create a Home Assistant development environment, then run the tests with:

```bash
pytest -q
```

The GitHub Actions workflow also compiles the integration Python modules and runs the parser tests.

## License

MIT. See [`LICENSE`](LICENSE).

## Disclaimer

This project is an independent community integration and is not affiliated with, endorsed by, or sponsored by LINQ Connect or Shelley School District 60.
