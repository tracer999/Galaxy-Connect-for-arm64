<#
.SYNOPSIS
  현재 레지스트리 값, 앱이 보는 값, 펌웨어 값, 서비스 상태, 최근 판정 로그를 보여준다.
  관리자 권한 없이 실행할 수 있다. -Json 을 주면 UI 앱이 읽는 JSON 으로 출력한다.
#>
[CmdletBinding()]
param(
    [int]$LogLines = 10,
    [switch]$Json
)

. (Join-Path $PSScriptRoot 'lib\Common.ps1')

$reg = Get-RegistryValues (Get-SpoofValues)
$eas = Get-EasClientInfo
$fw  = Get-FirmwareValues
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$packages = [ordered]@{}
foreach ($n in $PackageName, 'SAMSUNGELECTRONICSCoLtd.MultiControl') {
    $p = Get-AppxPackage -Name $n
    $packages[$n] = if ($p) { "$($p.Version)" } else { $null }
}
$svc = Get-Service $ServiceName -ErrorAction SilentlyContinue

$logLinesOut = @()
$detection = $null
$log = Get-GalaxyConnectLogPath
if ($log -and (Test-Path $log)) {
    $matches = Get-Content $log -Encoding UTF8 | Select-String 'IsSamsungDevice|HasSupported|Unsupported|not supported|ARM Arch|MCF DeviceInfo'
    $logLinesOut = @($matches | Select-Object -Last $LogLines | ForEach-Object { $_.Line })
    # 마지막 판정 줄: "... Manufacturer: X, IsSamsungDevice: True"
    $last = $matches | Where-Object { $_.Line -match 'Manufacturer: (.+), IsSamsungDevice: (True|False)' } | Select-Object -Last 1
    if ($last -and $last.Line -match '^(\S+ \S+).*Manufacturer: (.+), IsSamsungDevice: (True|False)') {
        $detection = [ordered]@{ Time = $Matches[1]; Manufacturer = $Matches[2]; IsSamsungDevice = ($Matches[3] -eq 'True') }
    }
}

if ($Json) {
    [ordered]@{
        Registry   = [ordered]@{
            Manufacturer = $reg[$SysInfoKey].SystemManufacturer
            ProductName  = $reg[$SysInfoKey].SystemProductName
        }
        AppSees    = [ordered]@{ Manufacturer = $eas.SystemManufacturer; ProductName = $eas.SystemProductName }
        Firmware   = [ordered]@{ Manufacturer = $fw[$SysInfoKey].SystemManufacturer; ProductName = $fw[$SysInfoKey].SystemProductName }
        Cpu        = [ordered]@{ Name = $cpu.Name; Architecture = $env:PROCESSOR_ARCHITECTURE }
        GalaxyConnect = $packages[$PackageName]
        MultiControl  = $packages['SAMSUNGELECTRONICSCoLtd.MultiControl']
        Service    = if ($svc) { "$($svc.Status)" } else { $null }
        Detection  = $detection
        HasBackup  = (Test-Path $BackupJson)
        Log        = $logLinesOut
    } | ConvertTo-Json -Depth 5 -Compress
    return
}

Write-Host '== 레지스트리'
foreach ($key in $reg.Keys) {
    foreach ($name in $reg[$key].Keys) { Write-Host ("  {0}\{1} = {2}" -f $key, $name, $reg[$key][$name]) }
}
Write-Host '== 앱이 보는 값 (EasClientDeviceInformation)'
Write-Host "  $($eas.SystemManufacturer) / $($eas.SystemProductName)"
Write-Host '== 펌웨어 값 (WMI, 스푸핑 영향 없음)'
Write-Host "  $($fw[$SysInfoKey].SystemManufacturer) / $($fw[$SysInfoKey].SystemProductName)"
Write-Host '== 설치 / 서비스'
foreach ($n in $packages.Keys) {
    Write-Host ("  {0}: {1}" -f $n, $(if ($packages[$n]) { $packages[$n] } else { '미설치' }))
}
Write-Host ("  {0}: {1}" -f $ServiceName, $(if ($svc) { $svc.Status } else { '없음' }))
Write-Host '== Galaxy Connect 최근 판정 로그'
if ($logLinesOut.Count) {
    $logLinesOut | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host '  (로그 없음. Galaxy Connect 를 한 번 실행하세요.)'
}
