$ErrorActionPreference = 'SilentlyContinue'
$procs = Get-Process | Where-Object { $_.Path -like '*CapCut*' }
Write-Output ('processos CapCut: ' + ($procs | Measure-Object).Count)
$log = 'C:\Users\Manoel\AppData\Local\Temp\opencode\local_capture.log'
$sz = (Get-Item $log).Length
Write-Output ('log: ' + $sz + ' bytes, ultima escrita ' + (Get-Item $log).LastWriteTime.ToString('HH:mm:ss'))
Get-Content $log -Tail 2 | ForEach-Object { Write-Output ('  ' + $_.Substring(0, [Math]::Min(120, $_.Length))) }
