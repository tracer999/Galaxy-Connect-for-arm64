<#
.SYNOPSIS
  레지스트리의 제조사 값을 Samsung 으로 바꾸고 Galaxy Connect 가 다시 판정하게 한다.

.DESCRIPTION
  1. 백업이 없으면 Backup.ps1 을 실행한다.
  2. 레지스트리 두 키의 제조사/모델 값을 바꾼다.
  3. 앱이 실제로 보는 값(EasClientDeviceInformation)이 Samsung 인지 확인한다.
  4. Galaxy Connect 를 종료하고 앱 데이터를 초기화한 뒤 서비스를 재시작한다.

  재부팅하면 레지스트리는 원래 값으로 돌아가지만, Galaxy Connect 는 첫 판정 결과를
  캐시하므로 계속 동작한다. 앱 데이터 초기화나 재설치 후에는 다시 실행한다.
#>
[CmdletBinding()]
param(
    [string]$Manufacturer = 'Samsung Electronics',
    [string]$ProductName  = '940XMA',
    [string]$Family       = 'Galaxy Book4 Edge'
)

. (Join-Path $PSScriptRoot 'lib\Common.ps1')
if (Invoke-SelfElevation $PSCommandPath $PSBoundParameters) { return }

if (-not (Get-GalaxyConnectPackage)) {
    throw "Galaxy Connect 가 설치되어 있지 않습니다. Microsoft Store 에서 먼저 설치하세요: $PackageName"
}

Write-Host '== 1. 백업'
& (Join-Path $PSScriptRoot 'Backup.ps1')

Write-Host '== 2. 레지스트리 적용'
Set-RegistryValues (Get-SpoofValues -Manufacturer $Manufacturer -ProductName $ProductName -Family $Family)

Write-Host '== 3. 확인'
$e = Get-EasClientInfo
Write-Host "  EasClientDeviceInformation: $($e.SystemManufacturer) / $($e.SystemProductName)"
if ($e.SystemManufacturer -notmatch '(?i)samsung') {
    Write-Warning '앱이 보는 값이 아직 Samsung 이 아닙니다. 앱 데이터는 초기화하지 않았습니다. Restore.ps1 로 되돌릴 수 있습니다.'
    return
}

Write-Host '== 4. 앱 데이터 초기화 / 서비스 재시작'
Stop-GalaxyConnect
Reset-GalaxyConnectData
Restart-GalaxyConnectService

Write-Host ''
Write-Host '완료. 다음 순서로 진행하세요.'
Write-Host '  1) Galaxy Connect 를 실행하고 Samsung 계정으로 로그인'
Write-Host '  2) Status.ps1 로 로그에 "IsSamsungDevice: True" 가 나오는지 확인'
Write-Host '  3) Multi Control 등 원하는 기능 사용'
