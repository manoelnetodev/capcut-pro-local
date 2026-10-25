import sys, io, shutil, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # raiz do projeto
P = os.path.join(os.environ['LOCALAPPDATA'], 'CapCut', 'User Data', 'MMKV', 'settings_json')
BAKDIR = os.path.join(ROOT, 'backup')
BAK = os.path.join(BAKDIR, 'settings_json_antes_do_fix.bak')
os.makedirs(BAKDIR, exist_ok=True)

d = bytearray(open(P, 'rb').read())
orig = len(d)

def sub_all(buf, pat, rep):
    assert len(pat) == len(rep), pat
    n = 0
    start = 0
    while True:
        i = buf.find(pat, start)
        if i < 0:
            break
        buf[i:i + len(pat)] = rep
        start = i + len(pat)
        n += 1
    return n

shutil.copyfile(P, BAK)

# 1) todas as ocorrencias do timestamp vencido -> 2065 (10 digitos -> 10 digitos)
n1 = sub_all(d, b'1747238400', b'2999999999')
# 2) lite flag: true -> null em TODAS as variantes completas
n2 = sub_all(d, b'"use_get_user_lite_info":true', b'"use_get_user_lite_info":null')

assert len(d) == orig
f = open(P, 'r+b')
f.seek(0)
f.write(bytes(d))
f.close()

print('offline_time corrigido:', n1)
print('lite flag corrigida:', n2)
print('restando vencidos:', d.count(b'1747238400'), ' restando true:', d.count(b'"use_get_user_lite_info":true'))
print('tamanho mantido:', len(d))
