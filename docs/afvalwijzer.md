# Afvalwijzer (Netherlands)

Buddyplan includes an **optional** integration with Dutch household waste collection schedules. It is aimed at users in the Netherlands whose municipality publishes data via [mijnafvalwijzer.nl](https://www.mijnafvalwijzer.nl).

This module is **not required** for core todo and agenda functionality. Disable it if you do not use Dutch waste-collection schedules.

## What it does

When enabled, Buddyplan can:

1. Fetch waste types and pickup dates for your postcode and house number
2. Let you configure which waste streams matter to your household
3. Assign "put out" (`buitenzetten`) and "bring in" (`binnenzetten`) tasks to family members
4. Create one-off tasks automatically for the relevant week(s)

Tasks appear in the normal task list and sync to mobile and wall-display apps like any other task.

## Requirements

- Admin access to the Buddyplan web UI
- A Dutch postcode and house number covered by mijnafvalwijzer.nl
- At least one person in Buddyplan to assign tasks to

## Setup

1. Log in to the web admin as an administrator.
2. Open **Persoonlijk → Afvalwijzer** (`/admin/afvalwijzer`).
3. Enable **Afvaltaken aanmaken**.
4. Enter your **postcode** and **huisnummer** (including suffix if applicable, e.g. `12A`).
5. Click **Synchroniseren** to load waste types from mijnafvalwijzer.nl.
6. For each waste type you want to track:
   - Enable the type
   - Set a short label (`naam`)
   - Choose who handles putting bins out and bringing them in
   - Pick timing: day before pickup, same day, or day after
7. Use **Taken nu aanmaken** to generate tasks for the current planning period.

## Scheduling behaviour

For each enabled waste type and pickup date in range:

| Task | Default timing |
|------|----------------|
| Buitenzetten | Day before pickup (configurable) |
| Binnenzetten | Same day as pickup (configurable) |

Duplicate tasks for the same person, title, and date are skipped.

## Privacy and external data

- Buddyplan requests **public** schedule pages from mijnafvalwijzer.nl using the postcode and house number you provide.
- No Afvalwijzer API key is stored; requests are made server-side when you sync or create tasks.
- Address data is stored in your local Buddyplan database (`afvalwijzer_config` table).

## Limitations

- Only works for addresses supported by mijnafvalwijzer.nl
- Schedule parsing depends on the external site's HTML structure; breakage is possible if the site changes
- Task creation is manual or triggered from the admin UI (no background cron is documented here)
- Labels and task text are in Dutch

## Disabling

Turn off **Afvaltaken aanmaken** in the Afvalwijzer admin page. Existing tasks created by the integration are not removed automatically.
