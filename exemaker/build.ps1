<#
build.ps1 - Build helper for tping using PyInstaller

Usage examples:
  # One-file console exe (recommended for testing in cmd/powershell)
  .\build.ps1 -Name tping -OneFile

  # One-file windowed exe (no console, good for double-click users)
  .\build.ps1 -Name tping -OneFile -Windowed

  # Clean previous build artifacts then build
  .\build.ps1 -Name tping -OneFile -Clean

This script will attempt to install PyInstaller into the active Python environment
if it's missing, then run `python -m PyInstaller` with sensible defaults.
#>

Param(
    [switch]$Windowed,
    [switch]$OneFile = $true,
    [string]$Name = "tping",
    [switch]$Clean
)

Set-StrictMode -Version Latest
Push-Location $PSScriptRoot
try {
    Write-Host "Building '$Name' (Windowed=$Windowed, OneFile=$OneFile, Clean=$Clean)"

    # Ensure python is available
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        Write-Error "`python` not found in PATH. Activate your virtualenv or install Python and try again."
        exit 2
    }

    # Ensure PyInstaller is available; try python -m PyInstaller so we don't rely on PATH
    $piTest = & python -m PyInstaller --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PyInstaller not found in the current Python environment. Installing..."
        & python -m pip install --upgrade pyinstaller
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install PyInstaller. Please install it manually and re-run this script."
            exit 3
        }
    }

    $scriptPath = Join-Path $PSScriptRoot 'tping.py'
    if (-not (Test-Path $scriptPath)) {
        Write-Error "Cannot find tping.py in $PSScriptRoot"
        exit 4
    }

    if ($Clean) {
        Write-Host "Cleaning previous build/dist/spec files..."
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .\build, .\dist, "$Name.spec"
    }

    $args = @()
    if ($OneFile) { $args += '--onefile' }
    $args += '--name'; $args += $Name
    if ($Windowed) { $args += '--windowed' }

    Write-Host "Running PyInstaller..."
    # Use python -m PyInstaller to ensure the correct interpreter is used
    & python -m PyInstaller @args $scriptPath

    if ($LASTEXITCODE -eq 0) {
        $exePath = Join-Path (Join-Path $PSScriptRoot 'dist') ($Name + '.exe')
        if (Test-Path $exePath) {
            Write-Host "Build succeeded. Output: $exePath"
        } else {
            Write-Host "Build completed but expected exe not found in dist\ : check output above." -ForegroundColor Yellow
        }
    } else {
        Write-Error "PyInstaller failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }

} finally {
    Pop-Location
}
