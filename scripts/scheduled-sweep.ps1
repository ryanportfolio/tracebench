# Scheduled tracebench sweep: run both CLI lanes over the correction family,
# grade, render reports, commit the dated run dirs, and land them on main via
# a PR. Registered in Windows Task Scheduler (see scripts/register-sweep-task.ps1).
#
# Requirements on this machine: uv, git, gh (authenticated), claude CLI and
# codex CLI logged in. Consumes real subscription quota on both lanes.

$ErrorActionPreference = "Stop"
$RepoDir = "C:\Users\Home\CoreWise\tracebench"
$LogDir = Join-Path $RepoDir ".tmp\scheduled-sweep-logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Date = Get-Date -Format "yyyy-MM-dd"
$Log = Join-Path $LogDir "$Date.log"

function Step($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg
    $line | Tee-Object -FilePath $Log -Append
}

try {
    Set-Location $RepoDir
    Step "sync main"
    git checkout main 2>&1 | Tee-Object -FilePath $Log -Append
    git pull --ff-only origin main 2>&1 | Tee-Object -FilePath $Log -Append

    $Branch = "sweep/$Date"
    git checkout -B $Branch 2>&1 | Tee-Object -FilePath $Log -Append

    $Lanes = @(
        @{ Config = "configs/scheduled-claude-code.yaml"; Dir = "results/runs/sched-$Date-claude-code"; Title = "scheduled correction - claude-sonnet-5 (Claude Code CLI)" },
        @{ Config = "configs/scheduled-codex.yaml";       Dir = "results/runs/sched-$Date-codex";       Title = "scheduled correction - gpt-5.6-sol (Codex CLI)" }
    )

    foreach ($Lane in $Lanes) {
        Step "sweep $($Lane.Config) -> $($Lane.Dir)"
        uv run tracebench run --config $Lane.Config --out $Lane.Dir 2>&1 | Tee-Object -FilePath $Log -Append
        if ($LASTEXITCODE -ne 0) { throw "tracebench run failed for $($Lane.Config)" }
        uv run tracebench report --run-dir $Lane.Dir --out "$($Lane.Dir)/report.html" --title $Lane.Title 2>&1 | Tee-Object -FilePath $Log -Append
        if ($LASTEXITCODE -ne 0) { throw "tracebench report failed for $($Lane.Dir)" }
    }

    Step "self-check: new runs reproduce under graders at HEAD"
    uv run python scripts/check_regrade_drift.py 2>&1 | Tee-Object -FilePath $Log -Append
    if ($LASTEXITCODE -ne 0) { throw "regrade drift self-check failed" }

    Step "commit + push"
    foreach ($Lane in $Lanes) { git add $Lane.Dir }
    $MsgFile = Join-Path $RepoDir ".tmp\sweep-commit-msg.txt"
    @(
        "Scheduled correction-family sweep $Date (both CLI lanes)",
        "",
        "Automated weekly run of configs/scheduled-*.yaml via scripts/scheduled-sweep.ps1.",
        "Graded at HEAD; regrade drift self-check passed before commit.",
        "",
        "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
    ) | Set-Content -Path $MsgFile -Encoding utf8
    git commit -F $MsgFile 2>&1 | Tee-Object -FilePath $Log -Append
    git push -u origin $Branch 2>&1 | Tee-Object -FilePath $Log -Append

    Step "open + merge PR"
    gh pr create --base main --title "Scheduled correction sweep $Date" --body "Automated weekly sweep (both CLI lanes). Regrade drift self-check passed. Produced by scripts/scheduled-sweep.ps1." 2>&1 | Tee-Object -FilePath $Log -Append
    if ($LASTEXITCODE -ne 0) { throw "gh pr create failed" }
    gh pr merge $Branch --merge 2>&1 | Tee-Object -FilePath $Log -Append
    if ($LASTEXITCODE -ne 0) { throw "gh pr merge failed (branch protection or failing checks?) - PR left open for review" }

    Step "done"
    git checkout main 2>&1 | Tee-Object -FilePath $Log -Append
    git pull --ff-only origin main 2>&1 | Tee-Object -FilePath $Log -Append
}
catch {
    Step "FAILED: $_"
    exit 1
}
