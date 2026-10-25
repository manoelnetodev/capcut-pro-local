$ErrorActionPreference = 'Stop'
$path = 'C:\Users\Manoel\AppData\Local\CapCut\User Data\MMKV\settings_json'
$bytes = [System.IO.File]::ReadAllBytes($path)

# JSON começa no offset 32
$start = 32
# varre contando depth de chaves, respeitando strings
$depth = 0
$inStr = $false
$esc = $false
$end = -1
for ($i = $start; $i -lt $bytes.Count; $i++) {
  $c = [char]$bytes[$i]
  if ($inStr) {
    if ($esc) { $esc = $false }
    elseif ($c -eq '\') { $esc = $true }
    elseif ($c -eq '"') { $inStr = $false }
  } else {
    if ($c -eq '"') { $inStr = $true }
    elseif ($c -eq '{') { $depth++ }
    elseif ($c -eq '}') { $depth--; if ($depth -eq 0) { $end = $i; break } }
  }
}
$jsonLen = $end - $start + 1
Write-Output ('JSON: start=' + $start + ' end=' + $end + ' len=' + $jsonLen)

# bytes logo apos a key (offset 26..31)
Write-Output ('bytes offset 26-31 = ' + (($bytes[26..31] | ForEach-Object { '{0:X2}' -f $_ }) -join ' '))
Write-Output ('bytes offset 28-31 (possivel valueLen 4B LE) = ' + [BitConverter]::ToString($bytes[28..31]))

# calcula CRC32 do JSON (padrao zlib)
$valBytes = New-Object byte[] $jsonLen
[Array]::Copy($bytes, $start, $valBytes, 0, $jsonLen)
function Get-Crc32([byte[]]$data) {
  $table = New-Object int[] 256
  for ($i = 0; $i -lt 256; $i++) {
    $c = $i
    for ($k = 0; $k -lt 8; $k++) { if (($c -band 1) -ne 0) { $c = (($c -shr 1) -bxor 0xEDB88320) } else { $c = $c -shr 1 } }
    $table[$i] = $c
  }
  $crc = -1
  foreach ($b in $data) { $crc = $table[(-bxor ($crc -band 0xFF) $b) -band 0xFF] -bxor ($crc -shr 8) }
  return (-bxor $crc -1) -band 0xFFFFFFFF
}
$crc = Get-Crc32 $valBytes
Write-Output ('CRC32 do JSON = 0x{0:X8}  (bytes LE: {1})' -f $crc, (($crc -band 0xFF), (($crc -shr 8) -band 0xFF), (($crc -shr 16) -band 0xFF), (($crc -shr 24) -band 0xFF) | ForEach-Object { '{0:X2}' -f $_ } | Join-String -Separator ' '))

# salva o JSON
[System.IO.File]::WriteAllBytes('C:\Users\Manoel\AppData\Local\Temp\opencode\settings_json_extracted.json', $valBytes)
$json = [System.Text.Encoding]::UTF8.GetString($valBytes)
Write-Output ('JSON salvo. inicio: ' + $json.Substring(0, [Math]::Min(120,$json.Length)))
