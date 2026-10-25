import re, struct, pefile
from capstone import *

DLL = r'C:\Users\Manoel\AppData\Local\CapCut\Apps\9.6.0.4097\VECreator.dll'
d = open(DLL, 'rb').read()
pe = pefile.PE(DLL, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
text = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
text_off = pe.get_offset_from_rva(text.VirtualAddress)
text_va = text.VirtualAddress

out = r'C:\Users\Manoel\AppData\Local\Temp\opencode\exportimpl_disasm.txt'
lo, hi = 0x6629000, 0x6632000
code = d[text_off + (lo - text_va): text_off + (hi - text_va)]
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

# mapa das strings referenciadas para anotar
file_str_va = base + pe.get_rva_from_offset(d.find(b'C:\\90741\\CapCutPC\\Commerce\\VipGuard\\vipbiz\\ExportImpl.cpp'))

with open(out, 'w', encoding='utf-8') as f:
    n = 0
    for ins in md.disasm(code, base + lo):
        mark = ''
        m = re.match(r'lea\s+(\w+), \[rip \+ 0x([0-9a-f]+)\]', ins.op_str)
        if m:
            f.write('%x: %-8s %s%s\n' % (ins.address, ins.mnemonic, ins.op_str, mark))
            continue
        m = re.search(r'\[rip \+ (0x[0-9a-f]+)\]', ins.op_str)
        if m:
            tgt = ins.address + ins.size + int(m.group(1), 16)
            if tgt == base + pe.get_rva_from_offset(d.find(b'be find, is not vip')):
                mark = '   <<< STR "be find, is not vip"'
            elif tgt == file_str_va:
                mark = '   <<< STR ExportImpl.cpp'
            else:
                # tentar ler a string apontada (se for rdata imprimivel)
                try:
                    roff = pe.get_offset_from_rva(tgt - base)
                    raw = d[roff:roff + 90]
                    ms = re.match(rb'[\x20-\x7e]{5,90}', raw)
                    if ms:
                        mark = '   -> str: %r' % ms.group(0).decode('latin1')[:80]
                except Exception:
                    pass
        f.write('%x: %-8s %s%s\n' % (ins.address, ins.mnemonic, ins.op_str, mark))
        n += 1
print('instrucoes dumpadas:', n, '->', out)
