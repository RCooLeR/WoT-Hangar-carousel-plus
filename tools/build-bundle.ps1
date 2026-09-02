[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$GameRoot,
    [Parameter(Mandatory = $true)]
    [string]$PackagePath,
    [string]$DependencyRoot,
    [string]$BuildDirectory,
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$GameRoot = [IO.Path]::GetFullPath($GameRoot)
$PackagePath = [IO.Path]::GetFullPath($PackagePath)
if (-not $DependencyRoot) {
    $DependencyRoot = Join-Path $repo 'dependencies'
}
$DependencyRoot = [IO.Path]::GetFullPath($DependencyRoot)

if (-not (Test-Path -LiteralPath $PackagePath)) {
    throw "HCP package not found: $PackagePath"
}

[xml]$versionData = Get-Content -LiteralPath (Join-Path $GameRoot 'version.xml') -Raw
$clientVersionMatch = [regex]::Match([string]$versionData.DocumentElement.version, '\d+\.\d+\.\d+\.\d+')
if (-not $clientVersionMatch.Success) {
    throw 'Unable to determine the active World of Tanks client version.'
}
$clientVersion = $clientVersionMatch.Value

$manifestPath = Join-Path $DependencyRoot 'manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if (-not $manifest.dependencies -or $manifest.dependencies.Count -lt 1) {
    throw "No dependencies declared in $manifestPath"
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Read-WotmodMetadata([string]$Path) {
    $archive = [IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $entry = $archive.GetEntry('meta.xml')
        if (-not $entry) {
            throw "meta.xml is missing from $Path"
        }
        $reader = New-Object IO.StreamReader($entry.Open(), [Text.Encoding]::UTF8)
        try {
            return [xml]$reader.ReadToEnd()
        }
        finally {
            $reader.Dispose()
        }
    }
    finally {
        $archive.Dispose()
    }
}

[xml]$meta = Read-WotmodMetadata $PackagePath
$modVersion = [string]$meta.DocumentElement.version
if ($modVersion -notmatch '^\d+\.\d+\.\d+(?:-rc\.\d+)?$') {
    throw 'Invalid HCP package version.'
}
if (-not $BuildDirectory) { $BuildDirectory = Join-Path $repo 'build' }
$BuildDirectory = [IO.Path]::GetFullPath($BuildDirectory)
$stage = Join-Path $BuildDirectory "bundle-$modVersion"
if (-not $stage.StartsWith((Join-Path $repo 'build') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Bundle staging must remain inside the repository build directory.'
}
$modsDir = Join-Path $stage "mods\$clientVersion"
$dist = if ($OutputDirectory) { [IO.Path]::GetFullPath($OutputDirectory) } else { Split-Path -Parent $PackagePath }
if ($modVersion.Contains('-rc.') -and (
        $dist -eq (Join-Path $repo 'dist') -or
        $dist -eq (Join-Path $repo 'releases') -or
        $dist.StartsWith((Join-Path $repo 'releases') + '\', [StringComparison]::OrdinalIgnoreCase))) {
    throw 'Preview bundles must not overwrite stable dist or release directories.'
}
$bundleName = "Hangar_Carousel_Plus_${modVersion}_complete.zip"
$bundlePath = Join-Path $dist $bundleName
$checksumsPath = Join-Path $dist 'SHA256SUMS.txt'

Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $modsDir, $dist | Out-Null

$hcpDestination = Join-Path $modsDir ([IO.Path]::GetFileName($PackagePath))
Copy-Item -LiteralPath $PackagePath -Destination $hcpDestination

$expectedEntries = New-Object Collections.Generic.List[string]
$expectedEntries.Add(("mods/{0}/{1}" -f $clientVersion, [IO.Path]::GetFileName($PackagePath)))
foreach ($dependency in $manifest.dependencies) {
    $relativePath = ([string]$dependency.path).Replace('/', [IO.Path]::DirectorySeparatorChar)
    $source = Join-Path $DependencyRoot $relativePath
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Pinned dependency is missing: $source"
    }
    $actualHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    if ($actualHash -ne [string]$dependency.sha256) {
        throw "Dependency checksum mismatch for ${relativePath}: $actualHash"
    }
    $dependencyMeta = Read-WotmodMetadata $source
    if ([string]$dependencyMeta.DocumentElement.id -ne [string]$dependency.id -or
        [string]$dependencyMeta.DocumentElement.version -ne [string]$dependency.version) {
        throw "Dependency metadata mismatch for $relativePath"
    }
    $destination = Join-Path $modsDir $relativePath
    New-Item -ItemType Directory -Force -Path ([IO.Path]::GetDirectoryName($destination)) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination
    $expectedEntries.Add(("mods/{0}/{1}" -f $clientVersion, ([string]$dependency.path).Replace('\', '/')))
}

Remove-Item -LiteralPath $bundlePath -Force -ErrorAction SilentlyContinue
[IO.Compression.ZipFile]::CreateFromDirectory($stage, $bundlePath, [IO.Compression.CompressionLevel]::Optimal, $false)

$archive = [IO.Compression.ZipFile]::OpenRead($bundlePath)
try {
    $actualEntries = @($archive.Entries | Where-Object { -not [string]::IsNullOrWhiteSpace($_.Name) } | ForEach-Object { $_.FullName.Replace('\', '/') })
    foreach ($entry in $expectedEntries) {
        if ($entry -notin $actualEntries) {
            throw "Complete bundle is missing: $entry"
        }
    }
    if ($actualEntries.Count -ne $expectedEntries.Count) {
        throw "Complete bundle contains unexpected files: expected $($expectedEntries.Count), found $($actualEntries.Count)"
    }
    if ($actualEntries | Where-Object { $_ -like 'mods/configs/*' -or $_ -like 'res_mods/*' }) {
        throw 'Complete bundle must not overwrite user configuration or legacy res_mods data.'
    }
}
finally {
    $archive.Dispose()
}

$checksumLines = New-Object Collections.Generic.List[string]
$checksumLines.Add(('{0}  {1}' -f (Get-FileHash -LiteralPath $PackagePath -Algorithm SHA256).Hash, [IO.Path]::GetFileName($PackagePath)))
$checksumLines.Add(('{0}  {1}' -f (Get-FileHash -LiteralPath $bundlePath -Algorithm SHA256).Hash, $bundleName))
foreach ($entry in $expectedEntries) {
    $localPath = Join-Path $stage $entry.Replace('/', [IO.Path]::DirectorySeparatorChar)
    $checksumLines.Add(('{0}  {1}' -f (Get-FileHash -LiteralPath $localPath -Algorithm SHA256).Hash, $entry))
}
[IO.File]::WriteAllLines($checksumsPath, $checksumLines, (New-Object Text.UTF8Encoding($false)))
Copy-Item -LiteralPath (Join-Path $DependencyRoot 'THIRD_PARTY.md') -Destination (Join-Path $dist 'THIRD_PARTY.md') -Force

Write-Output $bundlePath
