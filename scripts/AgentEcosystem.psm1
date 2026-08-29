Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-AeRepoRoot {
    return [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
}

function Get-AeUserHome {
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        return [IO.Path]::GetFullPath($env:USERPROFILE)
    }
    return [IO.Path]::GetFullPath([Environment]::GetFolderPath('UserProfile'))
}

function Get-AeAgentsHome {
    $candidate = $env:AGENTS_HOME
    if ([string]::IsNullOrWhiteSpace($candidate)) {
        $candidate = Join-Path (Get-AeUserHome) '.agents'
    }
    $path = [IO.Path]::GetFullPath($candidate)
    $root = [IO.Path]::GetPathRoot($path)
    $user = Get-AeUserHome
    if ($path -eq $root -or $path.TrimEnd('\', '/') -eq $user.TrimEnd('\', '/')) {
        throw "Refusing unsafe AGENTS_HOME: $path"
    }
    Assert-AeNoReparseTraversal -Path $path
    return $path
}

function Assert-AeName([string] $Name) {
    if ($Name -notmatch '^[a-z0-9][a-z0-9-]*$') {
        throw "Invalid component name: $Name"
    }
}

function Test-AeChildPath([string] $Path, [string] $Parent) {
    $fullPath = [IO.Path]::GetFullPath($Path)
    $fullParent = [IO.Path]::GetFullPath($Parent).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    return $fullPath.StartsWith($fullParent, [StringComparison]::OrdinalIgnoreCase)
}

function Assert-AeNoReparseTraversal([string] $Path) {
    $fullPath = [IO.Path]::GetFullPath($Path)
    $current = [IO.Path]::GetPathRoot($fullPath)
    $relative = $fullPath.Substring($current.Length)
    foreach ($segment in @($relative -split '[\\/]' | Where-Object { $_ })) {
        $current = Join-Path $current $segment
        if (-not (Test-Path -LiteralPath $current)) { continue }
        $item = Get-Item -LiteralPath $current -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Refusing reparse-point traversal: $current"
        }
    }
}

function Assert-AeSafeDestination([string] $Path, [string] $SafetyRoot) {
    if (-not (Test-AeChildPath -Path $Path -Parent $SafetyRoot)) {
        throw "Destination escaped its safety root: $Path"
    }
    Assert-AeNoReparseTraversal -Path $SafetyRoot
    Assert-AeNoReparseTraversal -Path $Path
}

function Get-AeComponentSource([string] $Root, [string] $Kind, [string] $Name) {
    switch ($Kind) {
        'skill' { return Join-Path $Root "library/skills/$Name" }
        'agent' { return Join-Path $Root "library/agents/$Name.md" }
        'rule' { return Join-Path $Root "library/rules/$Name.md" }
        'model' { return Join-Path $Root "library/models/$Name" }
        'orchestration' { return Join-Path $Root 'library/orchestration' }
        'tool' { return Join-Path $Root "library/tools/$Name" }
        default { throw "Unknown component kind: $Kind" }
    }
}

function Get-AeComponentDestination([string] $HomePath, [string] $Kind, [string] $Name) {
    switch ($Kind) {
        'skill' { return Join-Path $HomePath "skills/$Name" }
        'agent' { return Join-Path $HomePath "agents/$Name.md" }
        'rule' { return Join-Path $HomePath "rules/$Name.md" }
        'model' { return Join-Path $HomePath "local-models/$Name" }
        'orchestration' { return Join-Path $HomePath 'orchestration' }
        'tool' { return Join-Path $HomePath "tools/$Name" }
        default { throw "Unknown component kind: $Kind" }
    }
}

function Expand-AeProfile {
    param(
        [Parameter(Mandatory = $true)][string] $Root,
        [Parameter(Mandatory = $true)][string] $Profile,
        [string[]] $Stack = @()
    )
    Assert-AeName $Profile
    if ($Stack -contains $Profile) {
        throw "Profile cycle: $($Stack + $Profile -join ' -> ')"
    }
    $file = Join-Path $Root "profiles/$Profile.profile"
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Unknown profile: $Profile"
    }
    foreach ($raw in [IO.File]::ReadAllLines($file)) {
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith('#')) { continue }
        if ($line.StartsWith('profile:')) {
            Expand-AeProfile -Root $Root -Profile $line.Substring(8) -Stack ($Stack + $Profile)
        } else {
            $line
        }
    }
}

function Resolve-AeComponents([string] $Root, [string[]] $Profiles, [string[]] $Components) {
    $seen = @{}
    $result = New-Object Collections.Generic.List[string]
    foreach ($profile in $Profiles) {
        foreach ($component in @(Expand-AeProfile -Root $Root -Profile $profile)) {
            if (-not $seen.ContainsKey($component)) {
                $seen[$component] = $true
                [void]$result.Add($component)
            }
        }
    }
    foreach ($component in $Components) {
        if (-not $seen.ContainsKey($component)) {
            $seen[$component] = $true
            [void]$result.Add($component)
        }
    }
    return $result.ToArray()
}

function Get-AePathHash([string] $Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            $stream = [IO.File]::OpenRead($Path)
            try { return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
            finally { $stream.Dispose() }
        }
        $root = [IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
        $items = @(Get-ChildItem -LiteralPath $root -File -Recurse | Sort-Object FullName)
        $builder = New-Object Text.StringBuilder
        foreach ($item in $items) {
            $relative = $item.FullName.Substring($root.Length).TrimStart('\', '/').Replace('\', '/')
            $stream = [IO.File]::OpenRead($item.FullName)
            try { $hash = ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
            finally { $stream.Dispose() }
            [void]$builder.Append($relative).Append([char]0).Append($hash).Append([char]10)
        }
        $bytes = [Text.Encoding]::UTF8.GetBytes($builder.ToString())
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

function Read-AeState([string] $StatePath) {
    $state = @{}
    if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) { return $state }
    try {
        $data = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
        foreach ($entry in @($data.entries)) {
            if ($null -eq $entry -or $entry.id -isnot [string] -or $entry.hash -isnot [string] -or
                [string]::IsNullOrWhiteSpace($entry.id) -or [string]::IsNullOrWhiteSpace($entry.hash)) {
                throw "Invalid ecosystem state entry in: $StatePath"
            }
            if ($state.ContainsKey([string]$entry.id)) {
                throw "Duplicate ecosystem state entry: $($entry.id)"
            }
            $state[[string]$entry.id] = [string]$entry.hash
        }
    } catch {
        throw "Invalid ecosystem state file: $StatePath"
    }
    return $state
}

function Write-AeState([hashtable] $State, [string] $StatePath) {
    $entries = @($State.Keys | Sort-Object | ForEach-Object {
        [ordered]@{ id = $_; hash = $State[$_] }
    })
    $document = [ordered]@{ version = 1; entries = $entries }
    $parent = Split-Path -Parent $StatePath
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $temporary = Join-Path $parent ('.ecosystem-state-{0}.tmp' -f [Guid]::NewGuid().ToString('N'))
    try {
        $document | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $temporary -Encoding UTF8
        Move-Item -LiteralPath $temporary -Destination $StatePath -Force
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}

function Write-AeManagedLines {
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][string[]] $Values,
        [Parameter(Mandatory = $true)][string] $SafetyRoot
    )
    Assert-AeSafeDestination -Path $Path -SafetyRoot $SafetyRoot
    $parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Assert-AeSafeDestination -Path $Path -SafetyRoot $SafetyRoot
    $temporary = Join-Path $parent ('.ecosystem-selection-{0}.tmp' -f [Guid]::NewGuid().ToString('N'))
    try {
        [IO.File]::WriteAllLines($temporary, $Values, [Text.UTF8Encoding]::new($false))
        Assert-AeSafeDestination -Path $Path -SafetyRoot $SafetyRoot
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}

function Copy-AeManagedPath {
    param(
        [Parameter(Mandatory = $true)][string] $Source,
        [Parameter(Mandatory = $true)][string] $Destination,
        [Parameter(Mandatory = $true)][string] $StateId,
        [Parameter(Mandatory = $true)][hashtable] $State,
        [Parameter(Mandatory = $true)][string] $SafetyRoot,
        [switch] $Force,
        [switch] $DryRun
    )
    if (-not (Test-Path -LiteralPath $Source)) { throw "Missing source: $Source" }
    Assert-AeSafeDestination -Path $Destination -SafetyRoot $SafetyRoot
    $sourceHash = Get-AePathHash $Source
    $destinationHash = Get-AePathHash $Destination
    if ($DryRun) {
        # A preflight may render host wrappers from a temporary installation.
        # Their instructions contain that temporary path, so comparing their
        # bytes with an already installed wrapper would incorrectly report a
        # conflict.  Ownership is the relevant check during a preflight: a
        # destination is safe to update only when it is absent or still has
        # the hash recorded for this managed state entry.
        if ($destinationHash -eq $sourceHash) {
            Write-Host "unchanged  $StateId"
            $State[$StateId] = $destinationHash
            return @{ Installed = $false; Conflict = $false }
        }
        if ($null -ne $destinationHash -and
            (-not $State.ContainsKey($StateId) -or $State[$StateId] -ne $destinationHash)) {
            Write-Error "conflict   $StateId ($Destination)" -ErrorAction Continue
            return @{ Installed = $false; Conflict = $true }
        }
        Write-Host "would-install  $StateId -> $Destination"
        return @{ Installed = $false; Conflict = $false }
    }
    if ($destinationHash -eq $sourceHash) {
        Write-Host "unchanged  $StateId"
        $State[$StateId] = $destinationHash
        return @{ Installed = $false; Conflict = $false }
    }
    if ($null -ne $destinationHash) {
        if (-not $State.ContainsKey($StateId) -or $State[$StateId] -ne $destinationHash) {
            Write-Error "conflict   $StateId ($Destination)" -ErrorAction Continue
            return @{ Installed = $false; Conflict = $true }
        }
        Write-Host "updating   $StateId"
    }
    $parent = Split-Path -Parent $Destination
    Assert-AeSafeDestination -Path $Destination -SafetyRoot $SafetyRoot
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Assert-AeSafeDestination -Path $Destination -SafetyRoot $SafetyRoot
    $stage = Join-Path $parent ('.ae-{0}.tmp' -f [Guid]::NewGuid().ToString('N'))
    try {
        if (Test-Path -LiteralPath $Source -PathType Container) {
            New-Item -ItemType Directory -Path $stage | Out-Null
            Get-ChildItem -LiteralPath $Source -Force | Copy-Item -Destination $stage -Recurse -Force
        } else {
            Copy-Item -LiteralPath $Source -Destination $stage -Force
        }
        if (Test-Path -LiteralPath $Destination) {
            Assert-AeSafeDestination -Path $Destination -SafetyRoot $SafetyRoot
            Remove-Item -LiteralPath $Destination -Recurse -Force
        }
        Move-Item -LiteralPath $stage -Destination $Destination
    } finally {
        if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    }
    $State[$StateId] = Get-AePathHash $Destination
    Write-Host "installed  $StateId"
    return @{ Installed = $true; Conflict = $false }
}

function Get-AePython {
    foreach ($candidate in @('python3', 'python', 'py')) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) { return $command.Source }
    }
    return $null
}

function Install-AeComponents {
    param(
        [string[]] $Profiles,
        [string[]] $Components,
        [string[]] $Hosts,
        [switch] $Force,
        [switch] $DryRun,
        [switch] $NoRootFiles,
        [switch] $PreserveAgentsFile
    )
    if ($Profiles.Count -eq 0 -and $Components.Count -eq 0) {
        throw 'Select at least one profile or component.'
    }
    $root = Get-AeRepoRoot
    $homePath = Get-AeAgentsHome
    $statePath = Join-Path $homePath '.ecosystem-state-windows.json'
    $state = Read-AeState $statePath
    $selected = @(Resolve-AeComponents -Root $root -Profiles $Profiles -Components $Components)
    $installed = New-Object Collections.Generic.List[string]
    $installedCount = 0
    $conflicts = 0
    foreach ($component in $selected) {
        if ($component -notmatch '^([^:]+):(.+)$') { throw "Invalid component entry: $component" }
        $kind = $Matches[1]
        $name = $Matches[2]
        Assert-AeName $name
        $source = Get-AeComponentSource $root $kind $name
        $destination = Get-AeComponentDestination $homePath $kind $name
        $result = Copy-AeManagedPath -Source $source -Destination $destination -StateId $component -State $state -SafetyRoot $homePath -Force:$Force -DryRun:$DryRun
        if ($result.Conflict) { $conflicts++ } else { [void]$installed.Add($component) }
        if ($result.Installed) { $installedCount++ }
    }
    if (-not $NoRootFiles) {
        $roots = @(
            @{ Source = Join-Path $root 'CONNECT.md'; Destination = Join-Path $homePath 'CONNECT.md'; Id = 'root:CONNECT.md' },
            @{ Source = Join-Path $root 'catalog/catalog.json'; Destination = Join-Path $homePath 'catalog.json'; Id = 'root:catalog.json' },
            @{ Source = Join-Path $root 'catalog/migrations.json'; Destination = Join-Path $homePath 'migrations.json'; Id = 'root:migrations.json' }
        )
        if (-not $PreserveAgentsFile) {
            $roots += @{ Source = Join-Path $root 'AGENTS.md'; Destination = Join-Path $homePath 'AGENTS.md'; Id = 'root:AGENTS.md' }
        }
        foreach ($item in $roots) {
            $result = Copy-AeManagedPath -Source $item.Source -Destination $item.Destination -StateId $item.Id -State $state -SafetyRoot $homePath -Force:$Force -DryRun:$DryRun
            if ($result.Conflict) { $conflicts++ }
            if ($result.Installed) { $installedCount++ }
        }
    }
    if (-not $DryRun) {
        Write-AeState $state $statePath
        $manifest = Join-Path $homePath '.ecosystem-installed'
        $old = if (Test-Path -LiteralPath $manifest) { @(Get-Content -LiteralPath $manifest) } else { @() }
        Write-AeManagedLines -Path $manifest `
            -Values @($old + $installed | Where-Object { $_ } | Sort-Object -Unique) -SafetyRoot $homePath
        $componentManifest = Join-Path $homePath '.ecosystem-components'
        $oldComponents = if (Test-Path -LiteralPath $componentManifest) { @(Get-Content -LiteralPath $componentManifest) } else { @() }
        $completedComponents = @($Components | Where-Object { $installed -contains $_ })
        Write-AeManagedLines -Path $componentManifest `
            -Values @($oldComponents + $completedComponents | Where-Object { $_ } | Sort-Object -Unique) `
            -SafetyRoot $homePath
        if ($conflicts -gt 0) {
            Write-Host "Finished: $installedCount installed, $conflicts conflicts."
            throw "$conflicts conflict(s) require review."
        }
        $profileManifest = Join-Path $homePath '.ecosystem-profiles'
        $oldProfiles = if (Test-Path -LiteralPath $profileManifest) { @(Get-Content -LiteralPath $profileManifest) } else { @() }
        Write-AeManagedLines -Path $profileManifest `
            -Values @($oldProfiles + $Profiles | Where-Object { $_ } | Sort-Object -Unique) `
            -SafetyRoot $homePath
        if ($Hosts.Count -gt 0) {
            Connect-AeHosts -Hosts $Hosts -Force:$Force -DryRun
            Connect-AeHosts -Hosts $Hosts -Force:$Force
        }
    }
    Write-Host "Finished: $installedCount installed, $conflicts conflicts."
    if ($conflicts -gt 0) { throw "$conflicts conflict(s) require review." }
}

function Get-AeHostPaths([string] $HostName) {
    $user = Get-AeUserHome
    switch ($HostName) {
        'codex' { return @{ Skills = Join-Path $user '.codex/skills'; Agents = Join-Path $user '.codex/agents'; Render = 'codex' } }
        'claude' { return @{ Skills = Join-Path $user '.claude/skills'; Agents = Join-Path $user '.claude/agents'; Render = 'claude' } }
        'gemini' { return @{ Skills = Join-Path $user '.gemini/skills'; Agents = Join-Path $user '.gemini/agents'; Render = 'gemini' } }
        'sourcecraft' { return @{ Agents = Join-Path $user '.config/opencode/agents'; Render = 'sourcecraft' } }
        'generic' { return $null }
        default { throw "Unsupported host: $HostName" }
    }
}

function Connect-AeHosts {
    param([Parameter(Mandatory = $true)][string[]] $Hosts, [switch] $Force, [switch] $DryRun)
    $homePath = Get-AeAgentsHome
    $skills = Join-Path $homePath 'skills'
    if (-not (Test-Path -LiteralPath $skills -PathType Container)) { throw 'Install a profile before connecting hosts.' }
    $statePath = Join-Path $homePath '.ecosystem-state-windows.json'
    $state = Read-AeState $statePath
    $conflicts = 0
    foreach ($hostName in $Hosts) {
        if ($hostName -eq 'generic') {
            Write-Host "generic host: point the agent to $homePath/AGENTS.md and $homePath/CONNECT.md"
            continue
        }
        if ($hostName -eq 'koda') {
            Write-Host "koda host: skills are discovered directly from $homePath/skills; run 'koda skills list' to verify"
            continue
        }
        $paths = Get-AeHostPaths $hostName
        if ($hostName -ne 'sourcecraft') {
            foreach ($skill in @(Get-ChildItem -LiteralPath $skills -Directory)) {
                if (-not (Test-Path -LiteralPath (Join-Path $skill.FullName 'SKILL.md') -PathType Leaf)) { continue }
                $destination = Join-Path $paths.Skills $skill.Name
                $result = Copy-AeManagedPath -Source $skill.FullName -Destination $destination -StateId "host:$hostName:skill:$($skill.Name)" -State $state -SafetyRoot $paths.Skills -Force:$Force -DryRun:$DryRun
                if ($result.Conflict) { $conflicts++ }
            }
        }
        $python = Get-AePython
        if (-not $python) { throw 'Python 3 is required to render host subagents.' }
        $team = Join-Path $homePath 'tools/team/team.py'
        if (-not (Test-Path -LiteralPath $team -PathType Leaf)) { throw 'Install the core profile before connecting subagents.' }
        $renderStage = Join-Path ([IO.Path]::GetTempPath()) ('.ae-render-{0}' -f [Guid]::NewGuid().ToString('N'))
        try {
            New-Item -ItemType Directory -Path $renderStage | Out-Null
            & $python $team --home $homePath render-host --host $paths.Render --target $renderStage
            if ($LASTEXITCODE -ne 0) { throw "Failed to render $hostName agents." }
            foreach ($wrapper in @(Get-ChildItem -LiteralPath $renderStage -File)) {
                $destination = Join-Path $paths.Agents $wrapper.Name
                $stateName = [IO.Path]::GetFileNameWithoutExtension($wrapper.Name)
                $result = Copy-AeManagedPath -Source $wrapper.FullName -Destination $destination `
                    -StateId "host:$hostName:agent:$stateName" -State $state `
                    -SafetyRoot $paths.Agents -Force:$Force -DryRun:$DryRun
                if ($result.Conflict) { $conflicts++ }
            }
        } finally {
            if (Test-Path -LiteralPath $renderStage) {
                Remove-Item -LiteralPath $renderStage -Recurse -Force
            }
        }
        if ($hostName -eq 'sourcecraft') {
            $ruleRoot = Join-Path (Get-AeUserHome) '.codeassistant/rules'
            $ruleSource = Join-Path (Get-AeRepoRoot) 'library/hosts/sourcecraft-global-rule.md'
            $ruleDestination = Join-Path $ruleRoot 'agent-ecosystem.md'
            $result = Copy-AeManagedPath -Source $ruleSource -Destination $ruleDestination -StateId 'host:sourcecraft:rule:agent-ecosystem' -State $state -SafetyRoot $ruleRoot -Force:$Force -DryRun:$DryRun
            if ($result.Conflict) { $conflicts++ }
        }
    }
    if (-not $DryRun -and $conflicts -eq 0) {
        Write-AeState $state $statePath
        $hostManifest = Join-Path $homePath '.ecosystem-hosts'
        $oldHosts = if (Test-Path -LiteralPath $hostManifest) { @(Get-Content -LiteralPath $hostManifest) } else { @() }
        $mergedHosts = @($oldHosts) + @($Hosts)
        Write-AeManagedLines -Path $hostManifest `
            -Values @($mergedHosts | Where-Object { $_ } | Sort-Object -Unique) `
            -SafetyRoot $homePath
    }
    if ($conflicts -gt 0) { throw "$conflicts host adapter conflict(s) require review." }
}

function Test-AeWindowsHostSkillsState {
    $homePath = Get-AeAgentsHome
    $skills = Join-Path $homePath 'skills'
    $hostManifest = Join-Path $homePath '.ecosystem-hosts'
    $errors = 0
    $statePath = Join-Path $homePath '.ecosystem-state-windows.json'
    if ((Test-Path -LiteralPath $statePath -PathType Leaf) -and -not (Test-Path -LiteralPath $hostManifest -PathType Leaf)) {
        Write-Error 'host-conflicting host:manifest-missing' -ErrorAction Continue
        return $false
    }
    if (-not (Test-Path -LiteralPath $skills -PathType Container) -or -not (Test-Path -LiteralPath $hostManifest -PathType Leaf)) {
        return $true
    }
    $configuredHosts = @(Get-Content -LiteralPath $hostManifest)
    foreach ($hostName in @($configuredHosts | Where-Object { $_ -in @('codex', 'claude', 'gemini') })) {
        $paths = Get-AeHostPaths $hostName
        foreach ($skill in @(Get-ChildItem -LiteralPath $skills -Directory)) {
            if (-not (Test-Path -LiteralPath (Join-Path $skill.FullName 'SKILL.md') -PathType Leaf)) { continue }
            $stateId = "host:$hostName:skill:$($skill.Name)"
            $destination = Join-Path $paths.Skills $skill.Name
            try {
                Assert-AeSafeDestination -Path $skill.FullName -SafetyRoot $homePath
                Assert-AeSafeDestination -Path $destination -SafetyRoot $paths.Skills
                $sourceHash = Get-AePathHash $skill.FullName
                $destinationHash = Get-AePathHash $destination
                if ($null -eq $sourceHash -or $sourceHash -ne $destinationHash) {
                    Write-Error "host-conflicting $stateId" -ErrorAction Continue
                    $errors++
                } else {
                    Write-Host "current        $stateId"
                }
            } catch {
                Write-Error "host-conflicting $stateId" -ErrorAction Continue
                $errors++
            }
        }
    }
    if ($configuredHosts -contains 'sourcecraft') {
        $stateId = 'host:sourcecraft:rule:agent-ecosystem'
        $root = Get-AeRepoRoot
        $source = Join-Path $root 'library/hosts/sourcecraft-global-rule.md'
        $ruleRoot = Join-Path (Get-AeUserHome) '.codeassistant/rules'
        $destination = Join-Path $ruleRoot 'agent-ecosystem.md'
        try {
            Assert-AeSafeDestination -Path $source -SafetyRoot $root
            Assert-AeSafeDestination -Path $destination -SafetyRoot $ruleRoot
            if ((Get-AePathHash $source) -ne (Get-AePathHash $destination)) {
                Write-Error "host-conflicting $stateId" -ErrorAction Continue
                $errors++
            } else {
                Write-Host "current        $stateId"
            }
        } catch {
            Write-Error "host-conflicting $stateId" -ErrorAction Continue
            $errors++
        }
    }
    return $errors -eq 0
}

function Invoke-AeDoctor {
    $root = Get-AeRepoRoot
    $homePath = Get-AeAgentsHome
    $errors = 0
    $warnings = 0
    foreach ($profile in @(Get-ChildItem -LiteralPath (Join-Path $root 'profiles') -Filter '*.profile' -File)) {
        foreach ($raw in [IO.File]::ReadAllLines($profile.FullName)) {
            $line = $raw.Trim()
            if (-not $line -or $line.StartsWith('#') -or $line.StartsWith('profile:')) { continue }
            if ($line -notmatch '^([^:]+):(.+)$') { Write-Error "invalid component: $line" -ErrorAction Continue; $errors++; continue }
            if (-not (Test-Path -LiteralPath (Get-AeComponentSource $root $Matches[1] $Matches[2]))) {
                Write-Error "missing source for $line" -ErrorAction Continue; $errors++
            }
        }
    }
    $python = Get-AePython
    if (-not $python) {
        Write-Warning 'Python 3 is unavailable; catalog validation skipped.'
        $warnings++
    } else {
        & $python -m json.tool (Join-Path $root 'catalog/catalog.json') | Out-Null
        if ($LASTEXITCODE -ne 0) { $errors++ }
        & $python (Join-Path $root 'library/tools/team/team.py') --home $root validate-catalog --repo-root $root | Out-Null
        if ($LASTEXITCODE -ne 0) { $errors++ }
        & $python (Join-Path $root 'scripts/check_repository.py') $root
        if ($LASTEXITCODE -ne 0) { $errors++ }
    }
    $forbidden = @(Get-ChildItem -LiteralPath $root -File -Recurse | Where-Object {
        $_.Name -in @('.env') -or $_.Extension -in @('.safetensors', '.gguf', '.bin', '.pem', '.key')
    })
    if ($forbidden.Count -gt 0) { Write-Error 'forbidden secret or model artifact found' -ErrorAction Continue; $errors++ }
    $manifest = Join-Path $homePath '.ecosystem-installed'
    if (Test-Path -LiteralPath $manifest -PathType Leaf) {
        foreach ($component in @(Get-Content -LiteralPath $manifest | Where-Object { $_ })) {
            if ($component -notmatch '^([^:]+):(.+)$') { continue }
            $destination = Get-AeComponentDestination $homePath $Matches[1] $Matches[2]
            if (-not (Test-Path -LiteralPath $destination)) { Write-Warning "installed manifest entry is missing: $component"; $warnings++ }
        }
    } else {
        Write-Warning "no installation manifest at $manifest"
        $warnings++
    }
    if ($python -and (Test-Path -LiteralPath $manifest -PathType Leaf)) {
        & $python (Join-Path $root 'scripts/environment.py') status `
            --repo $root --home $homePath --user-home (Get-AeUserHome) --skip-windows-host-skills
        $environmentStatus = $LASTEXITCODE
        $hostSkillsCurrent = Test-AeWindowsHostSkillsState
        if ($environmentStatus -ne 0 -or -not $hostSkillsCurrent) {
            Write-Error 'installed environment has missing, stale, modified, or host-conflicting targets' -ErrorAction Continue
            $errors++
        }
    }
    Write-Host "Doctor finished: $errors errors, $warnings warnings."
    if ($errors -gt 0 -or $warnings -gt 0) { throw 'Doctor found errors or warnings.' }
}

Export-ModuleMember -Function Get-AeRepoRoot, Get-AeUserHome, Get-AeAgentsHome, Install-AeComponents, Connect-AeHosts, Invoke-AeDoctor, Test-AeWindowsHostSkillsState
