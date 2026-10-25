import sys, io, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = r'C:\Users\Manoel\AppData\Local\CapCut\User Data\MMKV\settings_json'
BAK = r'C:\Users\Manoel\AppData\Local\Temp\opencode\settings_json.pre_edit4.bak'

d = bytearray(open(P, 'rb').read())
orig = len(d)

pat = b'"export_intercept_exper_offline_time":1747238400'
rep = b'"export_intercept_exper_offline_time":2999999999'
assert len(pat) == len(rep)

n = d.count(pat)
print('ocorrencias:', n)
if not n:
    sys.exit(1)

shutil.copyfile(P, BAK)
start = 0
while True:
    i = d.find(pat, start)
    if i < 0:
        break
    d[i:i + len(pat)] = rep
    start = i + len(pat)

assert len(d) == orig
open(P, 'wb').write(bytes(d))
print('editado: offline_time 1747238400 -> 2999999999 (%d ocorrencias, tamanho %d mantido)' % (n, orig))
