<#
.SYNOPSIS
    Thin PowerShell wrapper around the Python builder (2exe.py).

.DESCRIPTION
    All build logic lives in 2exe.py so that the tool list and version come
    from cbox_core instead of being duplicated here. This script only maps
    PowerShell parameters onto the builder's CLI.

.EXAMPLE
    .\build.ps1                       # build every tool
    .\build.ps1 -Name cpi             # build one tool
    .\build.ps1 -Name cro -Windowed   # no-console build
    .\build.ps1 -Clean                # wipe build\ and dist\ first
#>

[CmdletBinding()]
param(
    [string[]] $Name = @(),
    [switch] $Windowed,
    [switch] $Clean,
    [switch] $NoMetadata
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot

try {
    if ($Clean) {
        Write-Host 'Removing previous build artifacts...' -ForegroundColor Yellow
        foreach ($dir in @('.\build', '.\dist')) {
            if (Test-Path -LiteralPath $dir) {
                Remove-Item -Recurse -Force -LiteralPath $dir
            }
        }
    }

    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error 'python was not found in PATH. Install Python or activate your virtualenv.'
        exit 2
    }

    $builderArgs = @('2exe.py')
    if ($Name) { $builderArgs += $Name }
    if ($Windowed) { $builderArgs += '--windowed' }
    if ($NoMetadata) { $builderArgs += '--no-metadata' }

    & python @builderArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}