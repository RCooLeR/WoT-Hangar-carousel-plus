# Hangar Carousel Plus

[Українська](README.md) · English

Hangar Carousel Plus extends the native World of Tanks 2.x hangar carousel with smart filters, sorting, local statistics, and configurable row layouts.

The mod currently targets the Wargaming EU 2.4.0.0 client and provides:

- filters for incomplete Field Modification, incompletely trained crews, and non-elite vehicles;
- reward/special, not-ready, no-Ace, fewer-than-three-Marks, and research-now-available filters;
- battles, win rate, average damage, mastery, and Marks of Excellence on vehicle cards and in the native hover card;
- sorting by battles, win rate, average damage, Marks of Excellence, Battle Pass points, last played, or the priority chain “primary → incomplete Field Modification → native default order”;
- one-, two-, three-, and four-row carousel layouts with automatic mode in the standard hangar and compatible Comp7, Comp7 Light, Frontline, Fun Random, and Last Stand hangars;
- optional hiding of the Buy vehicle, Buy slot, and Restore vehicle cells;
- a settings page through ModsSettingsAPI;
- localization for all 24 EU client languages.

No account credentials or statistics are sent to an external service.

[![Hangar Carousel Plus filters, sorting, statistics, and three-row carousel](docs/images/hangar-carousel-plus.png)](docs/images/hangar-carousel-plus.png)

## Download and install

[Download the complete Hangar Carousel Plus 0.8.14 bundle](releases/0.8.14/Hangar_Carousel_Plus_0.8.14_complete.zip?raw=1)

1. Close World of Tanks.
2. Remove older `com.rcooler.hangar_carousel_plus_*.wotmod` files from `<game>\mods\<current-client-version>\`.
3. Extract the ZIP directly into the World of Tanks root and allow it to merge the `mods` directory.
4. Start the game.

The bundle already contains HCP and all required dependencies in the standard `mods\<current-client-version>\` structure. Advanced users can also download the [standalone HCP file](releases/0.8.14/com.rcooler.hangar_carousel_plus_0.8.14.wotmod?raw=1). Checksums are stored in `SHA256SUMS.txt`, and bundled third-party components are documented in `THIRD_PARTY.md`.

## Requirements

- World of Tanks Wargaming client 2.4.0.0;
- `net.openwg.gameface` 1.1.6 or newer and ModsSettingsAPI, both included in the complete bundle.

## Configuration

The active configuration is stored at:

```text
<game>\mods\configs\RCooLeR\hangar_carousel_plus.json
```

Use the ModsSettingsAPI page or edit `filters.enabled`, `cardStats`, `sorting`, and `actionCards`.

Sorting direction, last-played timestamps, and carousel row mode are stored in `hangar_carousel_plus.runtime.json` beside the configuration. The old files under `res_mods\configs\hangar_carousel_plus` are migrated automatically on first launch.

The standard filter popover retains the client's native height. For easier access to the additional controls, the mod makes its scrollbar more visible.

Automatic row mode uses the final vehicle count after native and HCP filters:

- up to 8 vehicles: 1 row;
- up to 16: 2 rows;
- up to 24: 3 rows;
- more than 24: 4 rows.

While switching hangars, the mod ignores a transient empty list and waits for the visible vehicle list to stabilize before applying a new row count.

## Filters

Every HCP icon is an independent toggle. Active HCP predicates are combined with logical **AND**, after which the client applies its normal nation, type, role, level, special, and name filters.

HCP deliberately does not duplicate the client’s existing filters for Premium, Elite, rented/temporary vehicles, the daily first-victory bonus, or vehicles that can still earn Battle Pass points.

Field Modification is considered incomplete only when the vehicle is eligible for the system, its tree exists, and the native completion state is not `FULL`.

A crew is considered incomplete when a required slot is empty, qualification or efficiency is below 100%, a perk is still being trained, or another learnable perk slot is available.

## Statistics

Vehicle cards show four compact, shadow-free lines containing battles and win rate, average damage, mastery, and Marks of Excellence. Metric-aware colors make the values easier to scan. The same data is injected as a native section into the vehicle hover card.

## Carousel rows

The controls in the filter panel select one to four rows or automatic mode. Automatic mode uses the thresholds listed in the configuration section.

## Localization

The language is detected automatically. HCP includes all 24 languages declared by the WoT EU client: Bulgarian, Czech, Danish, German, Greek, English, Spanish, Finnish, French, Croatian, Hungarian, Italian, Lithuanian, Latvian, Dutch, Norwegian, Polish, Portuguese, Romanian, Serbian, Swedish, Turkish, Russian, and Ukrainian. Missing individual strings fall back to English.

## Uninstall

Remove `com.rcooler.hangar_carousel_plus_*.wotmod` from the active `mods\<client-version>` directory. The configuration and locally tracked last-played data may be removed separately.

Development, build, and release documentation: [DEVELOPERS.md](DEVELOPERS.md).
