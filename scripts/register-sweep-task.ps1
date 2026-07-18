# Register (or refresh) the weekly tracebench sweep in Windows Task Scheduler.
# Run once from an elevated-or-normal PowerShell; safe to re-run (replaces task).
#
#   powershell -ExecutionPolicy Bypass -File scripts\register-sweep-task.ps1
#
# Cadence: Mondays 09:00 local. The machine must be on (or the task fires at
# next startup if missed, via StartWhenAvailable). Remove with:
#   Unregister-ScheduledTask -TaskName "tracebench-weekly-sweep" -Confirm:$false

$ErrorActionPreference = "Stop"
$RepoDir = "C:\Users\Home\CoreWise\tracebench"
$Script = Join-Path $RepoDir "scripts\scheduled-sweep.ps1"

$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Script`"" `
    -WorkingDirectory $RepoDir
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 09:00
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 6) -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName "tracebench-weekly-sweep" `
    -Action $Action -Trigger $Trigger -Settings $Settings -Force

Write-Host "Registered 'tracebench-weekly-sweep' (Mondays 09:00, catch-up on missed runs)."
