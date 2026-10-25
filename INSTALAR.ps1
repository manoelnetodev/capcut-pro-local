# INSTALAR.ps1 — prepara UMA MAQUINA para o CapCut Pro local (rodar como admin)
# Premissas: CapCut PC instalado; Python 3 em 'C:\Program Files\Python312\python.exe'
# (ou 'python' no PATH). Server usa apenas stdlib.
$ErrorActionPreference = 'Continue'
$ROOT = $PSScriptRoot
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Start-Process powershell -Verb RunAs -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"')
  exit
}
Start-Transcript -Path "$ROOT\instalar.log" -Force | Out-Null
try {
  # 1) HOSTS: aponta API de comercio/monitoracao para o server local
  $hostsPath = 'C:\Windows\System32\drivers\etc\hosts'
  $hostsNeed = @(
    '127.0.0.1 commerce-api-sg.capcutapi.com',
    '127.0.0.1 commerce-api.capcutapi.com',
    '127.0.0.1 commerce-api-va.capcut.com',
    '127.0.0.1 commerce-api-sg.capcut.com',
    '127.0.0.1 commerce-api-va.capcutapi.com',
    '127.0.0.1 commerce-api-v2-boot.capcutapi.com',
    '127.0.0.1 commercepro.capcut.com',
    '127.0.0.1 www.capcut.com',
    '127.0.0.1 feed-api-sg.capcut.com'
  )
  $txt = [System.IO.File]::ReadAllText($hostsPath)
  if ($txt -notmatch '# capcut-local-mitm') {
    $block = "`r`n# capcut-local-mitm`r`n" + ($hostsNeed -join "`r`n") + "`r`n# capcut-local-mitm end`r`n"
    [System.IO.File]::AppendAllText($hostsPath, $block)
    Write-Output 'hosts: bloco capcut-local-mitm adicionado'
  } else { Write-Output 'hosts: bloco ja existe' }

  # 2) CA local confiavel (para o TLS do server nao dar erro de certificado)
  $ca = Join-Path $ROOT 'server\mitm\ca.crt'
  Import-Certificate -FilePath $ca -CertStoreLocation 'Cert:\CurrentUser\Root' | Out-Null
  Write-Output 'CA importada em CurrentUser\Root'

  # 3) FIREWALL: regras de bloqueio outbound (modo OFFLINE Pro) p/ exes da versao mais recente
  $apps = 'C:\Users\Manoel\AppData\Local\CapCut\Apps'
  $verDir = Get-ChildItem $apps -Directory | Where-Object { $_.Name -match '^\d+\.\d+\.\d+\.\d+$' } |
            Sort-Object { [version]($_.Name) } -Descending | Select-Object -First 1
  Write-Output ('versao detectada: ' + $verDir.Name)
  $exes = Get-ChildItem $verDir.FullName -Recurse -Filter '*.exe' -File | Select-Object -ExpandProperty FullName
  foreach ($e in $exes) {
    $name = 'CapCutOffline ' + (Split-Path $e -Leaf)
    Remove-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName $name -Direction Outbound -Program $e -Action Block -Profile Any | Out-Null
  }
  $main = Join-Path $verDir.FullName 'CapCut.exe'
  Remove-NetFirewallRule -DisplayName 'CapcutOffline Allow Local' -ErrorAction SilentlyContinue
  New-NetFirewallRule -DisplayName 'CapcutOffline Allow Local' -Direction Outbound -Program $main -Action Allow -RemoteAddress 127.0.0.1 | Out-Null
  Write-Output ('firewall: ' + $exes.Count + ' regras criadas (desativadas = loja; ativadas = offline Pro)')

  # 4) LOGIN Google/CEF exige o server no ar durante o login do app
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$ROOT\scripts\iniciar_server.ps1"

  # 5) edits Pro no settings_json (app deve estar FECHADO — o toggle fecha)
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$ROOT\scripts\toggle_mode.ps1" -Mode offline
  Write-Output 'PRONTO: use MODO_OFFLINE_pro.cmd / MODO_LOJA_online.cmd (ou atalhos do Desktop)'
} catch {
  Write-Output ('ERRO: ' + $_.Exception.Message)
} finally {
  Stop-Transcript | Out-Null
}
