[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PackagePath
)

$ErrorActionPreference = 'Stop'
$PackagePath = [IO.Path]::GetFullPath($PackagePath)
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($PackagePath)
try {
    $eventNativeBundles = @(
        'res/comp7_light/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js',
        'res/comp7/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js',
        'res/frontline/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js',
        'res/fun_random/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js',
        'res/last_stand/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js'
    )
    $required = @(
        'meta.xml',
        'res/scripts/client/gui/mods/mod_hangar_carousel_plus.pyc',
        'res/gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.i18n.js',
        'res/gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.js',
        'res/gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.css',
        'res/gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.tooltip.js',
        'res/gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.tooltip.css',
        'res/gui/gameface/_dist/production/mono/hangar/views/main/main.html/bundle.js',
        'res/gui/gameface/_dist/production/mono/hangar/views/vehicle_tooltip/vehicle_tooltip.html/bundle.js',
        'res/gui/gameface/_dist/production/mono/hangar/vehicle_tooltip/vehicle_tooltip.css'
    ) + $eventNativeBundles
    $names = @($zip.Entries | ForEach-Object FullName)
    foreach ($entry in $required) {
        if ($entry -notin $names) {
            throw "Required package entry is missing: $entry"
        }
    }

    $pyc = $zip.GetEntry('res/scripts/client/gui/mods/mod_hangar_carousel_plus.pyc')
    $stream = $pyc.Open()
    try {
        $header = New-Object byte[] 4
        [void]$stream.Read($header, 0, 4)
    }
    finally {
        $stream.Dispose()
    }
    $magic = ($header | ForEach-Object { $_.ToString('X2') }) -join '-'
    if ($magic -ne '03-F3-0D-0A') {
        throw "Unexpected Python bytecode magic: $magic (expected Python 2.7)."
    }

    $js = $zip.GetEntry('res/gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.js')
    $jsStream = $js.Open()
    $reader = New-Object IO.StreamReader($jsStream, [Text.Encoding]::UTF8)
    try {
        $jsSource = $reader.ReadToEnd()
    }
    finally {
        $reader.Dispose()
        $jsStream.Dispose()
    }
    if ($jsSource.Contains(':scope')) {
        throw 'Unsupported Gameface CSS selector found: :scope'
    }
    if ($jsSource.Contains('Page_carouselButtons_')) {
        throw 'HCP controls must be rendered inside the native filter popover, not beside the carousel.'
    }
    if ($jsSource.Contains('createElement("select")')) {
        throw 'Native Gameface does not render an HTML select compactly; use icon controls.'
    }
    if (-not $jsSource.Contains('carouselRowButtonContent') -or
        -not $jsSource.Contains('labels().carousel_auto') -or
        -not $jsSource.Contains('SORT_ICONS') -or
        -not $jsSource.Contains('SORT_DIRECTION_ICONS')) {
        throw 'Carousel row icon controls or automatic mode UI are missing.'
    }
    if ($jsSource.Contains('-webkit-text-fill-color')) {
        throw 'Unsupported Gameface text-fill property found.'
    }
    if (-not $jsSource.Contains('onSetSorting') -or
        -not $jsSource.Contains('applyActionCardsVisibility')) {
        throw 'Native sorting controls or action-card visibility support are missing.'
    }
    if (-not $jsSource.Contains('sort_priority') -or
        -not $jsSource.Contains("priority: '<svg") -or
        $jsSource.Contains('setInterval(renderCardStats')) {
        throw 'Priority sorting is missing or obsolete card-stat polling is still enabled.'
    }
    if ($jsSource.Contains('CurrencyLock') -or
        $jsSource.Contains('hcp-currency-lock')) {
        throw 'Currency protection must not be included in this carousel mod.'
    }
    if ($jsSource.Contains('console.warn') -or
        -not $jsSource.Contains('function debugLog(message)')) {
        throw 'Routine Gameface diagnostics must be debug-gated and must not use warnings.'
    }

    $nativeBundle = $zip.GetEntry('res/gui/gameface/_dist/production/mono/hangar/views/main/main.html/bundle.js')
    $nativeStream = $nativeBundle.Open()
    $nativeReader = New-Object IO.StreamReader($nativeStream, [Text.Encoding]::UTF8)
    try {
        $nativeSource = $nativeReader.ReadToEnd()
    }
    finally {
        $nativeReader.Dispose()
        $nativeStream.Dispose()
    }
    if (-not $nativeSource.Contains('t+=i)e.push(j.slice(t,t+i))')) {
        throw 'Native carousel bundle does not contain the generic HCP row chunker.'
    }
    if ($nativeSource.Contains('totalElements:2===v?N.length:w.length')) {
        throw 'Native carousel bundle still contains the two-row-only renderer.'
    }
    if (-not $nativeSource.Contains('3===s&&"hcp-native-carousel--3",4===s&&"hcp-native-carousel--4"')) {
        throw 'Native carousel bundle does not expose the three- and four-row height classes.'
    }
    if (-not $nativeSource.Contains('!p||m<=0)return;const hcpRows=m<=8?1:m<=16?2:m<=24?3:4') -or
        -not $nativeSource.Contains('hcpCarouselAuto') -or
        -not $nativeSource.Contains('m=f.model.current.amount()') -or
        -not $nativeSource.Contains('hcpAuto:!0})},200);return()=>clearTimeout(hcpTimer)')) {
        throw 'Native carousel bundle does not contain stable final-list automatic row selection.'
    }
    if (-not $nativeSource.Contains('hcpSortJson') -or
        -not $nativeSource.Contains('const hcp=') -or
        -not $nativeSource.Contains('hcpCarouselAuto:i.hcpCarouselAuto')) {
        throw 'Native carousel bundle does not contain HCP sorting support.'
    }

    foreach ($eventBundlePath in $eventNativeBundles) {
        $eventBundle = $zip.GetEntry($eventBundlePath)
        $eventStream = $eventBundle.Open()
        $eventReader = New-Object IO.StreamReader($eventStream, [Text.Encoding]::UTF8)
        try {
            $eventSource = $eventReader.ReadToEnd()
        }
        finally {
            $eventReader.Dispose()
            $eventStream.Dispose()
        }
        if (-not [regex]::IsMatch(
                $eventSource,
                't\+=(?<rows>[A-Za-z_$][\w$]*)\)e\.push\((?<source>[A-Za-z_$][\w$]*)\.slice\(t,t\+\k<rows>\)\);const a=e\.at\(-1\);if\(a\)for\(;a\.length<\k<rows>;\)a\.push')) {
            throw "Event hangar bundle does not contain the generic row chunker: $eventBundlePath"
        }
        if ($eventSource.Contains('totalElements:2===')) {
            throw "Event hangar bundle still contains a two-row-only renderer: $eventBundlePath"
        }
        if (-not [regex]::IsMatch(
                $eventSource,
                'className:[A-Za-z_$][\w$]*\([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)?,1<(?<rows>[A-Za-z_$][\w$]*)&&[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)?,3===\k<rows>&&"hcp-native-carousel--3",4===\k<rows>&&"hcp-native-carousel--4"\)')) {
            throw "Event hangar bundle does not expose extended height classes: $eventBundlePath"
        }
        if ($eventBundlePath.StartsWith('res/last_stand/') -and
            (-not $eventSource.Contains('HangarApp_carousel_bc4dc752') -or
             -not $eventSource.Contains('HangarApp_carousel__double_5f5d7e60'))) {
            throw 'Last Stand bundle is not using its expected HangarApp carousel wrapper.'
        }
        if (-not $eventSource.Contains('!hcpAuto||hcpAmount<=0)return;const hcpRows=hcpAmount<=8?1:hcpAmount<=16?2:hcpAmount<=24?3:4') -or
            -not $eventSource.Contains('hcpCarouselAuto') -or
            -not $eventSource.Contains('hcpAuto:!0})},200);return()=>clearTimeout(hcpTimer)')) {
            throw "Event hangar bundle does not contain stable automatic row selection: $eventBundlePath"
        }
        if (-not $eventSource.Contains('hcpSortJson') -or
            -not $eventSource.Contains('const hcp=')) {
            throw "Event hangar bundle does not contain HCP sorting support: $eventBundlePath"
        }
    }

    $tooltipBundle = $zip.GetEntry('res/gui/gameface/_dist/production/mono/hangar/views/vehicle_tooltip/vehicle_tooltip.html/bundle.js')
    $tooltipStream = $tooltipBundle.Open()
    $tooltipReader = New-Object IO.StreamReader($tooltipStream, [Text.Encoding]::UTF8)
    try {
        $tooltipSource = $tooltipReader.ReadToEnd()
    }
    finally {
        $tooltipReader.Dispose()
        $tooltipStream.Dispose()
    }
    if ($tooltipSource.Contains('console.warn') -or
        $tooltipSource.Contains('[HangarCarouselPlusTooltip]')) {
        throw 'Routine tooltip lifecycle diagnostics must remain disabled.'
    }
    if ($tooltipSource.Contains('setInterval(hcpTooltipRender') -or
        -not $tooltipSource.Contains('setInterval(hcpTooltipSyncModel, 1000)')) {
        throw 'Tooltip renderer must use mutation-driven rendering with one low-frequency model-sync fallback.'
    }

    $tooltipCss = $zip.GetEntry('res/gui/gameface/_dist/production/mono/hangar/vehicle_tooltip/vehicle_tooltip.css')
    $tooltipCssStream = $tooltipCss.Open()
    $tooltipCssReader = New-Object IO.StreamReader($tooltipCssStream, [Text.Encoding]::UTF8)
    try {
        $tooltipCssSource = $tooltipCssReader.ReadToEnd()
    }
    finally {
        $tooltipCssReader.Dispose()
        $tooltipCssStream.Dispose()
    }
    if (-not $tooltipCssSource.Contains('.hcp-tooltip-stats-title')) {
        throw 'Native vehicle tooltip stylesheet does not contain the HCP styles.'
    }

    $css = $zip.GetEntry('res/gui/gameface/mods/rcooler/hangar_carousel_plus/hangar_carousel_plus.css')
    $cssStream = $css.Open()
    $cssReader = New-Object IO.StreamReader($cssStream, [Text.Encoding]::UTF8)
    try {
        $cssSource = $cssReader.ReadToEnd()
    }
    finally {
        $cssReader.Dispose()
        $cssStream.Dispose()
    }
    if ($cssSource.Contains('calc(')) {
        throw 'Unsupported Gameface calc() expression found.'
    }
    if (-not $cssSource.Contains('.hcp-native-carousel--3') -or
        -not $cssSource.Contains('.hcp-native-carousel--4') -or
        -not $cssSource.Contains('min-height: 443rem')) {
        throw 'Extended carousel height rules are missing.'
    }
    if (-not $cssSource.Contains('[data-test-id="buyTank"]') -or
        -not $cssSource.Contains('.hcp-native-sort-button')) {
        throw 'Action-card visibility or sorting styles are missing.'
    }
    if (-not $cssSource.Contains('.hcp-native-filter svg *') -or
        -not $cssSource.Contains('stroke: #fff !important') -or
        -not $cssSource.Contains('.hcp-native-row-button svg *') -or
        -not $cssSource.Contains('.hcp-native-sort-svg')) {
        throw 'Filter and sorting glyphs are not force-colored white.'
    }
    if ($cssSource.Contains('-webkit-text-fill-color')) {
        throw 'Unsupported Gameface text-fill style found.'
    }
    if ($cssSource.Contains(':not(') -or
        $cssSource.Contains(':disabled') -or
        $cssSource.Contains('white-space: pre-line')) {
        throw 'Unsupported Gameface selector or white-space mode found.'
    }
    if ($cssSource.Contains('hcp-currency-lock')) {
        throw 'Currency protection styles must not be included in this carousel mod.'
    }
}
finally {
    $zip.Dispose()
}

Write-Output "Validated: $PackagePath"
