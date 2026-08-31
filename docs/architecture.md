# Architecture

## Python bridge

`mod_hangar_carousel_plus.py` extends `VehicleFilterModel` by two properties before Wulf initializes it:

1. OpenWG's `ModInjectModel`, which loads the CSS and ES module into the existing hangar view;
2. `HangarCarouselPlusModel`, which carries one JSON snapshot, the active-toggle set, and three commands.

The original model's four properties and three commands keep their indices. The patch only appends properties, avoiding changes to native filter serialization.

## Smart filter registry

`FILTER_ORDER` defines the public filters and `_matches()` dispatches their predicates. Active predicates are combined with AND. HCP patches `VehiclesStatisticsPresenter` so its native statistics map contains only matching owned vehicles; the unmodified Gameface provider then applies normal client filters and virtualization.

To add a filter:

1. add its ID to `FILTER_ORDER`;
2. implement a predicate branch in `_matches()`;
3. add localized labels in the Gameface module;
4. add the ID to `config/default.json` when it should be enabled by default.

## Statistics

The account random-statistics cut supplies battles, wins, and mastery. Per-vehicle dossiers already cached by the client supply random-battle damage and Marks of Excellence. The Gameface module adds overlays only to currently rendered cards and re-applies them as the virtual list changes.

The native vehicle tooltip gets a child model containing the same configured statistic snapshot. Root tooltip documents are outside OpenWG's subview injector, so the build appends the localized renderer to a checksum-verified copy of the native tooltip bundle and appends its styles to the matching native stylesheet. The renderer adds a section before the native vehicle-status row and re-applies it if React replaces the tooltip DOM.

## Carousel rows

`VehicleFiltersDataProvider` is extended to accept row counts one through four and persists the selection in HCP's runtime state. Automatic mode ignores transient empty lists, waits briefly for Gameface's visible-vehicle count to stabilize, and passes the candidate through a second Python-side debounce. The most recently loaded provider owns that coordinator; stale providers cannot cancel its pending value, and an automatic result is applied only to the active requester. Finalizing the active provider cancels its callback and promotes the most recently loaded remaining provider. The promoted provider's automatic observable is re-armed across callback ticks so its own current amount is recalculated even when no other Gameface dependency changed; identity and mode checks prevent a finalized or superseded provider from being re-enabled. Unchanged effective values skip runtime writes, model refreshes, and native rebuilds. The supported native renderer chunks only in pairs and uses equality checks for the double-row branch, so `patch-native-carousel.ps1` generalizes exact expressions in the standard hangar bundle. `patch-native-event-carousels.ps1` applies the same model, sorting, chunking, navigation, rendering, height, and automatic-row contract to the separate Comp7, Comp7 Light, Frontline, Fun Random, and Last Stand hangar bundles. Last Stand's `HangarApp_carousel__double` wrapper is handled independently from the other modes' `Page_carousel__double` wrapper. Battle Royale is not patched because its carousel does not use the shared `VehicleFilters` provider contract.

Every native source has its own SHA-256 guard, and every semantic replacement must match the expected count before a build can continue. The filter popover deliberately retains its native height because its portal anchor moves with the carousel; HCP scopes a higher-contrast scrollbar style to that popover instead. Generated patched bundles are packaged, but no Wargaming source bundle is stored in the repository.

## Sorting and last played

The checksum-guarded native carousel hook sorts the final vehicle list without creating playlists. Numeric modes receive cached per-vehicle values from Python. Battle Pass sorting uses the current season's earned value returned by `IBattlePassController.getVehicleProgression()` and invalidates only affected vehicles when the controller publishes point updates. Priority mode assigns three stable buckets—primary vehicles, incomplete Field Modification, and all remaining vehicles—so the client's existing order is preserved inside every bucket. Last-played timestamps remain local to HCP.

The garage API does not provide a historical last-played value per vehicle. HCP records the vehicle and timestamp on the global real-battle `onAvatarReady` event, skips replay playback, and stores this private local data in `mods/configs/RCooLeR/hangar_carousel_plus.runtime.json`. Untracked vehicles remain after tracked vehicles for both directions.

## Compatibility boundaries

- Python: generated `VehicleFilterModel`, `VehiclesStatisticsPresenter`, vehicle/tankman wrappers, and post-progression completion.
- Gameface: OpenWG subview injection, `FilterPopover_*`, `data-test-id="vehicleCard-<intCD>"`, and the checksum-locked standard and compatible event hangar bundles for WoT 2.3.1.

Every client update requires re-validating all native bundle substitutions before a new package can be built.
