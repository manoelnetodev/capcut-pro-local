import pefile, base64, json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

dll = r'C:\Users\Manoel\AppData\Local\CapCut\Apps\9.0.0.3858\VECreator.dll'
d = open(dll, 'rb').read()
pe = pefile.PE(dll, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase

# endereco da chave: instrucao lea em VA base+0x5a08cba (7 bytes) -> next = base+0x5a08cc1
key_va = (base + 0x5a08cc1) + 0x651007f
key_rva = key_va - base
key_off = pe.get_offset_from_rva(key_rva)
print('chave em VA %s rva %s fileoff %d' % (hex(key_va), hex(key_rva), key_off))
keydata = d[key_off: key_off + 400]
# pega o PEM
end = keydata.find(b'-----END PUBLIC KEY-----')
pem = keydata[:end+22]
print('PEM lido (%d bytes):' % len(pem))
print(pem.decode('latin1')[:200])

key = serialization.load_pem_public_key(pem)
print('chave: %d bits' % key.key_size)

# agora re-verifica a assinatura da resposta free com ESTA chave
samp = json.load(open(r'C:\Users\Manoel\AppData\Local\Temp\opencode\sign_sample_free.json', encoding='utf-8'))
sign = base64.b64decode(samp['sign'])
resp_str = samp['response'].encode('utf-8')
data_obj = samp['data']

cands = {
    'response_str': resp_str,
    'data_canon': json.dumps(data_obj, separators=(',', ':'), ensure_ascii=False).encode(),
    'data_sort': json.dumps(data_obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode(),
    'full_body': json.dumps(samp, separators=(',', ':'), ensure_ascii=False).encode(),
}
hashes_try = [('sha1', hashes.SHA1()), ('sha256', hashes.SHA256()), ('md5', hashes.MD5())]

print('\nverificando sign com a chave correta:')
match = False
for cname, cdata in cands.items():
    for hname, hobj in hashes_try:
        try:
            key.verify(sign, cdata, padding.PKCS1v15(), hobj)
            print('  >>> MATCH! %s + %s sobre %s' % (hname, 'PKCS1v15', cname))
            match = True
        except Exception:
            pass
        # tenta PSS
        try:
            key.verify(sign, cdata, padding.PSS(mgf=padding.MGF1(hobj), salt_length=padding.PSS.AUTO), hobj)
            print('  >>> MATCH PSS! %s sobre %s' % (hname, cname))
            match = True
        except Exception:
            pass
if not match:
    print('  (ainda sem match direto - o payload pode ser um subconjunto/ordem especifica)')
