import re, struct, pefile

DLL = r'C:\Users\Manoel\AppData\Local\CapCut\Apps\9.6.0.4097\VECreator.dll'
d = open(DLL, 'rb').read()
pe = pefile.PE(DLL, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
text = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
text_off = pe.get_offset_from_rva(text.VirtualAddress)
text_bytes = d[text_off:text_off + text.Misc_VirtualSize]
text_va = text.VirtualAddress

# procura call qword ptr [rip+X] e call rel32 cujo alvo resolvido = funcoes-chave
targets = {
    0x662ca20: 'ExportStart lambda (bool dl)',
    0x662b7e0: 'GetBtnStatus lambda_14c0',
    0x662c800: 'funcao @c800',
}
rel_hits = []
i = 0
n = len(text_bytes)
while i < n - 5:
    if text_bytes[i] == 0xE8:  # call rel32
        disp, = struct.unpack_from('<i', text_bytes, i + 1)
        tva = text_va + i + 5 + disp
        if tva in targets:
            rel_hits.append((base + text_va + i, targets[tva]))
        i += 5
        continue
    i += 1

print('callers diretos (call rel32) das funcoes-chave:')
for a, lab in rel_hits:
    print('  @%x -> %s' % (a, lab))
