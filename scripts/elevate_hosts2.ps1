$ErrorActionPreference = 'Continue'
Start-Transcript -Path 'C:\Users\Manoel\AppData\Local\Temp\opencode\elevate_hosts2.log' -Force | Out-Null
try {
  $hosts = 'C:\Windows\System32\drivers\etc\hosts'
  $txt = [System.IO.File]::ReadAllText($hosts)
  $new = @(
    '127.0.0.1 commerce-api-sg.capcut.com',
    '127.0.0.1 commerce-api-va.capcutapi.com',
    '127.0.0.1 commerce-api-v2-boot.capcutapi.com'
  )
  foreach ($line in $new) {
    $h = $line.Split(' ')[1]
    if ($txt -notmatch [regex]::Escape($h)) {
      $txt = $txt -replace '# capcut-local-mitm end', ($line + "`r`n# capcut-local-mitm end")
      Write-Output ('adicionado: ' + $h)
    } else {
      Write-Output ('ja existia: ' + $h)
    }
  }
  [System.IO.File]::WriteAllText($hosts, $txt)

  # reinicia server na 443
  $conns = Get-NetTCPConnection -LocalPort 443 -State Listen -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    Write-Output ('matando PID ' + $c.OwningProcess)
    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
  }
  Start-Sleep -Seconds 2
  $py = 'C:\Program Files\Python312\python.exe'
  $script = 'C:\Users\Manoel\AppData\Local\Temp\opencode\local_tls_server.py'
  $err = 'C:\Users\Manoel\AppData\Local\Temp\opencode\local_tls_server.err'
  Start-Process -FilePath $py -ArgumentList $script -WindowStyle Hidden -RedirectStandardError $err
  Start-Sleep -Seconds 3
  $listen = Get-NetTCPConnection -LocalPort 443 -State Listen -ErrorAction SilentlyContinue
  Write-Output ('ouvindo na 443: ' + ($listen | Measure-Object).Count)
  $errtxt = Get-Content $err -ErrorAction SilentlyContinue
  if ($errtxt) { Write-Output ('stderr: ' + ($errtxt -join ' | ')) }
} catch {
  Write-Output ('ERRO: ' + $_.Exception.Message)
} finally {
  Stop-Transcript | Out-Null
}
