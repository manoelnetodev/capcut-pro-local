param([ValidateSet('loja', 'offline')][string]$Mode = 'offline')

# auto-elevacao (UAC)
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Start-Process powershell -Verb RunAs -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -Mode ' + $Mode)
  exit
}

$ErrorActionPreference = 'Continue'
$ROOT = Split-Path $PSScriptRoot -Parent   # pasta raiz do projeto (pai de scripts\)
New-Item -ItemType Directory -Force -Path (Join-Path $ROOT 'logs') | Out-Null
Start-Transcript -Path (Join-Path $ROOT ("logs\toggle_{0}.log" -f $Mode)) -Force | Out-Null
try {
  # fecha tudo ligado ao CapCut (incl. handlers auxiliares)
  Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*CapCut*' } | Stop-Process -Force
  Start-Sleep -Seconds 4

  if ($Mode -eq 'offline') {
    # re-aplica os edits Pro no settings_json (o modo online re-polui o blob)
    & 'C:\Program Files\Python312\python.exe' (Join-Path $PSScriptRoot 'edit_settings_pro.py')
    if (-not (Test-Path 'C:\Program Files\Python312\python.exe')) { & python (Join-Path $PSScriptRoot 'edit_settings_pro.py') }
    $rules = Get-NetFirewallRule -DisplayName 'CapCutOffline*' -ErrorAction SilentlyContinue
    foreach ($r in $rules) { Set-NetFirewallRule -Name $r.Name -Enabled True }
    Write-Output ('REGRAS ATIVADAS (modo OFFLINE Pro): ' + ($rules | Measure-Object).Count)
  } else {
    $rules = Get-NetFirewallRule -DisplayName 'CapCutOffline*' -ErrorAction SilentlyContinue
    foreach ($r in $rules) { Set-NetFirewallRule -Name $r.Name -Enabled False }
    Write-Output ('REGRAS DESATIVADAS (modo LOJA online): ' + ($rules | Measure-Object).Count)
  }

  $listen = (Get-NetTCPConnection -LocalPort 443 -State Listen -ErrorAction SilentlyContinue | Measure-Object).Count
  if ($listen -eq 0) {
    Write-Output 'aviso: server local NAO esta ouvindo na 443 (rode INICIAR_SERVER.cmd antes, p/ login)'
  }

  # launcher oficial do CapCut
  Start-Process -FilePath (Join-Path $env:LOCALAPPDATA 'CapCut\Apps\CapCut.exe')
  Write-Output 'CapCut reaberto'
} catch {
  Write-Output ('ERRO: ' + $_.Exception.Message)
} finally {
  Stop-Transcript | Out-Null
}
