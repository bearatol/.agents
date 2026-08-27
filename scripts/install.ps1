[CmdletBinding()]
param(
    [string[]] $Profile = @(),
    [string[]] $Component = @(),
    [ValidateSet('codex', 'claude', 'gemini', 'koda', 'sourcecraft', 'generic')]
    [string[]] $HostName = @(),
    [switch] $Force,
    [switch] $DryRun,
    [switch] $NoRootFiles,
    [switch] $PreserveAgentsFile
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'AgentEcosystem.psm1') -Force
try {
    Install-AeComponents -Profiles $Profile -Components $Component -Hosts $HostName `
        -Force:$Force -DryRun:$DryRun -NoRootFiles:$NoRootFiles `
        -PreserveAgentsFile:$PreserveAgentsFile
} catch {
    Write-Error $_
    exit 1
}
