[CmdletBinding()]
param(
  [string[]]$Profile = @('core'),
  [ValidateSet('codex','claude','gemini','koda','sourcecraft','generic')]
  [string[]]$HostName = @('generic')
)
& (Join-Path $PSScriptRoot 'install.ps1') -Profile $Profile -HostName $HostName
if (-not $?) { exit 1 }
