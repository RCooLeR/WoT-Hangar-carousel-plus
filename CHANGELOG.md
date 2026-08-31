# Changelog

## 0.8.13 - 2026-08-21

- Stabilize automatic carousel rows while the standard and event hangars rebuild their vehicle models.
- Ignore transient empty vehicle counts and debounce row changes across Comp7, Comp7 Light, Frontline, Fun Random, and Last Stand.
- Let only the most recently loaded native carousel provider schedule and receive automatic row changes during hangar transitions.
- Re-arm automatic calculation when a previously hidden provider is promoted after the active event hangar closes.
- Skip unchanged runtime writes, model refreshes, and native carousel rebuilds.

## 0.8.12 - 2026-08-20

- Add compatibility with the Wargaming EU 2.3.1.3 client bundles.
- Revalidate the standard, Comp7, and Last Stand native carousel substitutions after the client rebuild.
- Preserve byte-identical Frontline, Comp7 Light, Fun Random, and vehicle-tooltip integrations.

## 0.8.11 - 2026-08-17

- Support one through four carousel rows in the separate Comp7, Comp7 Light, Frontline, Fun Random, and Last Stand Gameface hangars.
- Apply automatic row selection and native-list sorting consistently in every compatible event hangar namespace.
- Add checksum and replacement-count guards for all five event bundles and validate every patched renderer in the release package.

## 0.8.10 - 2026-08-14

- Treat transient Gameface carousel remounts as normal lifecycle events instead of warnings.
- Remove redundant tooltip render polling and retain mutation-driven rendering with a low-frequency model sync fallback.
- Keep live Wulf models in a weak registry so repeated hangar reconstruction cannot retain stale model instances.
- Replace unsupported Gameface selectors and tooltip white-space styling with explicit classes and line elements.
- Produce a checksum-verified complete ZIP with all runtime dependencies in `dist` on every build.

## 0.8.9 - 2026-08-12

- Add ascending and descending sorting by Battle Pass points earned on each vehicle in the current season.
- Refresh cached Battle Pass values from the client's vehicle-point and season events.
- Move user configuration to `mods/configs/RCooLeR/hangar_carousel_plus.json` and runtime state beside it, with automatic migration from the legacy `res_mods/configs` location.
- Keep the native filter popover height and improve its scrollbar contrast so the additional controls remain discoverable at every carousel size.

## 0.8.8 - 2026-08-12

- Add compatibility with the Wargaming EU 2.3.1.2 client bundles.
- Revalidate all native carousel substitutions against the updated hangar bundle.
- Refresh the native vehicle-tooltip checksum for the 2.3.1.2 hotfix.

## 0.8.7 - 2026-08-06

- Add priority sorting: primary vehicles first, then vehicles with incomplete Field Modification, then the native default order.
- Keep all seven sort modes and the direction control on one compact row.
- Cache per-vehicle filter and statistic data so filter toggles no longer reread every dossier several times.
- Invalidate only changed vehicle cache entries and batch model refreshes after client updates.
- Replace the 250 ms card-stat polling loop with filtered, throttled DOM observation.

## 0.8.6 - 2026-08-06

- Add compatibility with the Wargaming EU 2.3.1.1 client bundles.
- Revalidate every native carousel substitution against the updated hangar bundle.
- Refresh the native vehicle-tooltip checksum for the 2.3.1.1 hotfix.
- Update the complete release layout and bundled Gameface dependency for 2.3.1.1.

## 0.8.5 - 2026-07-17

- Replace Gameface-incompatible text sorting glyphs with six dedicated white SVG icons and SVG direction arrows.
- Remove the unsupported `-webkit-text-fill-color` property that prevented reliable sort icon rendering.

## 0.8.4 - 2026-07-17

- Force row-layout SVG bars and digits white at their actual DOM nodes.
- Render sorting glyphs in dedicated spans with inline-important white text fill for Gameface compatibility.
- Add Ukrainian and English project documentation.

## 0.8.3 - 2026-07-17

- Remove gold, Free XP, and bond protection to keep the project focused on the hangar carousel.
- Remove the related Gameface controls, Python account-property patches, settings, styles, and configuration defaults.

## 0.8.2 - 2026-07-17

- Override late-loading WoT SVG and button rules on the actual filter and sorting glyph nodes so icons stay white outside hover state.

## 0.8.1 - 2026-07-17

- Base automatic carousel rows on the final visible vehicle list after native and HCP filters.
- Render filter, refresh, and sorting glyphs white in normal and active states.

## 0.8.0 - 2026-07-17

- Audit WoT 2.3.1 native filters and avoid duplicating Premium, Elite, rental, daily-bonus, and Battle Pass availability criteria.
- Add reward/special, not-ready, no-Ace, fewer-than-three-Marks, and immediately researchable filters.
- Restore native-list sorting by battles, win rate, average damage, Marks of Excellence, and locally tracked last played time.
- Add optional hiding for Buy vehicle, Buy slot, and Restore vehicle action cards.
- Add optional gold, Free XP, and bond protection.
- Register a config-preserving settings page through ModsSettingsAPI 1.7.
- Localize the new filter names, descriptions, and sorting controls for all 24 supported client languages.

## 0.7.3 - 2026-07-17

- Add icon-and-digit controls for manual carousel row counts.
- Add a persistent automatic row mode based on the client's final filtered vehicle count.
- Localize the automatic mode name and threshold description for every supported client language.

## 0.7.2 - 2026-07-17

- Display card statistics as four compact rows instead of a two-column table.
- Give three- and four-row carousels native row-count classes and fixed responsive heights.
- Prevent the flex layout from shrinking extended carousels back toward the two-row height.

## 0.7.1 - 2026-07-17

- Replaced unsupported Gameface table layout with fixed-width flex columns.
- Kept statistics in exactly two rows while preserving wider spacing between metrics.
- Moved the HCP tooltip script and style into checksum-guarded native tooltip resources because root tooltip documents are not processed by OpenWG's subview injector.

## 0.7.0 - 2026-07-17

- Changed card statistics to a two-row table with stable metric columns and wider spacing.
- Fixed hover-card injection by loading its resources as classic scripts and added connection diagnostics.
- Added localized 1–4 row controls to the HCP filter panel.
- Generalized the WoT 2.3.1 native carousel chunking, sizing, navigation, and rendering from two rows to four.
- Added an exact-SHA guard so building fails safely instead of patching an unknown client bundle.

## 0.6.0 - 2026-07-17

- Moved carousel statistics to the bottom-left of each vehicle card.
- Increased card-stat font size and removed all text shadows.
- Added the configured HCP statistics as a native section in the vehicle hover tooltip.
- Localized hover-card statistic names for all 24 supported client languages.

## 0.5.1 - 2026-07-17

- Removed card-stat borders and black backgrounds in favor of transparent, shadowed text.
- Added value-ranked win-rate colors and distinct battle, damage, mastery, and Marks of Excellence colors.
- Increased filter tooltip title and description sizes and widened the tooltip.

## 0.5.0 - 2026-07-17

- Added localized filter names and descriptions for all 24 languages declared by the WoT EU client metadata.
- Added automatic normalization for uppercase, hyphenated, and regional locale codes.
- Moved additional translations into a dedicated Gameface i18n module with per-key English fallback.

## 0.4.4 - 2026-07-17

- Added complete English, Russian, and Ukrainian filter names, descriptions, state, and matching-count text.
- Read the language from the WoT client payload instead of the embedded browser locale.
- Localized compact statistic labels.
- Moved statistic children to the outer native vehicle-card node so they render above internal card overlays.
- Inherited the native Gameface font and weight instead of requesting unloaded font faces.

## 0.4.3 - 2026-07-17

- Replaced SVG `currentColor` inheritance with explicit normal, active, and white-hover stroke colors for Gameface compatibility.

## 0.4.2 - 2026-07-17

- Moved statistic rows from the body-level portal into real child elements of each native `Card_content` node.
- Re-adds the native child automatically whenever Gameface replaces a card during interaction.
- Includes the visible tooltip and white icon-hover changes that were built but not installed with 0.4.1.

## 0.4.1 - 2026-07-17

- Added visible Gameface hover tooltips with filter name, matching vehicle count, and on/off state.
- Changed filter icons to pure white on hover.
- Replaced unsupported CSS-generated card text with explicit, body-level statistic rows positioned over visible carousel cards.

## 0.4.0 - 2026-07-17

- Replaced dynamic HCP playlists with independent native-model on/off filter toggles.
- Combined active HCP filters with AND while preserving all standard client filters.
- Added automatic removal of obsolete `rcooler_hcp_` playlists to eliminate ownership warnings.
- Temporarily removed HCP custom sorting because playlist ordering is no longer used.
- Kept the compact SVG controls and native-card statistics layer from the unreleased 0.3.1 build.

## 0.3.1 - 2026-07-17

- Replaced filter text with five compact SVG icons and localized tooltips.
- Replaced the unsupported expanded HTML sorting selector with compact sort icons.
- Moved card statistics to a native-card CSS pseudo-layer so React cannot remove the text node.
- Increased card-stat contrast and added explicit two-line overlay dimensions.

## 0.3.0 - 2026-07-17

- Moved smart filters and sorting into the native vehicle-filter popover.
- Fixed Gameface command invocation so smart filters and sorting reach Python.
- Moved card statistics into the native card content layer and changed them to a compact two-line layout.
- Added filter and card-stat diagnostics plus safe handling of an empty native playlist selection.

## 0.2.2 - 2026-07-17

- Replaced unsupported Gameface `:scope` selectors that prevented filter and card-stat rendering.
- Corrected Python 2 Unicode handling when saving last-played runtime state.
- Added validation that rejects unsupported `:scope` selectors.

## 0.2.1 - 2026-07-17

- Changed `.wotmod` packaging to uncompressed ZIP entries, as required by the WoT 2.3.1 mod loader.
- Added a build-time compression check to prevent incompatible packages from being produced.

## 0.2.0 - 2026-07-17

- Added a non-elite/research-remaining smart filter.
- Added ascending and descending sorting by battles, win rate, average damage, Marks of Excellence, and last played.
- Added local last-played tracking from battles entered after installation.
- Confirmed that the native `bonus` filter already covers the available daily first-victory multiplier.

## 0.1.0 - 2026-07-17

- Added smart filters for incomplete Field Modification, crew not maxed, premium vehicles, and all vehicles.
- Added local battles, win rate, average damage, mastery, and Marks of Excellence overlays.
- Added native-playlist integration without patching the Wargaming hangar bundle.
- Added config-preserving build/install tooling and Python 2.7 package validation.
