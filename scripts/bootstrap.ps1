[CmdletBinding()]
param(
  [string[]]$Profile = @(),
  [ValidateSet('codex','claude','gemini','koda','sourcecraft','generic')]
  [string[]]$HostName = @()
)

$ErrorActionPreference = 'Stop'
if ($Profile.Count -gt 0 -or $HostName.Count -gt 0) {
  if ($Profile.Count -eq 0) { $Profile = @('core') }
  if ($HostName.Count -eq 0) { $HostName = @('generic') }
  & (Join-Path $PSScriptRoot 'install.ps1') -Profile $Profile -HostName $HostName
  if (-not $?) { exit 1 }
  exit 0
}

Write-Host '.agents setup'
Write-Host ''
Write-Host 'Foundation is always included. Choose one work pack and one host.'
$WorkPack = Read-Host 'Work pack (software, marketing, content, design, video, context, local-models) [software]'
if ([string]::IsNullOrWhiteSpace($WorkPack)) { $WorkPack = 'software' }
$AllowedPacks = @('software', 'marketing', 'content', 'design', 'video', 'context', 'local-models')
if ($WorkPack -notin $AllowedPacks) {
  Write-Error "Unsupported work pack: $WorkPack"
  exit 1
}

$HostChoice = Read-Host 'Host (codex, claude, gemini, koda, sourcecraft, generic) [generic]'
if ([string]::IsNullOrWhiteSpace($HostChoice)) { $HostChoice = 'generic' }
$AllowedHosts = @('codex', 'claude', 'gemini', 'koda', 'sourcecraft', 'generic')
if ($HostChoice -notin $AllowedHosts) {
  Write-Error "Unsupported host: $HostChoice"
  exit 1
}

Write-Host ''
Write-Host "Planned setup: Foundation + $WorkPack for $HostChoice"
$Answer = Read-Host 'Continue? [y/N]'
if ($Answer -notin @('y', 'Y')) { exit 0 }
& (Join-Path $PSScriptRoot 'install.ps1') -Profile @('core', $WorkPack) -HostName @($HostChoice)
if (-not $?) { exit 1 }
