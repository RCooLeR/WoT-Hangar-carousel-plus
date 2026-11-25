[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$scratchRoot = Join-Path $repo 'build\profile-tests'
$scratch = Join-Path $scratchRoot ([guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path (Join-Path $scratch 'res\packages') | Out-Null
. (Join-Path $repo 'tools\client-profile.ps1')

function Expect-Failure([scriptblock]$Action, [string]$Expected) {
    $failure = $null
    try { & $Action | Out-Null } catch { $failure = $_.Exception.Message }
    if (-not $failure -or $failure -notlike "*$Expected*") {
        throw "Expected failure containing '$Expected', got '$failure'."
    }
    Write-Output "PASS rejected: $Expected"
}

try {
    [IO.File]::WriteAllText((Join-Path $scratch 'version.xml'), '<root><version>9.9.9.9 #1</version></root>')
    Expect-Failure { Get-HcpClientProfile -GameRoot $scratch } 'No reviewed HCP resource profile'
    [IO.File]::WriteAllText((Join-Path $scratch 'version.xml'), '<root><version>2.4.0.0 #930</version></root>')
    Expect-Failure { & (Join-Path $repo 'tools\build.ps1') -GameRoot $scratch -PreviewVersion '0.8.15-rc.1' -Install } 'Preview builds cannot be installed'
    Expect-Failure { & (Join-Path $repo 'tools\build.ps1') -GameRoot $scratch -PreviewVersion '0.8.15-rc.1' -OutputDirectory (Join-Path $repo 'dist') } 'must not overwrite stable'
    Expect-Failure { & (Join-Path $repo 'tools\build.ps1') -GameRoot $scratch -PreviewVersion '0.8.15-rc.1' -OutputDirectory (Join-Path $repo 'releases\0.8.14') } 'must not overwrite stable'

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::Open((Join-Path $scratch 'res\packages\gui-part3.pkg'), [IO.Compression.ZipArchiveMode]::Create)
    try {
        $entry = $zip.CreateEntry('gui/gameface/_dist/production/mono/hangar/views/main/main.html/bundle.js')
        $writer = New-Object IO.StreamWriter($entry.Open())
        try { $writer.Write('unsupported client source') } finally { $writer.Dispose() }
    }
    finally { $zip.Dispose() }
    Expect-Failure { & (Join-Path $repo 'tools\patch-native-carousel.ps1') -GameRoot $scratch -OutputPath (Join-Path $scratch 'patched.js') } 'Unsupported standard hangar bundle'
    if (Test-Path -LiteralPath (Join-Path $scratch 'patched.js')) {
        throw 'Unreviewed source unexpectedly produced a patched output.'
    }
    [IO.File]::WriteAllText((Join-Path $scratch 'version.xml'), '<root><version>2.4.1.0 #974</version></root>')
    $zip = [IO.Compression.ZipFile]::Open((Join-Path $scratch 'res/packages/gui-part2.pkg'), [IO.Compression.ZipArchiveMode]::Create)
    try {
        $entry = $zip.CreateEntry('gui/gameface/_dist/production/mono/hangar/main/bundle.js')
        $writer = New-Object IO.StreamWriter($entry.Open())
        try { $writer.Write('unsupported relocated client source') } finally { $writer.Dispose() }
    }
    finally { $zip.Dispose() }
    Expect-Failure { & (Join-Path $repo 'tools/patch-native-carousel.ps1') -GameRoot $scratch -OutputPath (Join-Path $scratch 'patched.js') } 'Unsupported standard hangar bundle'
    if (Test-Path -LiteralPath (Join-Path $scratch 'patched.js')) {
        throw 'Unreviewed relocated source unexpectedly produced a patched output.'
    }
    [IO.File]::WriteAllText((Join-Path $scratch 'version.xml'), '<root><version>2.4.1.1 #993</version></root>')
    Expect-Failure { & (Join-Path $repo 'tools/patch-native-carousel.ps1') -GameRoot $scratch -OutputPath (Join-Path $scratch 'patched.js') } 'Unsupported standard hangar bundle'
    if (Test-Path -LiteralPath (Join-Path $scratch 'patched.js')) {
        throw 'Unreviewed 2.4.1.1 source unexpectedly produced a patched output.'
    }
    Expect-Failure { & (Join-Path $repo 'tools/build.ps1') -GameRoot $scratch } 'prerelease-only'
    [IO.File]::WriteAllText((Join-Path $scratch 'version.xml'), '<root><version>2.4.2.0 #1000</version></root>')
    Expect-Failure { & (Join-Path $repo 'tools/patch-native-carousel.ps1') -GameRoot $scratch -OutputPath (Join-Path $scratch 'patched.js') } 'Unsupported standard hangar bundle'
    if (Test-Path -LiteralPath (Join-Path $scratch 'patched.js')) {
        throw 'Unreviewed 2.4.2.0 source unexpectedly produced a patched output.'
    }
    $packagePath = Join-Path $scratch 'stale-event.wotmod'
    $zip = [IO.Compression.ZipFile]::Open($packagePath, [IO.Compression.ZipArchiveMode]::Create)
    try {
        [void]$zip.CreateEntry('res/fort_rush/gui/gameface/_dist/production/mono/lobby/hangar/bundle.js')
    }
    finally { $zip.Dispose() }
    Expect-Failure { & (Join-Path $repo 'tools/validate.ps1') -PackagePath $packagePath -GameRoot $scratch } 'Unexpected Black Signal resources'
    Write-Output 'Passed 10 build-profile safety checks.'
}
finally {
    $resolved = (Resolve-Path -LiteralPath $scratch).Path
    if (-not $resolved.StartsWith($scratchRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Refusing to clean a test directory outside the profile-tests root.'
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
