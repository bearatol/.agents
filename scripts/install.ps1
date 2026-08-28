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
$AgentsHome = Get-AeAgentsHome
try {
    Install-AeComponents -Profiles $Profile -Components $Component -Hosts @() `
        -Force:$Force -DryRun -NoRootFiles:$NoRootFiles `
        -PreserveAgentsFile:$PreserveAgentsFile
    if ($HostName.Count -gt 0) {
        $PreflightRoot = Join-Path ([IO.Path]::GetTempPath()) ('.ae-install-' + [Guid]::NewGuid().ToString('N'))
        $SavedAgentsHome = $env:AGENTS_HOME
        try {
            $env:AGENTS_HOME = Join-Path $PreflightRoot 'agents'
            Install-AeComponents -Profiles $Profile -Components $Component -Hosts @() `
                -Force:$Force -NoRootFiles:$NoRootFiles `
                -PreserveAgentsFile:$PreserveAgentsFile
            $ExistingState = Join-Path $AgentsHome '.ecosystem-state-windows.json'
            if (Test-Path -LiteralPath $ExistingState -PathType Leaf) {
                Copy-Item -LiteralPath $ExistingState `
                    -Destination (Join-Path $env:AGENTS_HOME '.ecosystem-state-windows.json') -Force
            }
            Connect-AeHosts -Hosts $HostName -Force:$Force -DryRun
        } finally {
            if ($null -eq $SavedAgentsHome) {
                Remove-Item Env:AGENTS_HOME -ErrorAction SilentlyContinue
            } else {
                $env:AGENTS_HOME = $SavedAgentsHome
            }
            if (Test-Path -LiteralPath $PreflightRoot) {
                Remove-Item -LiteralPath $PreflightRoot -Recurse -Force
            }
        }
    }
    Install-AeComponents -Profiles $Profile -Components $Component -Hosts $HostName `
        -Force:$Force -DryRun:$DryRun -NoRootFiles:$NoRootFiles `
        -PreserveAgentsFile:$PreserveAgentsFile
} catch {
    Write-Error $_
    exit 1
}
