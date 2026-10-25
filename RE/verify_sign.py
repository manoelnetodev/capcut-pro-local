import json, base64, glob, gzip, zlib, os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils

def decompress(d):
    for fn in (lambda x: gzip.decompress(x), lambda x: zlib.decompress(x), lambda x: zlib.decompress(x, -15)):
        try:
            return fn(x) if False else fn(d)
        except Exception:
            pass
    return d

# carrega as 3 chaves RSA-1024
keys = {}
for i in (2, 4, 5):
    pem = open(r'C:\Users\Manoel\AppData\Local\Temp\opencode\keys\key_%d.pem' % i, 'rb').read()
    keys[i] = serialization.load_pem_public_key(pem)
    print('key_%d: %d bits' % (i, keys[i].key_size))

# carrega resposta free original
samp = json.load(open(r'C:\Users\Manoel\AppData\Local\Temp\opencode\sign_sample_free.json', encoding='utf-8'))
sign = base64.b64decode(samp['sign'])
resp_str = samp['response'].encode('utf-8')
data_obj = samp['data']
print('sign', len(sign), 'bytes')

# candidatos de payload (o que a assinatura pode cobrir)
cands = {
    'response_str': resp_str,
    'data_canon_nosort': json.dumps(data_obj, separators=(',', ':'), ensure_ascii=False).encode(),
    'data_sort_keys': json.dumps(data_obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode(),
    'response_plus_ret': (str(samp.get('ret','')).encode('latin1') + resp_str),
    'systime_plus_response': (str(samp.get('systime','')).encode('latin1') + resp_str),
    'logid_plus_response': (str(samp.get('log_id','')).encode('latin1') + resp_str),
    'uid_plus_response': (str(data_obj.get('uid','')).encode('latin1') + resp_str),
    'response_plus_uid': (resp_str + str(data_obj.get('uid','')).encode('latin1')),
    'response_plus_systime': (resp_str + str(samp.get('systime','')).encode('latin1')),
    'full_body_canon': json.dumps(samp, separators=(',',':'), ensure_ascii=False).encode(),
}

hashes_try = [
    ('sha1', hashes.SHA1()),
    ('sha256', hashes.SHA256()),
    ('md5', hashes.MD5()),
]

found = []
for cname, cdata in cands.items():
    for ki, key in keys.items():
        for hname, hobj in hashes_try:
            try:
                key.verify(sign, cdata, padding.PKCS1v15(), hobj)
                found.append((cname, ki, hname))
                print('>>> MATCH! payload=%s key_%d %s' % (cname, ki, hname))
            except Exception:
                pass

if not found:
    print('\nNENHUM match direto. Testando pre-imagens PKCS1 brutas / outros payloads...')
    # tenta: assinatura sobre o JSON completo original (ret..data) como veio
    # e sobre response com espacos
    extra = {
        'resp_spaces': json.dumps(json.loads(samp['response']), ensure_ascii=False).encode(),
    }
    for cname, cdata in extra.items():
        for ki, key in keys.items():
            for hname, hobj in hashes_try:
                try:
                    key.verify(sign, cdata, padding.PKCS1v15(), hobj)
                    print('>>> MATCH extra! %s key_%d %s' % (cname, ki, hname))
                    found.append((cname, ki, hname))
                except Exception:
                    pass
    if not found:
        print('(sem match - a assinatura pode cobrir um subconjunto de campos ou usar outro padding/hash)')
