[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'AgentEcosystem.psm1') -Force
try {
    Invoke-AeDoctor
} catch {
    Write-Error $_
    exit 1
}
