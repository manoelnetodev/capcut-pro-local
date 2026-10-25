$ErrorActionPreference = 'Continue'
$ROOT = Split-Path $PSScriptRoot -Parent
$desktop = [Environment]::GetFolderPath('Desktop')
$ws = New-Object -ComObject WScript.Shell
foreach ($pair in @(
  @('CapCut PRO (offline).lnk', (Join-Path $ROOT 'MODO_OFFLINE_pro.cmd')),
  @('CapCut MODO LOJA (online).lnk', (Join-Path $ROOT 'MODO_LOJA_online.cmd')),
  @('CapCut SERVER local.lnk', (Join-Path $ROOT 'INICIAR_SERVER.cmd'))
)) {
  $sc = $ws.CreateShortcut((Join-Path $desktop $pair[0]))
  $sc.TargetPath = $pair[1]
  $sc.WorkingDirectory = $ROOT
  $capcut = Join-Path $env:LOCALAPPDATA 'CapCut\Apps\9.6.0.4097\CapCut.exe'
  if (Test-Path $capcut) { $sc.IconLocation = $capcut + ',0' }
  $sc.Description = $pair[0]
  $sc.Save()
  Write-Output ('atalho: ' + $pair[0] + ' -> ' + $pair[1])
}
