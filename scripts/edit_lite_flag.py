import sys, io, shutil, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = r'C:\Users\Manoel\AppData\Local\CapCut\User Data\MMKV\settings_json'
BAK = r'C:\Users\Manoel\AppData\Local\Temp\opencode\settings_json.pre_edit3.bak'

d = bytearray(open(P, 'rb').read())
orig_size = len(d)

pat = b'"vip_export_interface":{"use_get_user_lite_info":true}'
rep = b'"vip_export_interface":{"use_get_user_lite_info":null}'
assert len(pat) == len(rep)

# tambem a variante com espacos ou ordem diferente, se existir
n = d.count(pat)
if not n:
    # busca flexivel
    import re
    ms = list(re.finditer(rb'"vip_export_interface"\s*:\s*\{\s*"use_get_user_lite_info"\s*:\s*true\s*\}', d))
    print('variantes encontradas:', len(ms))
    for m in ms[:5]:
        print('  ', d[m.start():m.end()])
    sys.exit(1)

shutil.copyfile(P, BAK)
print('backup:', BAK)

# substitui apenas da ÚLTIMA para a primeira (a efetiva é a última; mas trocar todas mantém consistência)
start = 0
while True:
    i = d.find(pat, start)
    if i < 0:
        break
    d[i:i+len(pat)] = rep
    start = i + len(pat)

assert len(d) == orig_size
f = open(P, 'r+b')
f.seek(0)
f.write(bytes(d))
f.close()
print('substituidas %d ocorrencias, tamanho mantido: %d' % (n, len(d)))
