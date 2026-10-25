$ErrorActionPreference = 'Stop'
$path = 'C:\Users\Manoel\AppData\Local\CapCut\User Data\MMKV\settings_json'
$bytes = [System.IO.File]::ReadAllBytes($path)
$start = 32
# localiza fim do JSON (balanceamento de chaves com tratamento de string)
$depth = 0; $inStr = $false; $esc = $false; $end = -1
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
$valBytes = New-Object byte[] $jsonLen
[Array]::Copy($bytes, $start, $valBytes, 0, $jsonLen)
[System.IO.File]::WriteAllBytes('C:\Users\Manoel\AppData\Local\Temp\opencode\settings_json_extracted.json', $valBytes)

# CRC32 (IEEE 802.3 / zlib), reflectido
$table = New-Object 'int[]' 256
for ($n = 0; $n -lt 256; $n++) {
  $cc = $n
  for ($k = 0; $k -lt 8; $k++) {
    if (($cc -band 1) -ne 0) { $cc = (($cc -shr 1) -bxor 0xEDB88320) } else { $cc = ($cc -shr 1) }
  }
  $table[$n] = $cc
}
$crc = 0xFFFFFFFF
foreach ($b in $valBytes) {
  $idx = ((($crc -band 0xFF) -bxor $b)) -band 0xFF
  $crc = ($table[$idx]) -bxor ($crc -shr 8)
}
$crc = ($crc -bxor 0xFFFFFFFF) -band 0xFFFFFFFF
Write-Output ('JSON len = ' + $jsonLen)
Write-Output ('CRC32 do valor = 0x{0:X8}  (LE: {1} {2} {3} {4})' -f $crc,
  ('{0:X2}' -f ($crc -band 0xFF)), ('{0:X2}' -f (($crc -shr 8) -band 0xFF)),
  ('{0:X2}' -f (($crc -shr 16) -band 0xFF)), ('{0:X2}' -f (($crc -shr 24) -band 0xFF)))
Write-Output ('bytes apos key (26-31) = 84 DC 24 81 DC 24')
# compara
$le = '{0:X2} {1:X2} {2:X2} {3:X2}' -f ($crc -band 0xFF), (($crc -shr 8) -band 0xFF), (($crc -shr 16) -band 0xFF), (($crc -shr 24) -band 0xFF)
if ($le -eq '84 DC 24 81') { Write-Output '>> COINCIDE: os 4 bytes apos key = CRC32 do valor (LE)' }
elseif ('{0:X8}' -f $crc -eq '8124DC84') { Write-Output '>> COINCIDE (BE/uint): 8124DC84' }
else { Write-Output '>> NAO coincide com CRC32 padrao. Os 4 bytes sao outro campo (len/timestamp/seq).' }
