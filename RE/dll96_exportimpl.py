import re

DLL = r'C:\Users\Manoel\AppData\Local\CapCut\Apps\9.6.0.4097\VECreator.dll'
d = open(DLL, 'rb').read()
for pat in (rb'ExportImpl.cpp', rb'GetBtnStatus', rb'get_user_lite_info', rb'VipGuard'):
    occ = [m.start() for m in re.finditer(pat, d)]
    print('%-22s %dx %s' % (pat.decode(), len(occ), occ[:8]))

# contexto do caminho ExportImpl.cpp
for m in list(re.finditer(rb'ExportImpl\.cpp', d))[:3]:
    j = m.start()
    seg = d[max(0, j - 2500):j + 2500]
    strs = [s.decode('latin1', 'replace') for s in re.findall(rb'[\x20-\x7e]{4,}', seg)]
    keep = [t for t in strs if any(k in t.lower() for k in ('export', 'vip', 'guard', 'status', 'water', 'benefit'))]
    print('--- contexto @%d ---' % j)
    for t in list(dict.fromkeys(keep))[:45]:
        print('   ', t[:150])
    print()
