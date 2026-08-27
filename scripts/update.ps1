[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$ApprovedCommit,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'AgentEcosystem.psm1') -Force
$RepoRoot = Get-AeRepoRoot
$AgentsHome = Get-AeAgentsHome
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) { throw 'Update requires a Git clone.' }
$Manifest = Join-Path $AgentsHome '.ecosystem-profiles'
if (-not (Test-Path -LiteralPath $Manifest)) { throw 'No installed profile manifest found.' }
git -C $RepoRoot fetch --prune origin
if ($LASTEXITCODE) { throw 'git fetch failed' }
$Upstream = (& git -C $RepoRoot rev-parse '@{u}').Trim()
if ($LASTEXITCODE -or -not $Upstream) { throw 'Cannot resolve the current branch upstream.' }
$RemoteCommit = (& git -C $RepoRoot rev-parse $Upstream).Trim()
$ResolvedApproval = (& git -C $RepoRoot rev-parse "$ApprovedCommit^{commit}").Trim()
if ($LASTEXITCODE -or $ResolvedApproval -ne $RemoteCommit) {
    throw "Approved commit does not match upstream HEAD: $RemoteCommit"
}
git -C $RepoRoot merge --ff-only $ResolvedApproval
if ($LASTEXITCODE) { throw 'Fast-forward update failed' }
$Profiles = @(Get-Content -LiteralPath $Manifest | Where-Object { $_.Trim() })
& (Join-Path $PSScriptRoot 'install.ps1') -Profile $Profiles -Force:$Force
if (-not $?) { exit 1 }
& (Join-Path $PSScriptRoot 'doctor.ps1')
if (-not $?) { exit 1 }
