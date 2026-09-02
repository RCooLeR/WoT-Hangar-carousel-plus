[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$GameRoot,
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,
    [string]$StandardOutputPath
)

$ErrorActionPreference = 'Stop'
$GameRoot = [IO.Path]::GetFullPath($GameRoot)
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
. (Join-Path $PSScriptRoot 'client-profile.ps1')
$profile = Get-HcpClientProfile -GameRoot $GameRoot

$bundles = @(
    @{
        Name = 'Comp7 Light'
        Package = 'comp7_light.pkg'
        Entry = 'comp7_light/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js'
        RootKind = 'standard'
        NativeChangerCount = 1
    },
    @{
        Name = 'Comp7'
        Package = 'comp7.pkg'
        Entry = 'comp7/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js'
        RootKind = 'standard'
        NativeChangerCount = 1
    },
    @{
        Name = 'Frontline'
        Package = 'frontline.pkg'
        Entry = 'frontline/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js'
        RootKind = 'standard'
        NativeChangerCount = 1
    },
    @{
        Name = 'Fun Random'
        Package = 'fun_random.pkg'
        Entry = 'fun_random/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js'
        RootKind = 'standard'
        NativeChangerCount = 1
    },
    @{
        Name = 'Last Stand'
        Package = 'last_stand.pkg'
        Entry = 'last_stand/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js'
        RootKind = 'lastStand'
        NativeChangerCount = 2
    }
)

if ($StandardOutputPath) {
    $StandardOutputPath = [IO.Path]::GetFullPath($StandardOutputPath)
    $bundles = @(@{
        Name = 'standard'
        Package = 'gui-part3.pkg'
        Entry = 'gui/gameface/_dist/production/mono/hangar/views/main/main.html/bundle.js'
        RootKind = 'standard'
        NativeChangerCount = 1
        ProfileKey = 'main'
    })
}
foreach ($bundle in $bundles) {
    $key = if ($bundle.ProfileKey) { $bundle.ProfileKey } else { [IO.Path]::GetFileNameWithoutExtension($bundle.Package) }
    $bundle.Hash = $profile.Hashes.PSObject.Properties[$key].Value
    if (-not $bundle.Hash) { throw "Missing source hash for $key in $($profile.Version)." }
}

function Replace-RegexExact {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [string]$Pattern,
        [Parameter(Mandatory = $true)]
        [scriptblock]$ReplacementFactory,
        [Parameter(Mandatory = $true)]
        [string]$Description,
        [int]$ExpectedCount = 1
    )

    $regex = New-Object Text.RegularExpressions.Regex($Pattern)
    $matches = $regex.Matches($Source)
    if ($matches.Count -ne $ExpectedCount) {
        throw "Expected $ExpectedCount $Description patch point(s), found $($matches.Count)."
    }
    for ($index = $matches.Count - 1; $index -ge 0; $index--) {
        $match = $matches[$index]
        $replacement = [string](& $ReplacementFactory $match)
        $Source = $Source.Remove($match.Index, $match.Length).Insert($match.Index, $replacement)
    }
    return $Source
}

function Read-PackageEntry {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PackagePath,
        [Parameter(Mandatory = $true)]
        [string]$EntryPath
    )

    $zip = [IO.Compression.ZipFile]::OpenRead($PackagePath)
    try {
        $entry = $zip.GetEntry($EntryPath)
        if (-not $entry) {
            throw "Native event hangar bundle is missing: $EntryPath"
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

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

foreach ($bundle in $bundles) {
    $packagePath = Join-Path (Join-Path $GameRoot 'res\packages') $bundle.Package
    $sourceBytes = Read-PackageEntry -PackagePath $packagePath -EntryPath $bundle.Entry
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $sourceHash = (($sha.ComputeHash($sourceBytes) | ForEach-Object { $_.ToString('X2') }) -join '')
    }
    finally {
        $sha.Dispose()
    }
    if ($sourceHash -ne $bundle.Hash) {
        throw "Unsupported $($bundle.Name) hangar bundle $sourceHash; expected WoT $($profile.Version) bundle $($bundle.Hash)."
    }

    $source = [Text.Encoding]::UTF8.GetString($sourceBytes)
    if ($source.Contains('hcpCarouselAuto') -or $source.Contains('hcpSortJson')) {
        throw "$($bundle.Name) source bundle is already patched."
    }

    $defaultVariable = $null
    $source = Replace-RegexExact $source `
        '(?<defaults>[A-Za-z_$][\w$]*)=\{\.\.\.(?<observable>[A-Za-z_$][\w$]*)\.primitives\(\["defaultFilters"\]\)\}' `
        {
            param($match)
            $script:defaultVariable = $match.Groups['defaults'].Value
            return $script:defaultVariable + '={...' + $match.Groups['observable'].Value +
                '.primitives(["defaultFilters","hcpCarouselAuto","hcpSortJson"])}'
        } `
        "$($bundle.Name) filter-model property"
    $defaultVariable = $script:defaultVariable

    $source = Replace-RegexExact $source `
        'primitives\(\["carouselRowCount"\]\),filters:' `
        {
            param($match)
            return 'primitives(["carouselRowCount"]),hcpCarouselAuto:' + $defaultVariable +
                '.hcpCarouselAuto,hcpSortJson:' + $defaultVariable + '.hcpSortJson,filters:'
        } `
        "$($bundle.Name) filter-model export"

    $source = Replace-RegexExact $source `
        '(?<list>[A-Za-z_$][\w$]*)=(?<expr>\([^;]*?\)\.filter\([^;]*?(?<context>[A-Za-z_$][\w$]*)\.requires\.statistic\.model\.get\([^;]*?\)\));(?<commit>[A-Za-z_$][\w$]*\(\(\)=>[A-Za-z_$][\w$]*\.set\(\k<list>\)\))' `
        {
            param($match)
            $list = $match.Groups['list'].Value
            return $list + '=' + $match.Groups['expr'].Value +
                ';const hcp=(()=>{try{return JSON.parse(' + $match.Groups['context'].Value +
                '.requires.filters.model.hcpSortJson.get())}catch(e){return{}}})();' +
                'hcp.mode&&"default"!==hcp.mode&&hcp.values&&' + $list +
                '.sort((e,t)=>{const a=Number(hcp.values[e.id]??0),s=Number(hcp.values[t.id]??0);' +
                'return a===s?0:(hcp.descending?-1:1)*(a-s)}),' + $match.Groups['commit'].Value
        } `
        "$($bundle.Name) final-list sorting"

    $source = Replace-RegexExact $source `
        'carouselTypeChange:(?<external>[A-Za-z_$][\w$]*)\.createCallback\((?<argument>[A-Za-z_$][\w$]*)=>\(\{rowCount:\k<argument>\}\),"onCarouselTypeChange"\)' `
        {
            param($match)
            $argument = $match.Groups['argument'].Value
            return 'carouselTypeChange:' + $match.Groups['external'].Value + '.createCallback(' +
                $argument + '=>"object"==typeof ' + $argument + '?' + $argument +
                ':{rowCount:' + $argument + '},"onCarouselTypeChange")'
        } `
        "$($bundle.Name) carousel callback"

    $source = Replace-RegexExact $source `
        'onClick:function\(\)\{const (?<next>[A-Za-z_$][\w$]*)=1===(?<rows>[A-Za-z_$][\w$]*)\?2:1;(?<provider>[A-Za-z_$][\w$]*)\.controls\.carouselTypeChange\(\k<next>\)\}' `
        {
            param($match)
            $next = $match.Groups['next'].Value
            $rows = $match.Groups['rows'].Value
            return 'onClick:function(){const ' + $next + '=' + $rows + '>=4?1:' + $rows +
                '+1;' + $match.Groups['provider'].Value + '.controls.carouselTypeChange(' + $next + ')}'
        } `
        "$($bundle.Name) native row selector" `
        $bundle.NativeChangerCount

    $source = Replace-RegexExact $source `
        '(?<prefix>className:.{0,150}?)2===(?<rows>[A-Za-z_$][\w$]*)&&(?<suffix>.{0,150}?path:"hangar\.filter\.carousel_selector")' `
        {
            param($match)
            return $match.Groups['prefix'].Value + '1<' + $match.Groups['rows'].Value +
                '&&' + $match.Groups['suffix'].Value
        } `
        "$($bundle.Name) native row-selector active state" `
        $bundle.NativeChangerCount

    $source = Replace-RegexExact $source `
        'return (?<scale>[A-Za-z_$][\w$]*)\(2===e\?t\.double:t\.single\)' `
        {
            param($match)
            return 'return ' + $match.Groups['scale'].Value + '(1<e?t.double:t.single)'
        } `
        "$($bundle.Name) multi-row card sizing"

    $source = Replace-RegexExact $source `
        '(?<prefix>[A-Za-z_$][\w$]*&&[A-Za-z_$][\w$]*\()2!==(?![=])(?<rows>[A-Za-z_$][\w$]*)(?<suffix>\?\{visibleSlots)' `
        {
            param($match)
            return $match.Groups['prefix'].Value + '1===' + $match.Groups['rows'].Value +
                $match.Groups['suffix'].Value
        } `
        "$($bundle.Name) visible-slot calculation"

    $rowMatch = [regex]::Match(
        $source,
        '\{carouselRows:(?<rows>[A-Za-z_$][\w$]*),cardWidth:(?<card>[A-Za-z_$][\w$]*),visibleSlots:(?<visible>[A-Za-z_$][\w$]*)\}=')
    if (-not $rowMatch.Success -or
        [regex]::Matches($source, [regex]::Escape($rowMatch.Groups[0].Value)).Count -ne 1) {
        throw "Expected one $($bundle.Name) carousel row binding."
    }
    $renderRows = $rowMatch.Groups['rows'].Value
    $reactVariable = $null
    $source = Replace-RegexExact $source `
        '(?<lhs>[A-Za-z_$][\w$]*)=\((?<source>[A-Za-z_$][\w$]*)=(?<slots>[A-Za-z_$][\w$]*),(?<react>[A-Za-z_$][\w$]*)\.useMemo\(\(\)=>\{const e=\[\];for\(let t=0;t<\k<source>\.length;t\+=2\)e\.push\(\k<source>\.slice\(t,t\+2\)\);return 1===e\.at\(-1\)\?\.length&&e\.at\(-1\)\?\.push\((?<empty>[A-Za-z_$][\w$]*)\),e\},\[\k<source>\]\)\);var \k<source>;' `
        {
            param($match)
            $script:reactVariable = $match.Groups['react'].Value
            $sourceVariable = $match.Groups['source'].Value
            return $match.Groups['lhs'].Value + '=(' + $sourceVariable + '=' +
                $match.Groups['slots'].Value + ',' + $script:reactVariable +
                '.useMemo(()=>{const e=[];for(let t=0;t<' + $sourceVariable + '.length;t+=' +
                $renderRows + ')e.push(' + $sourceVariable + '.slice(t,t+' + $renderRows +
                '));const a=e.at(-1);if(a)for(;a.length<' + $renderRows +
                ';)a.push(' + $match.Groups['empty'].Value + ');return e},[' +
                $sourceVariable + ',' + $renderRows + ']));var ' + $sourceVariable + ';'
        } `
        "$($bundle.Name) generic row chunker"
    $reactVariable = $script:reactVariable

    $source = Replace-RegexExact $source `
        'function\(e,t,a,s,n\)\{const (?<multi>[A-Za-z_$][\w$]*)=2===s;function' `
        { param($match) return $match.Value.Replace('=2===s', '=1<s') } `
        "$($bundle.Name) multi-row keyboard navigation"

    $source = Replace-RegexExact $source `
        'totalElements:2===(?<rows>[A-Za-z_$][\w$]*)\?(?<chunked>[A-Za-z_$][\w$]*)\.length:(?<slots>[A-Za-z_$][\w$]*)\.length' `
        {
            param($match)
            if ($match.Groups['rows'].Value -ne $renderRows) {
                throw "$($bundle.Name) total-elements row binding changed unexpectedly."
            }
            return 'totalElements:1<' + $renderRows + '?' + $match.Groups['chunked'].Value +
                '.length:' + $match.Groups['slots'].Value + '.length'
        } `
        "$($bundle.Name) multi-row element count"

    $source = Replace-RegexExact $source `
        'return 2===(?<rows>[A-Za-z_$][\w$]*)\?(?<jsx>[A-Za-z_$][\w$]*)\.jsx' `
        {
            param($match)
            if ($match.Groups['rows'].Value -ne $renderRows) {
                throw "$($bundle.Name) renderer row binding changed unexpectedly."
            }
            return 'return 1<' + $renderRows + '?' + $match.Groups['jsx'].Value + '.jsx'
        } `
        "$($bundle.Name) multi-row renderer"

    if ($bundle.RootKind -eq 'standard') {
        $pageRows = $null
        $source = Replace-RegexExact $source `
            '(?<filter>[A-Za-z_$][\w$]*)=(?<filterHook>[A-Za-z_$][\w$]*)\(\),(?<selected>[A-Za-z_$][\w$]*)=(?<vehiclesHook>[A-Za-z_$][\w$]*)\(\)\.model\.selectedVehicle\(\),(?<rows>[A-Za-z_$][\w$]*)=\k<filter>\.model\.carouselRowCount\.get\(\)' `
            {
                param($match)
                $script:pageRows = $match.Groups['rows'].Value
                $filter = $match.Groups['filter'].Value
                return $filter + '=' + $match.Groups['filterHook'].Value +
                    '(),hcpVehicles=' + $match.Groups['vehiclesHook'].Value + '(),' +
                    $match.Groups['selected'].Value + '=hcpVehicles.model.selectedVehicle(),' +
                    $script:pageRows + '=' + $filter + '.model.carouselRowCount.get(),' +
                    'hcpAmount=hcpVehicles.model.current.amount(),hcpAuto=' + $filter +
                    '.model.hcpCarouselAuto.get()'
            } `
            "$($bundle.Name) page row model"
        $pageRows = $script:pageRows
    }
    else {
        $pageRows = $null
        $source = Replace-RegexExact $source `
            '(?<filter>[A-Za-z_$][\w$]*)=(?<filterHook>[A-Za-z_$][\w$]*)\(\),(?<inventory>[A-Za-z_$][\w$]*)=(?<vehiclesHook>[A-Za-z_$][\w$]*)\(\)\.model\.current\.intCD\.get\(\)(?<middle>.*?),(?<rows>[A-Za-z_$][\w$]*)=\k<filter>\.model\.carouselRowCount\.get\(\)' `
            {
                param($match)
                $script:pageRows = $match.Groups['rows'].Value
                $filter = $match.Groups['filter'].Value
                return $filter + '=' + $match.Groups['filterHook'].Value +
                    '(),hcpVehicles=' + $match.Groups['vehiclesHook'].Value + '(),' +
                    $match.Groups['inventory'].Value + '=hcpVehicles.model.current.intCD.get()' +
                    $match.Groups['middle'].Value + ',' + $script:pageRows + '=' + $filter +
                    '.model.carouselRowCount.get(),hcpAmount=hcpVehicles.model.current.amount(),' +
                    'hcpAuto=' + $filter + '.model.hcpCarouselAuto.get()'
            } `
            "$($bundle.Name) page row model"
        $pageRows = $script:pageRows
    }

    $escapedPageRows = [regex]::Escape($pageRows)
    $source = Replace-RegexExact $source `
        ('(?<prefix>hcpAuto=[A-Za-z_$][\w$]*\.model\.hcpCarouselAuto\.get\(\),[^;]+);return') `
        {
            param($match)
            $filterMatch = [regex]::Match($match.Groups['prefix'].Value, 'hcpAuto=(?<filter>[A-Za-z_$][\w$]*)\.model')
            $filter = $filterMatch.Groups['filter'].Value
            return $match.Groups['prefix'].Value + ';return ' + $reactVariable +
                '.useEffect(()=>{if(!hcpAuto||hcpAmount<=0)return;' +
                'const hcpRows=hcpAmount<=8?1:hcpAmount<=16?2:hcpAmount<=24?3:4,' +
                'hcpTimer=setTimeout(()=>{hcpRows!==' + $pageRows + '&&' + $filter +
                '.controls.carouselTypeChange({rowCount:hcpRows,hcpAuto:!0})},200);' +
                'return()=>clearTimeout(hcpTimer)},' +
                '[hcpAuto,hcpAmount,' + $pageRows + ',' + $filter + '.controls]),'
        } `
        "$($bundle.Name) automatic row selection"

    $source = Replace-RegexExact $source `
        ('className:(?<classes>[A-Za-z_$][\w$]*)\((?<base>[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)?),2===' +
            $escapedPageRows + '&&(?<double>[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)?)\)') `
        {
            param($match)
            return 'className:' + $match.Groups['classes'].Value + '(' +
                $match.Groups['base'].Value + ',1<' + $pageRows + '&&' +
                $match.Groups['double'].Value + ',3===' + $pageRows +
                '&&"hcp-native-carousel--3",4===' + $pageRows +
                '&&"hcp-native-carousel--4")'
        } `
        "$($bundle.Name) extended carousel height"

    $outputPath = if ($StandardOutputPath) { $StandardOutputPath } else { Join-Path $OutputRoot ($bundle.Entry.Replace('/', '\')) }
    $directory = Split-Path -Parent $outputPath
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    [IO.File]::WriteAllText($outputPath, $source, (New-Object Text.UTF8Encoding($false)))
    Write-Output "Patched native $($bundle.Name) carousel bundle: $outputPath"
}
