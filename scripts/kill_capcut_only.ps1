$ErrorActionPreference = 'SilentlyContinue'
$names = @('CapCut','CapCutHelper','VECreator','VEHelper','VEDetector','VECrashHandler','taskcontainer','push_detect','ttdaemon','perfect_crash_handler','parfait_crash_handler','courgette64','uninstshell','feedbacktool','ffmpeg')
foreach ($n in $names) {
  Get-Process -Name $n -ErrorAction SilentlyContinue | Stop-Process -Force
}
Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*CapCut*' } | Stop-Process -Force
Start-Sleep -Seconds 5
$left = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*CapCut*' }
Write-Output ('processos CapCut restantes: ' + ($left | Measure-Object).Count)
