# Build a standalone laberinto.exe using PyInstaller.
# Usage:   .\build.ps1
# Output:  dist\laberinto.exe
#
# Prerequisites:
#   pip install -e ".[build]"

$ErrorActionPreference = "Stop"

$pyinstaller = Join-Path $PSScriptRoot ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $pyinstaller)) {
    Write-Host "pyinstaller no encontrado en $pyinstaller" -ForegroundColor Red
    Write-Host "Ejecuta primero: .venv\Scripts\python.exe -m pip install -e '.[build]'"
    exit 1
}

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# Si existe docs\laberinto.ico, lo usa como ícono del .exe.
$iconArg = @()
$iconPath = Join-Path $PSScriptRoot "docs\laberinto.ico"
if (Test-Path $iconPath) {
    Write-Host "Usando icono: $iconPath" -ForegroundColor Cyan
    $iconArg = @("--icon", $iconPath)
} else {
    Write-Host "Sin icono custom (coloca docs\laberinto.ico para personalizar)." -ForegroundColor DarkGray
}

& $pyinstaller `
    --onefile `
    --name laberinto `
    --collect-all reportlab `
    --console `
    --noconfirm `
    @iconArg `
    maze_pdf\__main__.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build falló." -ForegroundColor Red
    exit $LASTEXITCODE
}

$exe = Join-Path $PSScriptRoot "dist\laberinto.exe"
Write-Host ""
Write-Host "OK: $exe" -ForegroundColor Green
Write-Host "Tamaño: $([math]::Round((Get-Item $exe).Length / 1MB, 1)) MB"
