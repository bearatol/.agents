[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('codex', 'claude', 'gemini', 'koda', 'sourcecraft', 'generic')]
    [string[]] $HostName,
    [switch] $Force
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'AgentEcosystem.psm1') -Force
try {
    Connect-AeHosts -Hosts $HostName -Force:$Force -DryRun
    Connect-AeHosts -Hosts $HostName -Force:$Force
} catch {
    Write-Error $_
    exit 1
}
