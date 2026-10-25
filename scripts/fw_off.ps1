$ErrorActionPreference = 'Continue'
Start-Transcript -Path 'C:\Users\Manoel\AppData\Local\Temp\opencode\fw_off.log' -Force | Out-Null
try {
  Get-Process -Name CapCut -ErrorAction SilentlyContinue | Stop-Process -Force
  Start-Sleep -Seconds 3
  $rules = Get-NetFirewallRule -DisplayName 'CapCutOffline*' -ErrorAction SilentlyContinue
  $n = 0
  foreach ($r in $rules) { Set-NetFirewallRule -Name $r.Name -Enabled False; $n++ }
  Write-Output ('regras desativadas: ' + $n)
} catch {
  Write-Output ('ERRO: ' + $_.Exception.Message)
} finally {
  Stop-Transcript | Out-Null
}
