<#
.SYNOPSIS
    Universal Windows installer for the ashiba-keisan AI Agent Skill.
.DESCRIPTION
    Installs skills/ashiba-keisan into one or more AI coding agent skill directories.
    Works both inside a cloned repository and as a standalone remote one-liner:
      irm https://raw.githubusercontent.com/RingLord3812/ashiba-keisan/main/install.ps1 | iex
.PARAMETER Target
    One of: agents (default), antigravity, claude, codex, cursor, gemini, copilot, windsurf, project, all
.PARAMETER Repo
    GitHub repository slug (default: RingLord3812/ashiba-keisan)
.PARAMETER Branch
    Git branch (default: main)
#>
param(
    [ValidateSet("agents", "antigravity", "claude", "codex", "cursor", "gemini", "copilot", "windsurf", "project", "all")]
    [string]$Target = "agents",
    [string]$Repo = "RingLord3812/ashiba-keisan",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
$SkillName = "ashiba-keisan"
$HomeDir = $env:USERPROFILE

$TargetMap = @{
    "agents"      = Join-Path $HomeDir ".agents\skills\$SkillName"
    "antigravity" = Join-Path $HomeDir ".gemini\config\skills\$SkillName"
    "claude"      = Join-Path $HomeDir ".claude\skills\$SkillName"
    "codex"       = Join-Path $HomeDir ".codex\skills\$SkillName"
    "cursor"      = Join-Path $HomeDir ".cursor\skills\$SkillName"
    "gemini"      = Join-Path $HomeDir ".gemini\skills\$SkillName"
    "copilot"     = Join-Path $HomeDir ".copilot\skills\$SkillName"
    "windsurf"    = Join-Path $HomeDir ".codeium\windsurf\skills\$SkillName"
    "project"     = Join-Path (Get-Location).Path ".agents\skills\$SkillName"
}

$ScriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$LocalSource = Join-Path $ScriptRoot "skills\$SkillName"
$TempDir = $null

try {
    if (Test-Path (Join-Path $LocalSource "SKILL.md")) {
        $SourceDir = $LocalSource
        Write-Host "[ashiba-keisan] Using local skill source: $SourceDir"
    } else {
        $TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("ashiba-keisan-" + [System.Guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
        $ZipPath = Join-Path $TempDir "repo.zip"
        $ZipUrl = "https://github.com/$Repo/archive/refs/heads/$Branch.zip"
        Write-Host "[ashiba-keisan] Downloading $ZipUrl ..."
        Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
        Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force
        $ExtractedRoot = Get-ChildItem -Directory $TempDir | Select-Object -First 1
        $SourceDir = Join-Path $ExtractedRoot.FullName "skills\$SkillName"
        if (-not (Test-Path (Join-Path $SourceDir "SKILL.md"))) {
            throw "SKILL.md not found inside downloaded archive."
        }
    }

    $Targets = if ($Target -eq "all") {
        @("agents", "antigravity", "claude", "codex", "cursor", "gemini", "copilot", "windsurf")
    } else {
        @($Target)
    }

    $FirstDest = $null
    foreach ($t in $Targets) {
        $Dest = $TargetMap[$t]
        if (-not $FirstDest) { $FirstDest = $Dest }
        $Parent = Split-Path -Parent $Dest
        New-Item -ItemType Directory -Force -Path $Parent | Out-Null
        if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
        robocopy $SourceDir $Dest /E /XD __pycache__ .pytest_cache /XF *.pyc | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "Failed to copy skill to $Dest (robocopy exit $LASTEXITCODE)" }
        Write-Host "[OK] Installed ($t) -> $Dest"
    }

    Write-Host "`nDone! Verify with:"
    Write-Host "  python -m unittest discover -s `"$FirstDest\tests`" -v"
} finally {
    if ($TempDir -and (Test-Path $TempDir)) {
        Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    }
}
