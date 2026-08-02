param(
    [switch]$OneDir
)

$ErrorActionPreference = "Stop"

Write-Host "== TourDeFrance Windows build ==" -ForegroundColor Cyan

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    py -3 -m pip install pyinstaller
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$entry = "src/tour_de_france/main.py"
if (-not (Test-Path $entry)) {
    throw "Could not find entrypoint: $entry"
}

$assetsArg = $null
if (Test-Path "assets") {
    $assetsArg = "--add-data `"assets;assets`""
    Write-Host "Including assets directory: assets/" -ForegroundColor Green
} else {
    Write-Host "No assets/ directory found. Build will use fallback logo." -ForegroundColor Yellow
}

$bundleArg = if ($OneDir) { "--onedir" } else { "--onefile" }

$cmd = @(
    "pyinstaller",
    "--noconfirm",
    $bundleArg,
    "--windowed",
    "--name TourDeFrance",
    "--paths src"
)

if ($assetsArg) {
    $cmd += $assetsArg
}

$cmd += $entry
$cmdLine = $cmd -join " "

Write-Host "Running: $cmdLine" -ForegroundColor DarkGray
Invoke-Expression $cmdLine

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
if ($OneDir) {
    Write-Host "Output: dist/TourDeFrance/" -ForegroundColor Green
} else {
    Write-Host "Output: dist/TourDeFrance.exe" -ForegroundColor Green
}
