<#
.SYNOPSIS
  스푸핑하기 전의 레지스트리 값을 backup\ 폴더에 저장한다.

.DESCRIPTION
  - backup\original-values.json : 복원에 쓰는 값
  - backup\BIOS.reg, backup\SystemInformation.reg : 참고용 전체 키 내보내기
  백업이 이미 있으면 덮어쓰지 않는다 (-Force 로 덮어쓰기).
  이미 스푸핑된 상태(제조사에 samsung 포함)면 잘못된 값을 저장하지 않도록 중단한다.
#>
[CmdletBinding()]
param([switch]$Force)

. (Join-Path $PSScriptRoot 'lib\Common.ps1')
if (Invoke-SelfElevation $PSCommandPath $PSBoundParameters) { return }

if ((Test-Path $BackupJson) -and -not $Force) {
    Write-Host "백업이 이미 있습니다 (덮어쓰려면 -Force): $BackupJson"
    return
}

$current = Get-RegistryValues (Get-SpoofValues)
if ($current[$SysInfoKey].SystemManufacturer -match '(?i)samsung' -and -not $Force) {
    throw '레지스트리가 이미 Samsung 값입니다. 재부팅해서 원래 값으로 돌린 뒤 백업하세요.'
}

New-Item -ItemType Directory -Force $BackupDir | Out-Null
[ordered]@{ CreatedAt = (Get-Date).ToString('o'); Keys = $current } |
    ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $BackupJson
& reg.exe export 'HKLM\HARDWARE\DESCRIPTION\System\BIOS' (Join-Path $BackupDir 'BIOS.reg') /y | Out-Null
& reg.exe export 'HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation' (Join-Path $BackupDir 'SystemInformation.reg') /y | Out-Null

Write-Host "백업 완료: $BackupDir"
