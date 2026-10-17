<#
.SYNOPSIS
  데스크톱 앱을 단일 exe 로 빌드한다: app\release\GalaxyConnectForARM64-<version>-arm64-portable.exe

.DESCRIPTION
  ARM64 용 Python(3.12 이상, tkinter 포함)이 필요하다. 처음 실행하면 app\.venv 를 만들고
  PyInstaller 를 설치한다. 루트의 *.ps1 과 lib\ 는 exe 안의 scripts\ 로 들어간다.
#>
[CmdletBinding()]
param([string]$Python = 'python')

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    & $Python -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE) { throw "venv 를 만들지 못했습니다: $Python" }
}
# x64 Python 으로 빌드하면 ARM64 PC 에서 에뮬레이션으로 돌므로 막는다
$arch = & $venvPython -c 'import platform; print(platform.machine())'
if ($arch -ne 'ARM64') { throw "ARM64 Python 이 아닙니다 ($arch). -Python 으로 ARM64 python.exe 경로를 지정하세요." }

& $venvPython -m pip install --disable-pip-version-check -q -r (Join-Path $PSScriptRoot 'requirements-build.txt')
if ($LASTEXITCODE) { throw 'PyInstaller 를 설치하지 못했습니다.' }

$version = & $venvPython -c "import sys; sys.path.insert(0, r'$PSScriptRoot'); import backend; print(backend.VERSION)"
$name = "GalaxyConnectForARM64-$version-arm64-portable"
$data = @('Apply.ps1', 'Backup.ps1', 'Restore.ps1', 'Status.ps1') | ForEach-Object { '--add-data', "$(Join-Path $root $_);scripts" }
$data += '--add-data', "$(Join-Path $root 'lib');scripts\lib"

& $venvPython -m PyInstaller --noconfirm --clean --onefile --windowed --name $name `
    --distpath (Join-Path $PSScriptRoot 'release') `
    --workpath (Join-Path $PSScriptRoot 'build') `
    --specpath (Join-Path $PSScriptRoot 'build') `
    @data (Join-Path $PSScriptRoot 'main.py')
if ($LASTEXITCODE) { throw 'PyInstaller 빌드에 실패했습니다.' }

$exe = Get-Item (Join-Path $PSScriptRoot "release\$name.exe")
Write-Host ("빌드 완료: {0} ({1:N1} MB)" -f $exe.FullName, ($exe.Length / 1MB))
