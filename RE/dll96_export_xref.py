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

# localizar as strings isoladas (log names) do ExportImpl
labels = [b'VEByteguard::ExportImpl::CheckCanUseVip',
          b'VEByteguard::ExportImpl::ExportStart',
          b'VEByteguard::ExportImpl::GetBtnStatus']
targets = {}
for lab in labels:
    for m in re.finditer(re.escape(lab), d):
        j = m.start()
        s = j
        while s > 0 and d[s - 1] != 0:
            s -= 1
        e = j + len(lab)
        while e < len(d) and d[e] != 0:
            e += 1
        full = d[s:e]
        if full == lab:  # string isolada exata
            va = base + pe.get_rva_from_offset(s)
            targets[va] = lab.decode()
for va, lab in sorted(targets.items()):
    print('string %s @%x' % (lab, va))

# xref scan
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
for a, t in hits:
    print('ref @%x -> %s' % (a, targets[t]))
