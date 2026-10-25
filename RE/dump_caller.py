import re, struct, pefile, sys, io
from capstone import *

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DLL = r'C:\Users\Manoel\AppData\Local\CapCut\Apps\9.6.0.4097\VECreator.dll'
d = open(DLL, 'rb').read()
pe = pefile.PE(DLL, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
text = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
text_off = pe.get_offset_from_rva(text.VirtualAddress)
text_va = text.VirtualAddress

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = False

strtab = {}
def annotate(ins):
    m = re.search(r'\[rip \+ (0x[0-9a-f]+)\]', ins.op_str)
    if m:
        tgt = ins.address + ins.size + int(m.group(1), 16)
        try:
            roff = pe.get_offset_from_rva(tgt - base)
            raw = d[roff:roff + 90]
            ms = re.match(rb'[\x20-\x7e]{5,90}', raw)
            if ms:
                return '   -> %r' % ms.group(0).decode('latin1')[:70]
        except Exception:
            pass
    return ''

def dump(lo, hi, label):
    print('#' * 22, label)
    code = d[text_off + (lo - text_va): text_off + (hi - text_va)]
    for ins in md.disasm(code, base + lo):
        print('%x: %-8s %s%s' % (ins.address, ins.mnemonic, ins.op_str, annotate(ins)))
    print()

dump(0xb99aa0, 0xb99d00, 'FUNCAO GATE 0x180b99aa0 (retorna bool is_vip?)')
