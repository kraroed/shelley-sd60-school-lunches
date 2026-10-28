# Changelog

## 1.4.8 - 2026-10-27

- Separate Shelley High School lunch into Main Menu, Hot n Ready, Grab N Go, and Shared Items sensors while preserving existing combined-menu sensors.

## 1.4.7 - 2026-10-27

- Add a concise summary of all LINQ menu group names and IDs found in the response, so users do not need to search through individual nested debug lines.

## 1.4.6 - 2026-10-27

- Log LINQ menu group label fields including null values and value types, to diagnose why menu-group names are missing.

## 1.4.5 - 2026-10-27

- Expanded LINQ menu diagnostics to log nested object keys and list lengths even when group labels use unexpected field names.

## 1.4.4 - 2026-10-27

- Added targeted debug logging for LINQ menu-group labels and object keys to help identify main, alternate, and shared menu sections without logging the full API payload.

## 1.4.3 - 2026-10-27

- Prevented long lunch lists from exceeding Home Assistant's 255-character state limit; the Today and Tomorrow sensors now show an item count while keeping the complete menu in attributes.
- Use Home Assistant's configured timezone for menu date selection and date attributes.

## 1.4.2 - 2026-10-27

- Fixed LINQ menu parsing for alternate/nested response structures.
- Added normalization for common LINQ date formats.
- Added debug logging for matched serving sessions and parsed menu days.
- Preserved existing configuration entry and entity IDs.

## 1.4.1 - 2026-10-26

- Added browser-like request headers for LINQ Connect, which may block requests without them.
- Improved API error reporting so HTTP blocks and unexpected/non-JSON responses are visible in Home Assistant logs.

## 1.4.0 - 2026-10-26

- Renamed the project branding to **Shelley SD60 School Lunches**.
- Updated README, HACS metadata, and GitHub links for `shelley-sd60-school-lunches`.
- Kept the Home Assistant integration domain `linq_shelley` unchanged to preserve configuration compatibility.

## 1.3.0 - 2026-10-26

- Prepared repository for HACS/custom-repository installation.
- Added complete README with installation, configuration, entities, and dashboard documentation.
- Added a ready-to-use Lovelace dashboard example.
- Added changelog, MIT license, issue templates, and repository metadata.
- Removed generated Python cache files from the distribution.

## 1.2.0

- Added calendar entities.
- Added 14-day menu sensors.
- Added direct Today and Tomorrow menu states.
- Added all six Shelley District 60 LINQ schools.

## 1.1.0

- Added all six Shelley LINQ building IDs.

## 1.0.0

- Initial Shelley LINQ Connect integration.
