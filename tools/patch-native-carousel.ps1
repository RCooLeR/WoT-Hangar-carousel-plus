[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$GameRoot,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$GameRoot = [IO.Path]::GetFullPath($GameRoot)
$OutputPath = [IO.Path]::GetFullPath($OutputPath)
. (Join-Path $PSScriptRoot 'client-profile.ps1')
$profile = Get-HcpClientProfile -GameRoot $GameRoot
if ($profile.Version -eq '2.4.0.0') {
    & (Join-Path $PSScriptRoot 'patch-native-event-carousels.ps1') `
        -GameRoot $GameRoot -OutputRoot (Split-Path -Parent $OutputPath) -StandardOutputPath $OutputPath
    return
}
$packagePath = Join-Path $GameRoot 'res\packages\gui-part3.pkg'
$entryPath = 'gui/gameface/_dist/production/mono/hangar/views/main/main.html/bundle.js'
$expectedHash = $profile.Hashes.main

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($packagePath)
try {
    $entry = $zip.GetEntry($entryPath)
    if (-not $entry) {
        throw "Native hangar bundle is missing: $entryPath"
    }
    $stream = $entry.Open()
    $memory = New-Object IO.MemoryStream
    try {
        $stream.CopyTo($memory)
        $sourceBytes = $memory.ToArray()
    }
    finally {
        $memory.Dispose()
        $stream.Dispose()
    }
}
finally {
    $zip.Dispose()
}

$sha = [Security.Cryptography.SHA256]::Create()
try {
    $sourceHash = (($sha.ComputeHash($sourceBytes) | ForEach-Object { $_.ToString('X2') }) -join '')
}
finally {
    $sha.Dispose()
}
if ($sourceHash -ne $expectedHash) {
    throw "Unsupported native hangar bundle $sourceHash; expected WoT $($profile.Version) bundle $expectedHash"
}

$source = [Text.Encoding]::UTF8.GetString($sourceBytes)
$replacements = @(
    @(
        'i={...t.primitives(["defaultFilters"])}',
        'i={...t.primitives(["defaultFilters","hcpCarouselAuto","hcpSortJson"])}'
    ),
    @(
        'l={...t.primitives(["carouselRowCount"]),filters:e.box(r,{deep:!1}),searchName:e.box(n?.[0]??""),nations:t.arrayClone("nationsOrder")}',
        'l={...t.primitives(["carouselRowCount"]),hcpCarouselAuto:i.hcpCarouselAuto,hcpSortJson:i.hcpSortJson,filters:e.box(r,{deep:!1}),searchName:e.box(n?.[0]??""),nations:t.arrayClone("nationsOrder")}'
    ),
    @(
        'o=(s?u(s.list):h()).filter(s=>!1!==i.has(s.id)&&(!!Nr(e,s,a.requires.statistic.model.get(s.id))&&jr(t,s)));r(()=>n.set(o))',
        'o=(s?u(s.list):h()).filter(s=>!1!==i.has(s.id)&&(!!Nr(e,s,a.requires.statistic.model.get(s.id))&&jr(t,s)));const hcp=(()=>{try{return JSON.parse(a.requires.filters.model.hcpSortJson.get())}catch(e){return{}}})();hcp.mode&&"default"!==hcp.mode&&hcp.values&&o.sort((e,t)=>{const a=Number(hcp.values[e.id]??0),s=Number(hcp.values[t.id]??0);return a===s?0:(hcp.descending?-1:1)*(a-s)}),r(()=>n.set(o))'
    ),
    @(
        'carouselTypeChange:n.createCallback(e=>({rowCount:e}),"onCarouselTypeChange")',
        'carouselTypeChange:n.createCallback(e=>"object"==typeof e?e:{rowCount:e},"onCarouselTypeChange")'
    ),
    @(
        'onClick:function(){const e=1===a?2:1;t.controls.carouselTypeChange(e)},children:o.jsx(Te,{className:l(cb.carouselIcon,2===a&&cb.carouselIcon__active),path:"hangar.filter.carousel_selector"})',
        'onClick:function(){const e=a>=4?1:a+1;t.controls.carouselTypeChange(e)},children:o.jsx(Te,{className:l(cb.carouselIcon,1<a&&cb.carouselIcon__active),path:"hangar.filter.carousel_selector"})'
    ),
    @(
        'return xt(2===e?t.double:t.single)',
        'return xt(1<e?t.double:t.single)'
    ),
    @(
        's&&r(2!==t?{visibleSlots:Math.ceil(s/a),cardWidth:a,carouselRows:t}:{visibleSlots:Math.ceil(s/a*t),cardWidth:a,carouselRows:t})',
        's&&r(1===t?{visibleSlots:Math.ceil(s/a),cardWidth:a,carouselRows:t}:{visibleSlots:Math.ceil(s/a*t),cardWidth:a,carouselRows:t})'
    ),
    @(
        'N=(j=w,n.useMemo(()=>{const e=[];for(let t=0;t<j.length;t+=2)e.push(j.slice(t,t+2));return 1===e.at(-1)?.length&&e.at(-1)?.push(nx),e},[j]));var j;',
        'N=(j=w,n.useMemo(()=>{const e=[];for(let t=0;t<j.length;t+=i)e.push(j.slice(t,t+i));const a=e.at(-1);if(a)for(;a.length<i;)a.push(nx);return e},[j,i]));var j;'
    ),
    @(
        'function(e,t,a,s,n){const r=2===s;function i(s)',
        'function(e,t,a,s,n){const r=1<s;function i(s)'
    ),
    @(
        'totalElements:2===v?N.length:w.length',
        'totalElements:1<v?N.length:w.length'
    ),
    @(
        'return 2===v?o.jsx(St',
        'return 1<v?o.jsx(St'
    ),
    @(
        'className:l(OH,2===s&&zH)',
        'className:l(OH,1<s&&zH,3===s&&"hcp-native-carousel--3",4===s&&"hcp-native-carousel--4")'
    ),
    @(
        'XH=i(function(){const e=Ve(),t=Pr(),a=Fr().model.selectedVehicle(),s=t.model.carouselRowCount.get(),r=void 0===a,i=ZH.includes(e.location)&&!r,c=GH.includes(e.location)&&!r,d=e.location===RC,u=!d;return n.useLayoutEffect(()=>{Us(!0)}),o.jsx',
        'XH=i(function(){const e=Ve(),t=Pr(),f=Fr(),a=f.model.selectedVehicle(),s=t.model.carouselRowCount.get(),m=f.model.current.amount(),p=t.model.hcpCarouselAuto.get(),r=void 0===a,i=ZH.includes(e.location)&&!r,c=GH.includes(e.location)&&!r,d=e.location===RC,u=!d;return n.useLayoutEffect(()=>{Us(!0)}),n.useEffect(()=>{if(!p||m<=0)return;const hcpRows=m<=8?1:m<=16?2:m<=24?3:4,hcpTimer=setTimeout(()=>{hcpRows!==s&&t.controls.carouselTypeChange({rowCount:hcpRows,hcpAuto:!0})},200);return()=>clearTimeout(hcpTimer)},[p,m,s,t.controls]),o.jsx'
    )
)

foreach ($replacement in $replacements) {
    $from = $replacement[0]
    $to = $replacement[1]
    $count = ([regex]::Matches($source, [regex]::Escape($from))).Count
    if ($count -ne 1) {
        throw "Expected one native carousel patch point, found $count for: $from"
    }
    $source = $source.Replace($from, $to)
}

$directory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $directory | Out-Null
[IO.File]::WriteAllText($OutputPath, $source, (New-Object Text.UTF8Encoding($false)))
Write-Output "Patched native carousel bundle: $OutputPath"
