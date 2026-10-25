$ErrorActionPreference = 'SilentlyContinue'
Get-Process | Where-Object { $_.Path -like '*CapCut*' } | ForEach-Object {
  Write-Output ('matando: ' + $_.Name + ' (' + $_.Id + ')')
  Stop-Process -Id $_.Id -Force
}
Start-Sleep -Seconds 3
$left = (Get-Process | Where-Object { $_.Path -like '*CapCut*' } | Measure-Object).Count
Write-Output ('restantes: ' + $left)
