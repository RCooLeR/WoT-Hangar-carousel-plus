[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$GameRoot,
    [Parameter(Mandatory = $true)]
    [string]$BundleOutputPath,
    [Parameter(Mandatory = $true)]
    [string]$CssOutputPath,
    [Parameter(Mandatory = $true)]
    [string]$I18nPath,
    [Parameter(Mandatory = $true)]
    [string]$ScriptPath,
    [Parameter(Mandatory = $true)]
    [string]$StylePath
)

$ErrorActionPreference = 'Stop'
$GameRoot = [IO.Path]::GetFullPath($GameRoot)
$BundleOutputPath = [IO.Path]::GetFullPath($BundleOutputPath)
$CssOutputPath = [IO.Path]::GetFullPath($CssOutputPath)
. (Join-Path $PSScriptRoot 'client-profile.ps1')
$profile = Get-HcpClientProfile -GameRoot $GameRoot
$bundlePackagePath = Join-Path $GameRoot 'res\packages\gui-part4.pkg'
$cssPackagePath = Join-Path $GameRoot 'res\packages\gui-part2.pkg'
$bundleEntryPath = 'gui/gameface/_dist/production/mono/hangar/views/vehicle_tooltip/vehicle_tooltip.html/bundle.js'
$cssEntryPath = 'gui/gameface/_dist/production/mono/hangar/vehicle_tooltip/vehicle_tooltip.css'
$expectedBundleHash = $profile.Hashes.tooltip
$expectedCssHash = $profile.Hashes.tooltipCss

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Read-ZipEntryBytes([string]$packagePath, [string]$entryPath) {
    $zip = [IO.Compression.ZipFile]::OpenRead($packagePath)
    try {
        $entry = $zip.GetEntry($entryPath)
        if (-not $entry) {
            throw "Native tooltip resource is missing: $entryPath"
        }
        $stream = $entry.Open()
        $memory = New-Object IO.MemoryStream
        try {
            $stream.CopyTo($memory)
            return $memory.ToArray()
        }
        finally {
            $memory.Dispose()
            $stream.Dispose()
        }
    }
    finally {
        $zip.Dispose()
    }
}

function Get-BytesHash([byte[]]$bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return (($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('X2') }) -join '')
    }
    finally {
        $sha.Dispose()
    }
}

$bundleBytes = Read-ZipEntryBytes $bundlePackagePath $bundleEntryPath
$cssBytes = Read-ZipEntryBytes $cssPackagePath $cssEntryPath
$bundleHash = Get-BytesHash $bundleBytes
$cssHash = Get-BytesHash $cssBytes
if ($bundleHash -ne $expectedBundleHash) {
    throw "Unsupported native tooltip bundle $bundleHash; expected $expectedBundleHash"
}
if ($cssHash -ne $expectedCssHash) {
    throw "Unsupported native tooltip stylesheet $cssHash; expected $expectedCssHash"
}

$utf8 = New-Object Text.UTF8Encoding($false)
$bundle = [Text.Encoding]::UTF8.GetString($bundleBytes)
$bundle += "`n/* Hangar Carousel Plus tooltip localization */`n"
$bundle += [IO.File]::ReadAllText([IO.Path]::GetFullPath($I18nPath), [Text.Encoding]::UTF8)
$bundle += "`n/* Hangar Carousel Plus tooltip renderer */`n"
$bundle += [IO.File]::ReadAllText([IO.Path]::GetFullPath($ScriptPath), [Text.Encoding]::UTF8)

$css = [Text.Encoding]::UTF8.GetString($cssBytes)
$css += "`n/* Hangar Carousel Plus tooltip styles */`n"
$css += [IO.File]::ReadAllText([IO.Path]::GetFullPath($StylePath), [Text.Encoding]::UTF8)

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BundleOutputPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $CssOutputPath) | Out-Null
[IO.File]::WriteAllText($BundleOutputPath, $bundle, $utf8)
[IO.File]::WriteAllText($CssOutputPath, $css, $utf8)
Write-Output "Patched native tooltip bundle: $BundleOutputPath"
Write-Output "Patched native tooltip stylesheet: $CssOutputPath"
