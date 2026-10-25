import struct, pefile, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DLL = r'C:\Users\Manoel\AppData\Local\CapCut\Apps\9.6.0.4097\VECreator.dll'
d = open(DLL, 'rb').read()
pe = pefile.PE(DLL, fast_load=True)
text = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
text_off = pe.get_offset_from_rva(text.VirtualAddress)
text_bytes = d[text_off:text_off + text.Misc_VirtualSize]
text_va = text.VirtualAddress

TARGET = 0xb99aa0

# call rel32 (E8) e jmp rel32 (E9) para o alvo
hits = []
i = 0
n = len(text_bytes)
while i < n - 5:
    op = text_bytes[i]
    if op in (0xE8, 0xE9):
        disp, = struct.unpack_from('<i', text_bytes, i + 1)
        tva = text_va + i + 5 + disp
        if tva == TARGET:
            hits.append((text_va + i, 'call' if op == 0xE8 else 'jmp'))
        i += 5
        continue
    i += 1

print('referencias diretas a 0x%x: %d' % (TARGET, len(hits)))
for a, k in hits:
    print('  %s @ RVA 0x%x (VA 0x%x)' % (k, a, 0x180000000 + a))
