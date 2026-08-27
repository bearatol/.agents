$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$TestRoot = Join-Path ([IO.Path]::GetTempPath()) ("agent-ecosystem-" + [guid]::NewGuid())
New-Item -ItemType Directory -Force -Path $TestRoot | Out-Null
$OriginalUserProfile = $env:USERPROFILE
$OriginalAgentsHome = $env:AGENTS_HOME
try {
  $env:USERPROFILE = Join-Path $TestRoot 'user'
  $env:AGENTS_HOME = Join-Path $TestRoot '.agents'
  New-Item -ItemType Directory -Force -Path $env:USERPROFILE | Out-Null
  & (Join-Path $RepoRoot 'scripts/install.ps1') -Profile all -HostName generic
  if ($LASTEXITCODE) { throw 'PowerShell install failed' }
  foreach ($Path in @(
    'skills/context-engineering/SKILL.md',
    'skills/security-gate/SKILL.md',
    'agents/ceo.md',
    'agents/ai-vulnerability-monitor.md',
    'agents/sales.md',
    'agents/seo-researcher.md',
    'agents/legal-content-reviewer.md',
    'tools/team/team.py',
    'catalog.json',
    'migrations.json'
  )) {
    if (-not (Test-Path -LiteralPath (Join-Path $env:AGENTS_HOME $Path))) { throw "Missing installed path: $Path" }
  }
  & (Join-Path $RepoRoot 'scripts/connect.ps1') -HostName codex,claude,gemini,sourcecraft,koda
  if ($LASTEXITCODE) { throw 'PowerShell host connection failed' }
  foreach ($Path in @(
    '.codex/agents/ceo.toml',
    '.claude/agents/engineer.md',
    '.gemini/agents/marketer.md',
    '.config/opencode/agents/seo-researcher.md',
    '.codeassistant/rules/agent-ecosystem.md'
  )) {
    if (-not (Test-Path -LiteralPath (Join-Path $env:USERPROFILE $Path))) { throw "Missing host adapter: $Path" }
  }
  & (Join-Path $RepoRoot 'scripts/doctor.ps1')
  if ($LASTEXITCODE) { throw 'PowerShell doctor failed' }

  $CustomizedSkill = Join-Path $env:AGENTS_HOME 'skills/context-engineering/SKILL.md'
  Add-Content -LiteralPath $CustomizedSkill -Value 'local customization'
  & pwsh -NoProfile -File (Join-Path $RepoRoot 'scripts/install.ps1') `
    -Profile core -NoRootFiles -Force
  if ($LASTEXITCODE -eq 0) { throw 'Force accepted a user-modified managed skill.' }
  if (-not (Select-String -LiteralPath $CustomizedSkill -SimpleMatch 'local customization')) {
    throw 'Force replaced a user-modified managed skill.'
  }

  $SafeUserProfile = $env:USERPROFILE
  $ReparseUser = Join-Path $TestRoot 'reparse-user'
  $Outside = Join-Path $TestRoot 'outside'
  $CodexRoot = Join-Path $ReparseUser '.codex'
  New-Item -ItemType Directory -Force -Path $CodexRoot,$Outside | Out-Null
  New-Item -ItemType Junction -Path (Join-Path $CodexRoot 'skills') -Target $Outside | Out-Null
  $env:USERPROFILE = $ReparseUser
  & pwsh -NoProfile -File (Join-Path $RepoRoot 'scripts/connect.ps1') -HostName codex
  if ($LASTEXITCODE -eq 0) { throw 'Host connection followed a junction outside its safety root.' }
  $env:USERPROFILE = $SafeUserProfile
  Write-Host 'All PowerShell tests passed.'
}
finally {
  $env:USERPROFILE = $OriginalUserProfile
  $env:AGENTS_HOME = $OriginalAgentsHome
  Remove-Item -LiteralPath $TestRoot -Recurse -Force
}
