$ErrorActionPreference = 'Continue'
Start-Transcript -Path 'C:\Users\Manoel\AppData\Local\Temp\opencode\elevate_restart_server.log' -Force | Out-Null
try {
  $conns = Get-NetTCPConnection -LocalPort 443 -State Listen -ErrorAction SilentlyContinue
  if ($conns) {
    foreach ($c in $conns) {
      $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
      $nm = if ($p) { $p.ProcessName } else { '?' }
      Write-Output ('matando PID ' + $c.OwningProcess + ' (' + $nm + ')')
      Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
    }
  } else {
    Write-Output 'nada ouvindo na 443 (ok)'
  }
  Start-Sleep -Seconds 2
  $py = 'C:\Program Files\Python312\python.exe'
  $script = 'C:\Users\Manoel\AppData\Local\Temp\opencode\local_tls_server.py'
  $err = 'C:\Users\Manoel\AppData\Local\Temp\opencode\local_tls_server.err'
  Start-Process -FilePath $py -ArgumentList $script -WindowStyle Hidden -RedirectStandardError $err
  Start-Sleep -Seconds 2
  $listen = Get-NetTCPConnection -LocalPort 443 -State Listen -ErrorAction SilentlyContinue
  Write-Output ('ouvindo na 443: ' + ($listen | Measure-Object).Count)
  if ($listen) {
    Write-Output ('PID novo: ' + ($listen | Select-Object -First 1 -ExpandProperty OwningProcess))
  }
} catch {
  Write-Output ('ERRO: ' + $_.Exception.Message)
  Write-Output $_.ScriptStackTrace
} finally {
  Stop-Transcript | Out-Null
}
