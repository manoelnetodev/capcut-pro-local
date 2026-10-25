$ErrorActionPreference = 'SilentlyContinue'
$names = @('CapCut','CapCutHelper','VECreator','VEHelper','VEDetector','VECrashHandler','taskcontainer','push_detect','ttdaemon','parfait_crash_handler','courgette64','feedbacktool')
foreach ($n in $names) { Get-Process -Name $n -ErrorAction SilentlyContinue | Stop-Process -Force }
Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*CapCut*' } | Stop-Process -Force
Start-Sleep -Seconds 4
Write-Output ('apos fechar: ' + ((Get-Process -Name 'CapCut' -ErrorAction SilentlyContinue) | Measure-Object).Count + ' processo(s)')
Start-Process -FilePath 'C:\Users\Manoel\AppData\Local\CapCut\Apps\CapCut.exe'
Start-Sleep -Seconds 22
$p = Get-Process -Name 'CapCut'
Write-Output ('apos reabrir: ' + ($p | Measure-Object).Count + ' processo(s)')
