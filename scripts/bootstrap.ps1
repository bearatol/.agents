[CmdletBinding()]
param(
  [ValidateSet('code','research','writing','design','video','complex','local-ai','all')]
  [string[]]$Work = @(),
  [ValidateSet('codex','claude','gemini','kimi','koda','sourcecraft','generic')]
  [string[]]$App = @(),
  [string[]]$Profile = @(),
  [string[]]$Component = @(),
  [ValidateSet('codex','claude','gemini','kimi','koda','sourcecraft','generic')]
  [string[]]$HostName = @(),
  [switch]$Force,
  [switch]$DryRun,
  [switch]$NoRootFiles,
  [switch]$PreserveAgentsFile
)

$ErrorActionPreference = 'Stop'

function Add-UniqueValue([System.Collections.Generic.List[string]]$Values, [string]$Value) {
  if (-not $Values.Contains($Value)) { [void]$Values.Add($Value) }
}

function Resolve-WorkChoice([string]$Choice) {
  switch ($Choice) {
    'code' { return @{ Profile = 'software'; Name = 'Write and test code' } }
    'research' { return @{ Profile = 'marketing'; Name = 'Research and marketing' } }
    'writing' { return @{ Profile = 'content'; Name = 'Write documents and texts' } }
    'design' { return @{ Profile = 'design'; Name = 'Design interfaces' } }
    'video' { return @{ Profile = 'video'; Name = 'Make videos' } }
    'complex' { return @{ Profile = 'context'; Name = 'Organize complex tasks' } }
    'local-ai' { return @{ Profile = 'local-models'; Name = 'Use a local AI helper' } }
    'all' { return @{ Profile = 'all'; Name = 'Everything' } }
    default { throw "Unsupported work choice: $Choice" }
  }
}

$Interactive = $Work.Count -eq 0 -and $Profile.Count -eq 0 -and $Component.Count -eq 0 -and $App.Count -eq 0 -and $HostName.Count -eq 0
if ($Interactive) {
  Write-Host '.agents setup'
  Write-Host ''
  Write-Host 'Choose one or more areas. Common checks and helpers are added automatically.'
  Write-Host '  1) Write and test code'
  Write-Host '  2) Research and marketing'
  Write-Host '  3) Write documents and texts'
  Write-Host '  4) Design interfaces'
  Write-Host '  5) Make videos'
  Write-Host '  6) Organize complex tasks'
  Write-Host '  7) Use a local AI helper'
  Write-Host '  8) Everything'
  $Choices = Read-Host 'Your choices (for example 1,5) [1]'
  if ([string]::IsNullOrWhiteSpace($Choices)) { $Choices = '1' }
  $Numbers = @($Choices -split ',' | ForEach-Object { $_.Trim() })
  if ($Numbers.Count -eq 0 -or $Numbers -contains '') { throw 'Choose at least one number.' }
  $NumberMap = @{ '1' = 'code'; '2' = 'research'; '3' = 'writing'; '4' = 'design'; '5' = 'video'; '6' = 'complex'; '7' = 'local-ai'; '8' = 'all' }
  $Work = @($Numbers | ForEach-Object {
    if (-not $NumberMap.ContainsKey($_)) { throw "Unsupported choice: $_" }
    $NumberMap[$_]
  })
  $AppChoice = Read-Host 'AI application (codex, claude, gemini, kimi, koda, sourcecraft, generic) [generic]'
  if ([string]::IsNullOrWhiteSpace($AppChoice)) { $AppChoice = 'generic' }
  if ($AppChoice -notin @('codex','claude','gemini','kimi','koda','sourcecraft','generic')) { throw "Unsupported AI application: $AppChoice" }
  $App = @($AppChoice)
}

$Profiles = New-Object 'System.Collections.Generic.List[string]'
foreach ($Item in $Profile) { Add-UniqueValue $Profiles $Item }
$SelectionNames = New-Object 'System.Collections.Generic.List[string]'
foreach ($Choice in $Work) {
  $Resolved = Resolve-WorkChoice $Choice
  if ($Resolved.Profile -eq 'all' -and $Profiles.Contains('all')) { continue }
  if ($Resolved.Profile -eq 'all' -and $Profiles.Count -gt 0) { throw '"all" cannot be combined with another work choice.' }
  if ($Resolved.Profile -ne 'all' -and $Profiles.Contains('all')) { throw '"all" cannot be combined with another work choice.' }
  Add-UniqueValue $Profiles $Resolved.Profile
  Add-UniqueValue $SelectionNames $Resolved.Name
}
if ($Profiles.Count -eq 0 -and $Component.Count -eq 0) { throw 'Choose at least one work area.' }
Add-UniqueValue $Profiles 'core'

$Hosts = New-Object 'System.Collections.Generic.List[string]'
foreach ($Item in $HostName) { Add-UniqueValue $Hosts $Item }
foreach ($Item in $App) { Add-UniqueValue $Hosts $Item }
if ($Hosts.Count -eq 0 -and ($Interactive -or $Work.Count -gt 0)) { Add-UniqueValue $Hosts 'generic' }

if ($Interactive) {
  Write-Host ''
  Write-Host ("You selected: {0}" -f ($SelectionNames -join ', '))
  Write-Host ("AI application: {0}" -f ($Hosts -join ', '))
  $Answer = Read-Host 'Continue? [y/N]'
  if ($Answer -notin @('y', 'Y')) { exit 0 }
}

$InstallArguments = @{ Profile = $Profiles.ToArray(); Component = $Component; HostName = $Hosts.ToArray() }
if ($Force) { $InstallArguments.Force = $true }
if ($DryRun) { $InstallArguments.DryRun = $true }
if ($NoRootFiles) { $InstallArguments.NoRootFiles = $true }
if ($PreserveAgentsFile) { $InstallArguments.PreserveAgentsFile = $true }
& (Join-Path $PSScriptRoot 'install.ps1') @InstallArguments
if (-not $?) { exit 1 }
