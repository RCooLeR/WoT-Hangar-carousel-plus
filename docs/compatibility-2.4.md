# World of Tanks 2.4.0.0 compatibility report

The Wargaming EU 2.4.0.0 client was reviewed and tested on 2026-09-02.
The installed client reports **2.4.0.0 #930**, revision **2607998**, matching
the resources previously inspected in the EU preload
`wot_2.4.0.5419_eu_iwbmp6`.

## Release

- Stable mod version: **0.8.14**.
- Standalone package: `com.rcooler.hangar_carousel_plus_0.8.14.wotmod`.
- Complete bundle: `Hangar_Carousel_Plus_0.8.14_complete.zip`.
- Bundle layout: `mods/2.4.0.0/`.
- Included dependencies: OpenWG Gameface 1.1.6, ModsListAPI 1.7.9, and
  ModsSettingsAPI 1.7.0.
- User configuration and runtime files are deliberately excluded from the
  bundle and remain under `mods/configs/RCooLeR/`.

## Compatibility findings

The standard hangar, vehicle tooltip, and all five supported event-hangar
bundles changed from 2.3.1.3. The 2.4 release therefore uses independently
reviewed SHA-256 profiles and regenerated native substitutions; no patched
2.3 resources are reused.

`tools/check-client-api.py` inspects Python 2.7 code objects without importing
or executing client code. Ten fingerprints guard the generated model layouts
and exact private hooks used by HCP. The final 2.4.0.0 client passes those
contracts. Every native patch also verifies its source checksum and exact
replacement count.

The 2.4 native `VehicleFiltersDataProvider` initially stores its private row
count as `None`. Candidate RC1 exposed an `int(None)` failure when changing
rows. RC2 added a bounded fallback for the uninitialized provider/model state
and regression coverage for both `None` cases.

## Validation

The final release build passed:

- ten private client API contracts;
- six client-contract tests and ten automatic-row tests under Python 2.7;
- JavaScript syntax and behavior checks for the standard hangar, Comp7,
  Comp7 Light, Frontline, Fun Random, and Last Stand;
- 144 row-chunk cases per supported carousel plus sorting and DOM-anchor tests;
- vehicle-tooltip syntax and DOM-anchor tests;
- `.wotmod`, complete-bundle, dependency, layout, and checksum validation.

The release candidate was installed without replacing the existing user
configuration. A live hangar and full-battle smoke test loaded HCP, populated
382 vehicle/statistic records, rendered tooltip statistics, and changed
automatic rows from 2 to 4 and back to 2. The post-test log contained no HCP
warning, traceback, failed row update, or package-loader failure, and the
client exited normally.

## Rebuild

From the repository root:

```powershell
.\tools\build.ps1 -GameRoot '<reviewed-2.4.0.0-client-root>'
```

The build must stop on an unknown client version, changed guarded API,
unexpected native resource hash, or changed replacement count. Never bypass
those checks to reuse an artifact after a client update.

Battle Royale remains outside the patch contract because it does not use the
shared `VehicleFilters` provider. Event modes unavailable during the live
session retain checksum-verified automated coverage but should be smoke-tested
again when their servers are active.
