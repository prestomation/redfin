# Redfin Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]

[![hacs][hacsbadge]][hacs]
[![maintainer][maintenance-shield]][maintainer]

<img src="https://raw.githubusercontent.com/home-assistant/brands/master/custom_integrations/redfin/logo.png" width="40%">

### _This component requires HA Core version 2021.6.0 or greater._

This is a _Custom Integration_ for [Home Assistant](https://www.home-assistant.io/). It uses the unofficial [Redfin](https://www.redfin.com) API to get property value estimates and neighborhood scores.

Uses [`prestomation/pyredfin`](https://github.com/prestomation/pyredfin) — a maintained fork of the original `redfin` Python library with:
- Fixed 403 errors (real browser User-Agent)
- Working `neighborhood_stats()` endpoint
- Rate limit handling

## Installation

### HACS installation

Go to the HACS page and search for _Redfin_.

### Manual Installation

Create `custom_components/redfin/` in your HA config directory and drop in all files from this repo.

## Configuration

You will need the Redfin property ID for each property you'd like to track. Find it in the Redfin URL:

> `https://www.redfin.com/DC/Washington/1745-Q-St-NW-20009/unit-3/home/9860590`
>
> Property ID: `9860590`

Add the Redfin integration via Home Assistant UI and follow the prompts.

## Sensor Attributes

| Attribute | Description |
|-----------|-------------|
| `amount` | Estimated property value (USD) |
| `amount_currency` | `USD` |
| `amount_formatted` | Human-readable estimate (e.g. "Est. $750K") |
| `address` | Street address |
| `full_address` | Full address including city and state |
| `redfin_url` | Link to property on Redfin |
| `street_view` | Google Street View link (from lat/long) |
| `walk_score` | Walk Score (0–100) |
| `bike_score` | Bike Score (0–100) |
| `transit_score` | Transit Score (0–100) |
| `property_id` | Redfin property ID |

## Note on Requirements

The integration currently pulls `pyredfin` directly from GitHub. Once published to PyPI, this will switch to a version-pinned PyPI install.

<!---->

[commits-shield]: https://img.shields.io/github/commit-activity/y/prestomation/redfin.svg
[commits]: https://github.com/prestomation/redfin/commits/main
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40prestomation-blue.svg
[releases-shield]: https://img.shields.io/github/v/release/prestomation/redfin
[releases]: https://github.com/prestomation/redfin/releases
