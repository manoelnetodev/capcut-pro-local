import re, struct, pefile
from capstone import *

DLL = r'C:\Users\Manoel\AppData\Local\CapCut\Apps\9.6.0.4097\VECreator.dll'
d = open(DLL, 'rb').read()
pe = pefile.PE(DLL, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
text = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
text_off = pe.get_offset_from_rva(text.VirtualAddress)
text_bytes = d[text_off:text_off + text.Misc_VirtualSize]
text_va = text.VirtualAddress

cands = [b'C:\\90741\\CapCutPC\\Commerce\\VipGuard\\vipbiz\\ExportImpl.cpp',
         b'pulling vip info',
         b'be find, is not vip',
         b'Trial for non-VIP users']
targets = {}
for lab in cands:
    for m in re.finditer(re.escape(lab), d):
        s = m.start()
        va = base + pe.get_rva_from_offset(s)
        targets[va] = lab.decode('latin1')[:60]

def find_refs(want_vas):
    hits = []
    i = 0
    n = len(text_bytes)
    while i < n - 7:
        b0 = text_bytes[i]; b1 = text_bytes[i + 1]
        if b0 in (0x48, 0x4C) and b1 in (0x8D, 0x8B):
            modrm = text_bytes[i + 2]
            if (modrm >> 6) == 0 and (modrm & 7) == 5:
                disp, = struct.unpack_from('<i', text_bytes, i + 3)
                t = base + (text_va + i + 7) + disp
                if t in want_vas:
                    hits.append((text_va + i, t))
                i += 7
                continue
        i += 1
    return hits

hits = find_refs(set(targets))
print('refs:')
for a, t in hits:
    print('  @%x -> %s' % (a, targets[t]))

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True
# disassembla ao redor do primeiro ref do cpp-path
seen = set()
for a, t in hits:
    lab = targets[t]
    if 'ExportImpl.cpp' not in lab:
        continue
    start_va = a - 1200
    code = text_bytes[(start_va - text_va):(start_va - text_va) + 1600]
    print('=== disasm @%x (contexto do log) ===' % a)
    for ins in md.disasm(code, start_va):
        mark = ' <== FILE ref' if ins.address == a else ''
        print('%x: %-8s %s%s' % (ins.address, ins.mnemonic, ins.op_str, mark))
    break
