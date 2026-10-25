$ErrorActionPreference = 'SilentlyContinue'
foreach ($h in 'commerce-api-sg.capcut.com','commerce-api-va.capcutapi.com','commerce-api-v2-boot.capcutapi.com','commercepro.com') {
  $r = Resolve-DnsName $h -Type A | Where-Object { $_.IPAddress } | Select-Object -First 2 -ExpandProperty IPAddress
  Write-Output ($h + ' -> ' + ($r -join ', '))
}
