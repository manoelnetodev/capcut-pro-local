$ErrorActionPreference = 'Continue'
Start-Transcript -Path 'C:\Users\Manoel\AppData\Local\Temp\opencode\fw_block.log' -Force | Out-Null
try {
  # mata CapCut antes de aplicar
  Get-Process -Name CapCut -ErrorAction SilentlyContinue | Stop-Process -Force
  Start-Sleep -Seconds 3

  $exes = @()
  $exes += 'C:\Users\Manoel\AppData\Local\CapCut\Apps\9.6.0.4097\CapCut.exe'
  Get-ChildItem 'C:\Users\Manoel\AppData\Local\CapCut\Apps\9.6.0.4097' -Recurse -Filter '*.exe' -ErrorAction SilentlyContinue |
    ForEach-Object { $exes += $_.FullName }
  $exes = $exes | Sort-Object -Unique

  foreach ($e in $exes) {
    $name = 'CapCutOffline ' + (Split-Path $e -Leaf)
    Remove-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName $name -Direction Outbound -Program $e -Action Block -Profile Any | Out-Null
  }
  Write-Output ('regras de bloqueio criadas: ' + $exes.Count)

  # regra de PERMISSAO para qualquer IP remoto (loopback nao eh filtrado pelo firewall,
  # mas garantimos excecao p/ caso o app resolva hosts locais)
  Remove-NetFirewallRule -DisplayName 'CapcutOffline Allow Local' -ErrorAction SilentlyContinue
  New-NetFirewallRule -DisplayName 'CapcutOffline Allow Local' -Direction Outbound -Program 'C:\Users\Manoel\AppData\Local\CapCut\Apps\9.6.0.4097\CapCut.exe' -Action Allow -RemoteAddress 127.0.0.1 | Out-Null
  Write-Output 'regra allow 127.0.0.1 criada'

  # servidor na 443 continua?
  $listen = Get-NetTCPConnection -LocalPort 443 -State Listen -ErrorAction SilentlyContinue
  Write-Output ('ouvindo na 443: ' + ($listen | Measure-Object).Count)
} catch {
  Write-Output ('ERRO: ' + $_.Exception.Message)
} finally {
  Stop-Transcript | Out-Null
}
