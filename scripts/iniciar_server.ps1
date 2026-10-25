$ErrorActionPreference = 'Continue'
$ROOT = Split-Path $PSScriptRoot -Parent
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Start-Process powershell -Verb RunAs -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"')
  exit
}
Start-Transcript -Path (Join-Path $ROOT 'server\server_start.log') -Force | Out-Null
try {
  $conns = Get-NetTCPConnection -LocalPort 443 -State Listen -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    Write-Output ('matando PID ' + $c.OwningProcess + ' na 443')
    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
  }
  Start-Sleep -Seconds 2
  $py = 'C:\Program Files\Python312\python.exe'
  if (-not (Test-Path $py)) { $py = 'python' }
  Start-Process -FilePath $py -ArgumentList (Join-Path $ROOT 'server\local_tls_server.py') -WindowStyle Hidden -RedirectStandardError (Join-Path $ROOT 'server\server.err')
  Start-Sleep -Seconds 3
  $listen = (Get-NetTCPConnection -LocalPort 443 -State Listen -ErrorAction SilentlyContinue | Measure-Object).Count
  Write-Output ('ouvindo na 443: ' + $listen)
  $err = Get-Content (Join-Path $ROOT 'server\server.err') -ErrorAction SilentlyContinue
  if ($err) { Write-Output ('stderr: ' + ($err -join ' | ')) }
} catch {
  Write-Output ('ERRO: ' + $_.Exception.Message)
} finally {
  Stop-Transcript | Out-Null
}
