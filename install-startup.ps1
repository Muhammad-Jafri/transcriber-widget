#Requires -RunAsAdministrator
# Registers a Scheduled Task that launches transcriber-widget elevated at logon
# with NO UAC prompt (a Startup-folder shortcut can't do this for an admin app).
#
# Run ONCE from an elevated PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\install-startup.ps1
#
# Remove later with:  .\uninstall-startup.ps1

$ErrorActionPreference = "Stop"

$exe = Join-Path $PSScriptRoot "dist\transcriber-widget.exe"
if (-not (Test-Path $exe)) {
    throw "Not found: $exe`nBuild it first: uv run pyinstaller transcriber-widget.spec --clean --noconfirm"
}

$taskName = "TranscriberWidget"
$workdir  = Split-Path $exe

$action = New-ScheduledTaskAction -Execute $exe -WorkingDirectory $workdir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest
# Keep it running indefinitely (tray app); survive on battery; start if missed.
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "Installed scheduled task '$taskName'."
Write-Host "It will launch transcriber-widget (elevated, no prompt) at every logon."
Write-Host "Start it now without rebooting:  Start-ScheduledTask -TaskName $taskName"
