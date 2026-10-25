import glob, gzip, zlib, json, os, base64, hashlib, sys

def decompress(d):
    for fn in (lambda x: gzip.decompress(x), lambda x: zlib.decompress(x), lambda x: zlib.decompress(x, -15)):
        try:
            return fn(d)
        except Exception:
            pass
    return d

# pega a resposta ORIGINAL free (FASE1, antes do rewrite) do user_info
# 083 era flag:false; mas o seq reiniciou. Busca por conteudo flag:false
cands = []
for f in glob.glob(r'C:\Users\Manoel\AppData\Local\Temp\opencode\local_bodies\*resp*user_info*'):
    d = decompress(open(f, 'rb').read())
    try:
        obj = json.loads(d.decode('utf-8'))
    except Exception:
        continue
    dd = obj.get('data', {})
    cands.append((f, obj, dd.get('flag')))

print('respostas user_info capturadas:', len(cands))
for f, obj, flag in cands:
    print('  flag=%s  %s' % (flag, os.path.basename(f)))

# usa uma free (flag False) p/ analisar o sign
free = None
for f, obj, flag in cands:
    if flag is False:
        free = obj
        break
if free is None and cands:
    free = cands[0][1]

print('\n=== analise do sign (resposta free) ===')
sign = free.get('sign', '')
resp_str = free.get('response', '')
data_obj = free.get('data', {})
print('sign len (b64 chars):', len(sign))
try:
    raw = base64.b64decode(sign)
    print('sign raw bytes:', len(raw))
except Exception as e:
    print('b64 decode erro', e)
    raw = sign.encode()

# o que o sign cobre? testa hash de varias combinacoes
def H(name, data):
    return {'md5': hashlib.md5(data).digest(),
            'sha1': hashlib.sha1(data).digest(),
            'sha256': hashlib.sha256(data).digest()}[name]

combos = {
    'response': resp_str.encode('utf-8'),
    'data_canon': json.dumps(data_obj, separators=(',', ':'), ensure_ascii=False).encode(),
    'data_sort': json.dumps(data_obj, sort_keys=True, separators=(',', ':')).encode(),
}
print('\ncomparando sign raw com hashes:')
target = raw
for cname, cdata in combos.items():
    for hname in ('md5', 'sha1', 'sha256'):
        hv = H(hname, cdata)
        if hv == target or target.startswith(hv) or hv in target:
            print('  >>> MATCH! %s sobre %s (len %d)' % (hname, cname, len(hv)))
print('(sem match simples -> provavelmente HMAC com segredo ou hash de sub-campos)')

# imprime o sign e pedaços p/ referencia
print('\nsign:', sign[:80])
print('response[:120]:', resp_str[:120])
# salva p/ analise posterior
open(r'C:\Users\Manoel\AppData\Local\Temp\opencode\sign_sample_free.json', 'w', encoding='utf-8').write(json.dumps({
    'sign': sign, 'response': resp_str, 'data': data_obj,
    'ret': free.get('ret'), 'systime': free.get('systime'), 'log_id': free.get('log_id')
}, ensure_ascii=False, indent=2))
print('salvo sign_sample_free.json')
