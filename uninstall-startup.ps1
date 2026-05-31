#Requires -RunAsAdministrator
# Removes the logon Scheduled Task created by install-startup.ps1.
#   powershell -ExecutionPolicy Bypass -File .\uninstall-startup.ps1

$ErrorActionPreference = "Stop"
$taskName = "TranscriberWidget"

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed scheduled task '$taskName'."
} else {
    Write-Host "No scheduled task named '$taskName' found."
}
