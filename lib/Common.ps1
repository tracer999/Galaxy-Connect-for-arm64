# 공통 상수와 함수. 각 스크립트에서 dot-source 한다.
# Windows PowerShell 5.1 과 PowerShell 7 모두에서 동작하도록 작성한다.

$ErrorActionPreference = 'Stop'
# UI 앱이 출력을 읽을 때 진행 표시줄 기록이 섞이지 않게 한다
$ProgressPreference = 'SilentlyContinue'

$PackageName  = 'SAMSUNGELECTRONICSCoLtd.SamsungContinuityService'
$ServiceName  = 'SamsungContinuityWindowsService'
$ProcessNames = 'GalaxyConnectWinUI', 'WindowsMCFCore'

$BiosKey    = 'HKLM:\HARDWARE\DESCRIPTION\System\BIOS'
$SysInfoKey = 'HKLM:\SYSTEM\CurrentControlSet\Control\SystemInformation'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
# UI 앱(portable exe)은 실행할 때마다 임시 폴더에 풀리므로 백업 위치를 환경 변수로 지정한다
$BackupDir   = if ($env:GC_ARM64_BACKUP_DIR) { $env:GC_ARM64_BACKUP_DIR } else { Join-Path $ProjectRoot 'backup' }
$BackupJson  = Join-Path $BackupDir 'original-values.json'

# 스푸핑 대상 값. 기본값은 Snapdragon X Elite 를 쓰는 Galaxy Book4 Edge 계열.
function Get-SpoofValues {
    param(
        [string]$Manufacturer = 'Samsung Electronics',
        [string]$ProductName  = '940XMA',
        [string]$Family       = 'Galaxy Book4 Edge'
    )
    [ordered]@{
        $BiosKey    = [ordered]@{
            SystemManufacturer    = $Manufacturer
            SystemProductName     = $ProductName
            SystemFamily          = $Family
            BaseBoardManufacturer = $Manufacturer
        }
        $SysInfoKey = [ordered]@{
            SystemManufacturer = $Manufacturer
            SystemProductName  = $ProductName
        }
    }
}

# 펌웨어(SMBIOS)에서 직접 읽은 원래 값. WMI 는 레지스트리 스푸핑의 영향을 받지 않는다.
function Get-FirmwareValues {
    $cs = Get-CimInstance Win32_ComputerSystem
    $bb = Get-CimInstance Win32_BaseBoard
    [ordered]@{
        $BiosKey    = [ordered]@{
            SystemManufacturer    = $cs.Manufacturer
            SystemProductName     = $cs.Model
            SystemFamily          = $cs.SystemFamily
            BaseBoardManufacturer = $bb.Manufacturer
        }
        $SysInfoKey = [ordered]@{
            SystemManufacturer = $cs.Manufacturer
            SystemProductName  = $cs.Model
        }
    }
}

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 관리자 권한이 아니면 같은 스크립트를 관리자 권한으로 다시 실행한다.
# 다시 실행했으면 $true 를 반환하므로 호출한 스크립트는 바로 종료하면 된다.
function Invoke-SelfElevation {
    param([string]$ScriptPath, [hashtable]$BoundParameters)
    if (Test-Admin) { return $false }
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-NoExit', '-File', "`"$ScriptPath`"")
    foreach ($p in $BoundParameters.GetEnumerator()) {
        if ($p.Value -is [switch]) {
            if ($p.Value.IsPresent) { $argList += "-$($p.Key)" }
        } else {
            $argList += "-$($p.Key)", "`"$($p.Value)`""
        }
    }
    Write-Host '관리자 권한이 필요합니다. UAC 창에서 "예"를 눌러주세요.'
    Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -ArgumentList $argList
    return $true
}

# 앱이 실제로 보는 제조사 값. PowerShell 7 에는 WinRT 투영이 없으므로 항상 5.1 로 조회한다.
function Get-EasClientInfo {
    $cmd = '$null=[Windows.Security.ExchangeActiveSyncProvisioning.EasClientDeviceInformation,Windows.Security,ContentType=WindowsRuntime];' +
           '$e=New-Object Windows.Security.ExchangeActiveSyncProvisioning.EasClientDeviceInformation;' +
           '"{0}|{1}" -f $e.SystemManufacturer,$e.SystemProductName'
    # 5.1 에서 실행하면 -Command 인자의 따옴표가 사라지므로 인코딩해서 넘긴다
    $enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
    $out = & "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -EncodedCommand $enc
    $parts = "$out".Split('|', 2)
    [pscustomobject]@{ SystemManufacturer = $parts[0]; SystemProductName = $parts[1] }
}

function Get-RegistryValues {
    param($ValueMap)
    $result = [ordered]@{}
    foreach ($key in $ValueMap.Keys) {
        $props = Get-ItemProperty $key
        $vals = [ordered]@{}
        foreach ($name in $ValueMap[$key].Keys) {
            # 원래 없던 값은 $null 로 기록한다. 복원할 때 $null 이면 값을 지운다.
            $vals[$name] = if ($props.PSObject.Properties[$name]) { $props.$name } else { $null }
        }
        $result[$key] = $vals
    }
    $result
}

function Set-RegistryValues {
    param($ValueMap)
    foreach ($key in $ValueMap.Keys) {
        foreach ($name in $ValueMap[$key].Keys) {
            $v = $ValueMap[$key][$name]
            if ($null -eq $v) {
                Remove-ItemProperty -Path $key -Name $name -ErrorAction SilentlyContinue
                Write-Host ("  {0}\{1} = <삭제>" -f $key, $name)
            } else {
                Set-ItemProperty -Path $key -Name $name -Value $v -Type String
                Write-Host ("  {0}\{1} = {2}" -f $key, $name, $v)
            }
        }
    }
}

# JSON 으로 저장한 백업을 Set-RegistryValues 가 받는 형태로 바꾼다 (5.1 에는 -AsHashtable 이 없다).
function Read-BackupValues {
    $data = Get-Content $BackupJson -Raw -Encoding UTF8 | ConvertFrom-Json
    $map = [ordered]@{}
    foreach ($k in $data.Keys.PSObject.Properties) {
        $vals = [ordered]@{}
        foreach ($v in $k.Value.PSObject.Properties) { $vals[$v.Name] = $v.Value }
        $map[$k.Name] = $vals
    }
    $map
}

function Get-GalaxyConnectPackage {
    Get-AppxPackage -Name $PackageName
}

function Stop-GalaxyConnect {
    foreach ($p in $ProcessNames) { Get-Process $p -ErrorAction SilentlyContinue | Stop-Process -Force }
    $svc = Get-Service $ServiceName -ErrorAction SilentlyContinue
    if ($svc -and $svc.Status -ne 'Stopped') {
        Stop-Service $ServiceName -Force
        $svc.WaitForStatus('Stopped', '00:00:30')
    }
}

# Galaxy Connect 는 처음 판정한 제조사를 앱 설정(LocalSettings)에 캐시한다.
# 판정을 다시 하게 하려면 앱 데이터를 초기화해야 한다. Samsung 계정 로그인도 지워진다.
function Reset-GalaxyConnectData {
    $pkg = Get-GalaxyConnectPackage
    if (-not $pkg) { Write-Warning "Galaxy Connect 가 설치되어 있지 않습니다: $PackageName"; return }
    Write-Host "  앱 데이터 초기화: $($pkg.PackageFullName)"
    # 초기화는 되었는데 오류가 보고되는 경우가 있어 중단하지 않고 경고만 남긴다
    try { $pkg | Reset-AppxPackage } catch { Write-Warning "Reset-AppxPackage: $($_.Exception.Message)" }
}

function Restart-GalaxyConnectService {
    if (Get-Service $ServiceName -ErrorAction SilentlyContinue) {
        # Reset-AppxPackage 가 서비스를 다시 띄우는 경우가 있어 재시작으로 상태를 맞춘다
        Restart-Service $ServiceName -Force
        Write-Host "  서비스 재시작: $ServiceName"
    }
}

function Get-GalaxyConnectLogPath {
    $pkg = Get-GalaxyConnectPackage
    if (-not $pkg) { return $null }
    Join-Path $env:LOCALAPPDATA "Packages\$($pkg.PackageFamilyName)\LocalState\Samsung\MCFCore\Logs\SamsungMCFCoreSystemLog.log"
}
