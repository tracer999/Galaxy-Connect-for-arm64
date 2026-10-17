<#
.SYNOPSIS
  레지스트리를 원래 값으로 되돌리고 Galaxy Connect 가 다시 판정하게 한다.

.DESCRIPTION
  backup\original-values.json 이 있으면 그 값으로, 없으면 펌웨어(WMI) 값으로 복원한다.
  앱 데이터를 초기화하므로 Galaxy Connect 는 다시 원래 제조사로 판정한다.
  Samsung 계정 로그인도 지워진다.
#>
[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot 'lib\Common.ps1')
if (Invoke-SelfElevation $PSCommandPath $PSBoundParameters) { return }

Write-Host '== 1. 레지스트리 복원'
if (Test-Path $BackupJson) {
    Write-Host "  백업 사용: $BackupJson"
    Set-RegistryValues (Read-BackupValues)
} else {
    Write-Host '  백업이 없어 펌웨어(WMI) 값으로 복원합니다.'
    Set-RegistryValues (Get-FirmwareValues)
}

Write-Host '== 2. 앱 데이터 초기화 / 서비스 재시작'
if (Get-GalaxyConnectPackage) {
    Stop-GalaxyConnect
    Reset-GalaxyConnectData
    Restart-GalaxyConnectService
} else {
    Write-Host '  Galaxy Connect 가 설치되어 있지 않아 건너뜁니다.'
}

Write-Host '복원 완료.'
