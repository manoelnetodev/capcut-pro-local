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

anchors = {
    b'[splash_screen] is_login': 'splash is_vip log',
    b'ExportVipRightsViewModel': 'ExportVipRightsViewModel str',
    b'isVipInfoReady': 'isVipInfoReady str',
}
for pat, label in anchors.items():
    occ = [m.start() for m in re.finditer(re.escape(pat), d)]
    print('%-28s %dx %s' % (label, len(occ), occ[:6]))

def va_of(off):
    return base + pe.get_rva_from_offset(off)

# xref para a string do splash log
target_off = None
for m in re.finditer(re.escape(b'(%s:%d,%s) [splash_screen] is_login: %d, is_vip: %d'), d):
    target_off = m.start()
print('splash log string @', target_off)
if target_off:
    tv = va_of(target_off)
    hits = []
    i = 0
    n = len(text_bytes)
    while i < n - 7:
        b0 = text_bytes[i]; b1 = text_bytes[i + 1]
        if b0 in (0x48, 0x4C) and b1 in (0x8D, 0x8B):
            modrm = text_bytes[i + 2]
            if (modrm >> 6) == 0 and (modrm & 7) == 5:
                disp, = struct.unpack_from('<i', text_bytes, i + 3)
                if base + (text_va + i + 7) + disp == tv:
                    hits.append(text_va + i)
                i += 7
                continue
        i += 1
    print('xrefs splash:', [hex(h) for h in hits])
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    for a in hits[:2]:
        start_va = a - 700
        code = text_bytes[(start_va - text_va):(start_va - text_va) + 900]
        print('=== disasm @%x ===' % a)
        for ins in md.disasm(code, start_va):
            mark = ' <== logfmt ref' if ins.address == a else ''
            print('%x: %-8s %s%s' % (ins.address, ins.mnemonic, ins.op_str, mark))
