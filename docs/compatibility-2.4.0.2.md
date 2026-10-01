# WoT EU 2.4.0.2 #956 compatibility

Client revision 2626510, overrides 2629859. Reviewed against the previously released 0.8.16 patched resources.

- Main carousel: rebuilt imports/local aliases and native intro-overlay CSS identifiers; guarded row, filter and sort expressions remain compatible.
- Comp7 Light and Frontline: updated native imports.
- Comp7 and Last Stand: updated native imports and corresponding references.
- Tooltip: rebuilt aliases and component references; the appended renderer and required DOM anchors remain valid.
- Fun Random and tooltip CSS are byte-identical to 2.4.0.1.
- All 10 existing private Python API fingerprints pass without relaxing the contract.
- All 29 Python tests, six native carousel checks (864 row cases), tooltip checks and package checks pass.

Source hashes are recorded in tools/client-profiles.json. The user confirmed initial gameplay works. Log review identified a settings-template version mismatch, fixed by upgrading to template version 3 while seeding current config/runtime values. The corrected package is installed. The fresh 2026-10-01 session (12:45:49–12:53:52 Europe/Kiev) confirms HCP 0.8.17 initialization, successful ModsSettingsAPI registration, and carousel data for 394 vehicles, with no HCP warnings or errors. Installed, standalone and complete-bundle HCP packages match the release checksums. Unrelated client and third-party resource errors remain in the overall game log; this validation does not claim that the entire client is warning-free.
