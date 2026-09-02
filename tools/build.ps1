[CmdletBinding()]
param(
    [string]$Python27,
    [switch]$Install,
    [string]$GameRoot = 'E:\Games\steamapps\common\World of Tanks\ru',
    [string]$PreviewVersion,
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
. (Join-Path $PSScriptRoot 'client-profile.ps1')
$profile = Get-HcpClientProfile -GameRoot $GameRoot
$build = Join-Path $repo 'build'
$dist = Join-Path $repo 'dist'
[xml]$meta = Get-Content -LiteralPath (Join-Path $repo 'meta.xml') -Raw
$version = [string]$meta.DocumentElement.version
if ([string]::IsNullOrWhiteSpace($version)) {
    throw 'The mod version is missing from meta.xml.'
}
$sourceVersion = $version
if ($profile.Hashes.previewOnly -and -not $PreviewVersion) {
    throw "Client $($profile.Version) is prerelease-only; use -PreviewVersion so stable artifacts remain untouched."
}
if ($PreviewVersion) {
    if ($Install) { throw 'Preview builds cannot be installed by this command.' }
    if ($PreviewVersion -notmatch '^\d+\.\d+\.\d+-rc\.\d+$') {
        throw 'PreviewVersion must be a release candidate such as 0.8.15-rc.1.'
    }
    $version = $PreviewVersion
    $meta.DocumentElement.version = $version
    $build = Join-Path $build ("preview\$($profile.Version)\$version")
    $dist = Join-Path $dist ("preview\$($profile.Version)\$version")
}
if ($OutputDirectory) { $dist = [IO.Path]::GetFullPath($OutputDirectory) }
if ($PreviewVersion -and (
        $dist -eq (Join-Path $repo 'dist') -or
        $dist -eq (Join-Path $repo 'releases') -or
        $dist.StartsWith((Join-Path $repo 'releases') + '\', [StringComparison]::OrdinalIgnoreCase))) {
    throw 'Preview output must not overwrite stable dist or release directories.'
}
$stage = Join-Path $build 'stage'
if (-not [IO.Path]::GetFullPath($stage).StartsWith((Join-Path $repo 'build') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Build staging must remain inside the repository build directory.'
}
$packageName = "com.rcooler.hangar_carousel_plus_$version.wotmod"
$packagePath = Join-Path $dist $packageName

if (-not $Python27) {
    $Python27 = & (Join-Path $PSScriptRoot 'bootstrap-python27.ps1')
}
$Python27 = [IO.Path]::GetFullPath(($Python27 | Select-Object -Last 1))
if (-not (Test-Path -LiteralPath $Python27)) {
    throw "Python 2.7 not found: $Python27"
}
& $Python27 (Join-Path $repo 'tools\check-client-api.py') --game-root $GameRoot
if ($LASTEXITCODE -ne 0) { throw 'Client Python API compatibility check failed.' }
& $Python27 (Join-Path $repo 'tests\test_client_api.py')
if ($LASTEXITCODE -ne 0) { throw 'Client API guard tests failed.' }

Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path `
    (Join-Path $stage 'res\scripts\client\gui\mods'), `
    (Join-Path $stage 'res\gui\gameface\mods\rcooler\hangar_carousel_plus'), `
    (Join-Path $stage 'res\gui\gameface\_dist\production\mono\hangar\views\main\main.html'), `
    (Join-Path $stage 'res\gui\gameface\_dist\production\mono\hangar\views\vehicle_tooltip\vehicle_tooltip.html'), `
    (Join-Path $stage 'res\gui\gameface\_dist\production\mono\hangar\vehicle_tooltip'), `
    $dist | Out-Null

$pythonSource = Join-Path $repo 'src\python\mod_hangar_carousel_plus.py'
$pythonText = Get-Content -LiteralPath $pythonSource -Raw
if (-not $pythonText.Contains("MOD_VERSION = '$sourceVersion'")) {
    throw "Python MOD_VERSION does not match meta.xml version $sourceVersion."
}
if ($pythonText.Contains('.createPlaylist(')) {
    throw 'HCP filters must not create dynamic vehicle playlists.'
}
if ($pythonText.Contains('StatsRequester') -or
    $pythonText.Contains('onToggleCurrencyLock') -or
    $pythonText.Contains('def _patch_currency_locks')) {
    throw 'HCP must remain carousel-focused and must not patch currencies.'
}
if (-not $pythonText.Contains("'priority'") -or
    -not $pythonText.Contains("'battlePassPoints'") -or
    -not $pythonText.Contains('getVehicleProgression') -or
    -not $pythonText.Contains('VEHICLE_DATA_CACHE') -or
    -not $pythonText.Contains('def _invalidate_vehicle_data')) {
    throw 'Sorting modes or the vehicle-data cache are missing.'
}
if (-not $pythonText.Contains('AUTO_ROWS_DEBOUNCE_SECONDS') -or
    -not $pythonText.Contains('AUTO_ROWS_REARM_SERIAL') -or
    -not $pythonText.Contains('def _request_automatic_carousel_rows') -or
    -not $pythonText.Contains('def _register_filter_provider') -or
    -not $pythonText.Contains('def _rearm_filter_provider') -or
    -not $pythonText.Contains('provider is not ACTIVE_FILTER_PROVIDER') -or
    -not $pythonText.Contains('def _apply_rows_to_providers') -or
    -not $pythonText.Contains('if rows <= 0 or not _carousel_auto()')) {
    throw 'Stable automatic-row scheduling or no-op provider updates are missing.'
}
& $Python27 (Join-Path $repo 'tests\test_auto_rows.py') $pythonSource
if ($LASTEXITCODE -ne 0) {
    throw 'Automatic carousel-row behavioral tests failed.'
}
if ($PreviewVersion) {
    $pythonText = $pythonText.Replace("MOD_VERSION = '$sourceVersion'", "MOD_VERSION = '$version'")
}
$compiledSource = Join-Path $build 'mod_hangar_carousel_plus.py'
[IO.File]::WriteAllText($compiledSource, $pythonText, (New-Object Text.UTF8Encoding($false)))
& $Python27 -m py_compile $compiledSource
if ($LASTEXITCODE -ne 0) {
    throw 'Python 2.7 compilation failed.'
}
$compiled = "$compiledSource`c"

$meta.Save((Join-Path $stage 'meta.xml'))
Copy-Item -LiteralPath $compiled -Destination (Join-Path $stage 'res\scripts\client\gui\mods\mod_hangar_carousel_plus.pyc')
Copy-Item -LiteralPath (Join-Path $repo 'src\gameface\hangar_carousel_plus.js') `
    -Destination (Join-Path $stage 'res\gui\gameface\mods\rcooler\hangar_carousel_plus\hangar_carousel_plus.js')
Copy-Item -LiteralPath (Join-Path $repo 'src\gameface\hangar_carousel_plus.i18n.js') `
    -Destination (Join-Path $stage 'res\gui\gameface\mods\rcooler\hangar_carousel_plus\hangar_carousel_plus.i18n.js')
Copy-Item -LiteralPath (Join-Path $repo 'src\gameface\hangar_carousel_plus.css') `
    -Destination (Join-Path $stage 'res\gui\gameface\mods\rcooler\hangar_carousel_plus\hangar_carousel_plus.css')
Copy-Item -LiteralPath (Join-Path $repo 'src\gameface\hangar_carousel_plus.tooltip.js') `
    -Destination (Join-Path $stage 'res\gui\gameface\mods\rcooler\hangar_carousel_plus\hangar_carousel_plus.tooltip.js')
Copy-Item -LiteralPath (Join-Path $repo 'src\gameface\hangar_carousel_plus.tooltip.css') `
    -Destination (Join-Path $stage 'res\gui\gameface\mods\rcooler\hangar_carousel_plus\hangar_carousel_plus.tooltip.css')
& (Join-Path $PSScriptRoot 'patch-native-carousel.ps1') `
    -GameRoot $GameRoot `
    -OutputPath (Join-Path $stage 'res\gui\gameface\_dist\production\mono\hangar\views\main\main.html\bundle.js')
& (Join-Path $PSScriptRoot 'patch-native-event-carousels.ps1') `
    -GameRoot $GameRoot `
    -OutputRoot (Join-Path $stage 'res')
& (Join-Path $PSScriptRoot 'patch-native-tooltip.ps1') `
    -GameRoot $GameRoot `
    -BundleOutputPath (Join-Path $stage 'res\gui\gameface\_dist\production\mono\hangar\views\vehicle_tooltip\vehicle_tooltip.html\bundle.js') `
    -CssOutputPath (Join-Path $stage 'res\gui\gameface\_dist\production\mono\hangar\vehicle_tooltip\vehicle_tooltip.css') `
    -I18nPath (Join-Path $repo 'src\gameface\hangar_carousel_plus.i18n.js') `
    -ScriptPath (Join-Path $repo 'src\gameface\hangar_carousel_plus.tooltip.js') `
    -StylePath (Join-Path $repo 'src\gameface\hangar_carousel_plus.tooltip.css')

$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    & $node.Source (Join-Path $repo 'tests\test_native_carousels.js') $stage
    if ($LASTEXITCODE -ne 0) { throw 'Native carousel behavioral tests failed.' }
}
else {
    Write-Warning 'Node.js not found; native JavaScript behavioral and syntax tests were skipped.'
}

Remove-Item -LiteralPath $packagePath -Force -ErrorAction SilentlyContinue
& $Python27 (Join-Path $PSScriptRoot 'package_wotmod.py') $stage $packagePath
if ($LASTEXITCODE -ne 0) {
    throw 'WoT package creation failed.'
}

& (Join-Path $PSScriptRoot 'validate.ps1') -PackagePath $packagePath
$bundlePath = & (Join-Path $PSScriptRoot 'build-bundle.ps1') `
    -GameRoot $GameRoot `
    -PackagePath $packagePath `
    -BuildDirectory $build `
    -OutputDirectory $dist
if ($Install) {
    & (Join-Path $PSScriptRoot 'install.ps1') -GameRoot $GameRoot -PackagePath $packagePath
}

Write-Output $packagePath
Write-Output $bundlePath
