# World of Tanks 2.4.2.0 compatibility

HCP 0.8.20 targets the Wargaming EU 2.4.2.0 #1000 client. Native carousel
and tooltip resources are rebuilt from the installed client and checked
against exact hashes in `tools/client-profiles.json`.

The filter-provider class has a new bytecode fingerprint. The wrapped
lifecycle and vehicle-list methods retain their existing contracts; the
other nine guarded Python interfaces are unchanged.

This client no longer contains the Black Signal `fort_rush.pkg` package.
Its lobby integration is omitted for this profile. The standard, Comp7,
Comp7 Light, Frontline, Fun Random and Last Stand carousels remain included.
Older profiles that declare `fort_rush` still require its integration.

The package uses the existing configuration schema and preserves user
settings. Build with `tools/build.ps1 -GameRoot '<WoT root>'`.
