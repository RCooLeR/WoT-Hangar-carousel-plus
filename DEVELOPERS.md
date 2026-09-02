# Developer guide

[User documentation (Українська)](README.md) · [User documentation (English)](README-EN.md) · [Architecture](docs/architecture.md)

## Compatibility boundary

Hangar Carousel Plus currently targets the Wargaming EU 2.4.0.0 client. Its Python APIs, generated models, DOM hooks, and version-locked native Gameface bundle substitutions are private game interfaces. Rebuild and test the mod after every World of Tanks update.

The native carousel and tooltip patches are protected by source checksums and exact replacement counts. The build stops when the installed client resources do not match the supported version. Patched client resources are generated locally; no original Wargaming bundle is committed to this repository.

Reviewed source hashes live in `tools/client-profiles.json`. The 2.3.1.3 profile is retained for reproducibility, while 2.4.0.0 is the current stable release profile. `tools/check-client-api.py` also checks bytecode fingerprints for the exact private models and presenter methods HCP patches, without importing or executing client code.

## Prerequisites

- Windows PowerShell 5.1 or PowerShell 7;
- a local World of Tanks Wargaming EU 2.4.0.0 installation;
- enough network access for the first build to download the official Python 2.7.18 MSI.

When `-Python27` is not supplied, `tools/bootstrap-python27.ps1` verifies and extracts the official MSI into the local `.tools/` directory. It does not install Python system-wide.

## Build

From the repository root:

```powershell
.\tools\build.ps1
```

The default game root is declared in `tools/build.ps1`. Override it for another installation:

```powershell
.\tools\build.ps1 -GameRoot 'E:\Games\World of Tanks'
```

The package is written to:

```text
dist\com.rcooler.hangar_carousel_plus_0.8.14.wotmod
dist\Hangar_Carousel_Plus_0.8.14_complete.zip
```

Build and install in one step:

```powershell
.\tools\build.ps1 -Install -GameRoot 'E:\Games\World of Tanks'
```

The installer backs up an existing HCP package before replacement. It preserves the user's live `hangar_carousel_plus.json`; `tools/install.ps1 -ForceConfig` is the explicit opt-in for replacing that configuration with the repository default.

## Pre-release compatibility builds

Build a candidate against a reconstructed or separate client tree:

```powershell
.\tools\build.ps1 -GameRoot '<staged-client-root>' -PreviewVersion '0.8.15-rc.1'
```

This writes generated metadata, Python bytecode, native patches, standalone mod, complete dependency ZIP, and checksums into separate paths:

```text
build\preview\<client-version>\0.8.15-rc.1\
dist\preview\<client-version>\0.8.15-rc.1\
```

Tracked `meta.xml`, runtime source version, README download links, and stable artifacts are unchanged. Preview builds reject `-Install`; profiles marked `previewOnly` also reject stable builds. `-OutputDirectory` may redirect artifacts but cannot target the stable `dist` root or `releases` tree for a preview. Do not distribute a candidate built against one client profile as a package for another profile.

On the release day, re-run against the actual updated client: any changed native source or guarded Python contract stops the build. Run the in-game smoke tests before removing `previewOnly` from the reviewed profile and updating stable version metadata.

## Build pipeline

`tools/build.ps1` performs the following operations:

1. runs the Python 2.7 automatic-row behavioral tests;
2. compiles `src/python/mod_hangar_carousel_plus.py` with Python 2.7;
3. stages the Python, Gameface, configuration, metadata, and localization resources;
4. extracts and patches checksum-verified carousel and tooltip resources from the local client;
5. packages the staging tree as a `.wotmod` file;
6. runs `tools/validate.ps1` against the completed package;
7. creates and validates a complete ZIP from checksum-pinned files in `dependencies/`;
8. optionally installs the standalone package into the selected game client.

`tools/patch-native-carousel.ps1` generalizes the standard hangar's hard-coded row-pair logic so the provider can render one through four rows. `tools/patch-native-event-carousels.ps1` applies the same contract to the separate Comp7, Comp7 Light, Frontline, Fun Random, and Last Stand Gameface namespaces. Battle Royale uses a different provider API and is deliberately not patched. `tools/patch-native-tooltip.ps1` adds the HCP statistics renderer and styles to the root vehicle tooltip, which is outside the OpenWG subview injector. Every native patch verifies the source resource hash and the exact number of substitutions.

The Python bridge publishes configuration, localized strings, filter state, vehicle statistics, sorting data, and row state to Gameface. HCP narrows the native vehicle model before the normal client filters run; it does not create dynamic vehicle playlists. See [docs/architecture.md](docs/architecture.md) for the component-level design.

## Configuration and runtime state

The repository default is `config/default.json`. The installed user configuration is:

```text
<game>\mods\configs\RCooLeR\hangar_carousel_plus.json
```

Sorting direction, last-played timestamps, and carousel row mode are stored in `hangar_carousel_plus.runtime.json` next to the live configuration. Changes to the configuration schema must preserve or migrate existing user values, because normal installation deliberately does not overwrite this file. Version 0.8.9 also reads and migrates the legacy files from `res_mods\configs\hangar_carousel_plus`.

## Validation

The build runs the Python API guard tests and automatic-row coordinator tests. When Node.js is available, it additionally syntax-checks all six patched carousel bundles and the tooltip bundle, executes 864 row-chunking cases, and checks automatic thresholds, sorting direction/ties, keyboard patch markers, and required DOM anchors. Node.js is recommended for release preparation; its absence produces an explicit warning rather than silently implying those tests passed.

The build-profile negative tests can be run separately:

```powershell
.\tests\test_build_profiles.ps1
```

The normal build already invokes the package validator. To validate an existing artifact separately:

```powershell
.\tools\validate.ps1 -PackagePath '.\dist\com.rcooler.hangar_carousel_plus_0.8.14.wotmod'
```

After a client update:

1. confirm the client version and active `mods` directory;
2. rebuild against the new local client resources;
3. update the guarded source hashes and exact substitutions only after reviewing the changed bundles;
4. test every filter, sort mode, card statistic, hover statistic, row mode, action-card option, settings page, and language fallback;
5. update the supported version in documentation and release artifacts.

## Release packaging

User releases live under `releases/<version>/`. A complete release must include:

- the standalone HCP `.wotmod` file;
- a ZIP rooted at the standard `mods/<client-version>/` directory;
- the HCP runtime dependencies (`net.openwg.gameface`, ModsListAPI, and ModsSettingsAPI);
- `SHA256SUMS.txt` for published artifacts;
- `THIRD_PARTY.md` with dependency names, versions, sources, and licenses.

Update both user README download links, the changelog, package metadata, and artifact names when the mod version changes. Commit generated public release artifacts intentionally and tag the exact published commit.
