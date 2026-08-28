[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('setup', 'status', 'export', 'restore', 'doctor', 'help')]
    [string] $Command,
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]] $Arguments = @()
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'AgentEcosystem.psm1') -Force
$RepoRoot = Get-AeRepoRoot
$AgentsHome = Get-AeAgentsHome
$Python = Get-Command python3, python, py -ErrorAction SilentlyContinue | Select-Object -First 1

function Show-Usage {
    Write-Host 'Usage: agents.ps1 setup [-Work NAME ...] [-App NAME]'
    Write-Host '       agents.ps1 status'
    Write-Host '       agents.ps1 export OUTPUT.json'
    Write-Host '       agents.ps1 restore MANIFEST.json'
    Write-Host '       agents.ps1 doctor'
}

try {
    switch ($Command) {
        'setup' {
            & (Join-Path $PSScriptRoot 'bootstrap.ps1') @Arguments
            if (-not $?) { exit 1 }
        }
        'status' {
            if ($Arguments.Count -ne 0) { throw 'status takes no arguments' }
            if (-not $Python) { throw 'Python 3 is required.' }
            & $Python.Source (Join-Path $PSScriptRoot 'environment.py') status `
                --repo $RepoRoot --home $AgentsHome --user-home (Get-AeUserHome)
            if ($LASTEXITCODE) { exit $LASTEXITCODE }
        }
        'export' {
            if ($Arguments.Count -ne 1) { throw 'usage: agents.ps1 export OUTPUT.json' }
            if (-not $Python) { throw 'Python 3 is required.' }
            & $Python.Source (Join-Path $PSScriptRoot 'environment.py') export `
                --repo $RepoRoot --home $AgentsHome --user-home (Get-AeUserHome) --output $Arguments[0]
            if ($LASTEXITCODE) { exit $LASTEXITCODE }
        }
        'restore' {
            if ($Arguments.Count -ne 1) { throw 'usage: agents.ps1 restore MANIFEST.json' }
            if (-not $Python) { throw 'Python 3 is required.' }
            $Plan = @(& $Python.Source (Join-Path $PSScriptRoot 'environment.py') restore-plan `
                --repo $RepoRoot --manifest $Arguments[0])
            if ($LASTEXITCODE) { exit $LASTEXITCODE }
            $Profiles = New-Object Collections.Generic.List[string]
            $Components = New-Object Collections.Generic.List[string]
            $Hosts = New-Object Collections.Generic.List[string]
            foreach ($Line in $Plan) {
                $Parts = $Line -split "`t", 2
                if ($Parts.Count -ne 2) { throw 'Invalid internal restore plan.' }
                switch ($Parts[0]) {
                    'profile' { [void]$Profiles.Add($Parts[1]) }
                    'component' { [void]$Components.Add($Parts[1]) }
                    'host' { [void]$Hosts.Add($Parts[1]) }
                    default { throw 'Invalid internal restore plan.' }
                }
            }
            if ($Profiles.Count -eq 0 -and $Components.Count -eq 0) {
                throw 'Manifest selects no profiles or components.'
            }

            Install-AeComponents -Profiles $Profiles.ToArray() -Components $Components.ToArray() `
                -Hosts @() -DryRun

            $PreflightRoot = Join-Path ([IO.Path]::GetTempPath()) ('.ae-restore-' + [Guid]::NewGuid().ToString('N'))
            $SavedAgentsHome = $env:AGENTS_HOME
            try {
                $env:AGENTS_HOME = Join-Path $PreflightRoot 'agents'
                Install-AeComponents -Profiles $Profiles.ToArray() -Components $Components.ToArray() `
                    -Hosts @()
                $ExistingState = Join-Path $AgentsHome '.ecosystem-state-windows.json'
                if (Test-Path -LiteralPath $ExistingState -PathType Leaf) {
                    Copy-Item -LiteralPath $ExistingState `
                        -Destination (Join-Path $env:AGENTS_HOME '.ecosystem-state-windows.json') -Force
                }
                if ($Hosts.Count -gt 0) { Connect-AeHosts -Hosts $Hosts.ToArray() -DryRun }
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

            Install-AeComponents -Profiles $Profiles.ToArray() -Components $Components.ToArray() `
                -Hosts @()
            if ($Hosts.Count -gt 0) { Connect-AeHosts -Hosts $Hosts.ToArray() -DryRun; Connect-AeHosts -Hosts $Hosts.ToArray() }
            Invoke-AeDoctor
        }
        'doctor' {
            if ($Arguments.Count -ne 0) { throw 'doctor takes no arguments' }
            Invoke-AeDoctor
        }
        'help' { Show-Usage }
    }
} catch {
    Write-Error $_
    exit 1
}
