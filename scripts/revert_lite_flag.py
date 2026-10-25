import sys, io, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = r'C:\Users\Manoel\AppData\Local\CapCut\User Data\MMKV\settings_json'
d = bytearray(open(P, 'rb').read())
orig = len(d)

pat = b'"use_get_user_lite_info":null'
rep = b'"use_get_user_lite_info":true'
assert len(pat) == len(rep)
n = d.count(pat)
print('ocorrencias null:', n)

start = 0
while True:
    i = d.find(pat, start)
    if i < 0:
        break
    d[i:i + len(pat)] = rep
    start = i + len(pat)
assert len(d) == orig
open(P, 'wb').write(bytes(d))
print('revertido para true:', n, 'ocorrencias; offline_time permanece 2999999999:', d.count(b'2999999999'))
