"""Servidor TLS local FASE 2: intercepta hosts de comercio do CapCut (hosts -> 127.0.0.1),
reescreve respostas de VIP/beneficio para 'Pro', loga tudo e repassa ao upstream.
Offline: se o upstream falhar, serve a ultima resposta cacheada (reescrita)."""
import socket
import ssl
import threading
import os
import time
import json
import gzip
import zlib
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(_HERE, 'mitm')
LOG = os.path.join(_HERE, 'local_capture.log')
BODYDIR = os.path.join(_HERE, 'local_bodies')
os.makedirs(BODYDIR, exist_ok=True)

# IPs reais dos hosts interceptados (atualize com scripts/dns_commerce.ps1 se mudarem)
REAL_IP = {
    'commerce-api-sg.capcutapi.com': '2.17.166.146',
    'commerce-api.capcutapi.com': '2.17.166.133',
    'commerce-api-va.capcut.com': '2.17.162.3',
    'commercepro.capcut.com': '2.17.166.147',
    'www.capcut.com': '2.17.162.2',
    'feed-api-sg.capcut.com': '2.17.162.2',
    'commerce-api-sg.capcut.com': '2.17.162.2',
    'commerce-api-va.capcutapi.com': '2.17.166.150',
    'commerce-api-v2-boot.capcutapi.com': '2.17.166.135',
}

PRO_MONTHLY_CREDITS = 1750
UNLIM = -1

EXTRA_PATH = os.path.join(_HERE, 'vip_extra.json')
_extra_cache = [0.0, {}]

def _load_extra():
    try:
        mt = os.path.getmtime(EXTRA_PATH)
        if mt != _extra_cache[0]:
            _extra_cache[0] = mt
            _extra_cache[1] = json.load(open(EXTRA_PATH, encoding='utf-8'))
    except Exception:
        pass
    return _extra_cache[1]

_seq = [0]
_lock = threading.Lock()
_cache = {}   # (host, path, bodyhash) -> (statusline, headers_list, body_bytes)

def log(s):
    with _lock:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(s)

def save_body(tag, host, path, data):
    _seq[0] += 1
    safe = (host + path).replace('/', '_').replace('?', '_').replace('&', '_').replace('=', '')[:80]
    p = os.path.join(BODYDIR, '%03d_%s_%s.bin' % (_seq[0], tag, safe))
    try:
        with open(p, 'wb') as f:
            f.write(data)
    except Exception:
        pass
    return p

def decompress(data):
    for fn in (lambda x: gzip.decompress(x), lambda x: zlib.decompress(x), lambda x: zlib.decompress(x, -15)):
        try:
            return fn(data)
        except Exception:
            pass
    return data

# ---------------- REWRITES ----------------

def _reserialize(obj):
    obj.pop('response', None)
    if 'data' in obj and isinstance(obj['data'], dict):
        # response espelhado (mesmo formato original: string JSON escapada)
        obj['response'] = json.dumps(obj['data'], separators=(',', ':'), ensure_ascii=False)
        # reordena como no original: ret, errmsg, systime, log_id, response, sign, data
        keys = ['ret', 'errmsg', 'systime', 'log_id', 'response', 'sign', 'data']
        ordered = {k: obj[k] for k in keys if k in obj}
        for k in obj:
            if k not in ordered:
                ordered[k] = obj[k]
        return json.dumps(ordered, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def rewrite_user_info(raw):
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if not isinstance(d, dict) or 'flag' not in d:
        return raw, False
    now_ms = int(time.time() * 1000)
    far_ms = now_ms + 365 * 24 * 3600 * 1000
    d['flag'] = True
    d['start_time'] = now_ms
    d['end_time'] = far_ms
    d['is_first_subscribe'] = False
    d['is_cancel_subscribe'] = False
    ws = d.get('workspace_subscribe_info')
    if isinstance(ws, dict):
        ws['flag'] = True
        ws['vip_real_end'] = far_ms
    # extras dinamicos (vip_extra.json) p/ iterar sem reiniciar o server
    for k, v in _load_extra().get('user_info_extra', {}).items():
        if isinstance(v, str):
            if v == 'now':
                v = now_ms
            elif v.startswith('+'):
                days = float(v[1:-1])
                v = now_ms + int(days * 24 * 3600 * 1000)
        d[k] = v
    return _reserialize(obj), True

def rewrite_v1_benefit(raw):
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if not isinstance(d, dict) or not isinstance(d.get('benefit_list'), list):
        return raw, False
    for b in d['benefit_list']:
        if not isinstance(b, dict):
            continue
        b['flag'] = True
        bt = b.get('benefit_type', '')
        if bt == 'user_credit':
            b['quota_all'] = PRO_MONTHLY_CREDITS
            b['quota_left'] = PRO_MONTHLY_CREDITS
        elif b.get('quota_left') in (0, None) and b.get('quota_all', 0) > 0:
            b['quota_left'] = b['quota_all']
    return _reserialize(obj), True

def rewrite_v3_benefit(raw):
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if not isinstance(d, dict) or not isinstance(d.get('asset_list'), list):
        return raw, False
    for a in d['asset_list']:
        if not isinstance(a, dict):
            continue
        details = a.get('asset_details')
        if not isinstance(details, list):
            continue
        any_unlim = False
        for det in details:
            if not isinstance(det, dict):
                continue
            role = det.get('role')
            pm = det.get('pay_mode')
            if role in ('vip', 'teams') or pm == 'Subscribe':
                det['quota_all'] = UNLIM
                det['quota_left'] = UNLIM
                any_unlim = True
            elif pm == 'UserCredit' and role == 'vip':
                det['quota_all'] = PRO_MONTHLY_CREDITS
                det['quota_left'] = PRO_MONTHLY_CREDITS
        # top-level do asset: usa o melhor detalhe
        tops = []
        for det in details:
            if isinstance(det, dict):
                tops.append((det.get('quota_all', 0), det.get('quota_left', 0)))
        if tops:
            best_all = max(t[0] for t in tops)
            best_left = max(t[1] for t in tops)
            a['quota_all'] = best_all
            a['quota_left'] = best_left
    return _reserialize(obj), True

def rewrite_vip_get_benefits(raw):
    # data: loc, pay[], limit_free[], once_func[], disable[], whitelist{feature_keys,resource_ids}
    # Pro: todas as funcoes 'pay' (e 'disable') viram whitelist (disponiveis); pay esvazia
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if not isinstance(d, dict) or not isinstance(d.get('pay'), list):
        return raw, False
    wl = d.get('whitelist')
    if not isinstance(wl, dict):
        wl = {}
        d['whitelist'] = wl
    fk = wl.get('feature_keys')
    if not isinstance(fk, list):
        fk = []
        wl['feature_keys'] = fk
    moved = 0
    for key in ('pay', 'disable'):
        lst = d.get(key)
        if isinstance(lst, list):
            for item in lst:
                if isinstance(item, str) and item not in fk:
                    fk.append(item)
                    moved += 1
            d[key] = []
    if moved:
        log('  [vip_get_benefits] %d funcoes pay/disable -> whitelist\n' % moved)
    return _reserialize(obj), True

def rewrite_start_up(raw):
    # teams_guide_libra_config.user_type: V0 (free) -> V1 (guess p/ pago)
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if not isinstance(d, dict):
        return raw, False
    tg = d.get('teams_guide_libra_config')
    if isinstance(tg, dict) and tg.get('user_type') == 'V0':
        tg['user_type'] = 'V1'
    return _reserialize(obj), True

def rewrite_workspace_creator(raw):
    # workspace_creator_info: flag false -> true (mantem ret original)
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if not isinstance(d, dict) or 'flag' not in d:
        return raw, False
    now_ms = int(time.time() * 1000)
    d['flag'] = True
    if not d.get('start_time'):
        d['start_time'] = now_ms
    if not d.get('end_time'):
        d['end_time'] = now_ms + 365 * 24 * 3600 * 1000
    return _reserialize(obj), True

def rewrite_price_list(raw):
    # teste: preco visivel absurdo para provar que o app parseia a resposta reescrita
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if not isinstance(d, dict) or not isinstance(d.get('all_price_list'), list):
        return raw, False
    for p in d['all_price_list']:
        if not isinstance(p, dict):
            continue
        p['price_tips'] = '0.01'
        p['total_amount'] = 1
        p['package_name'] = 'TESTE-OFFLINE ' + str(p.get('package_name') or '')
        if p.get('vip_price_tips'):
            p['vip_price_tips'] = 'R$0.01 ' + str(p['vip_price_tips'])
    return _reserialize(obj), True

def rewrite_user_credit(raw):
    # creditos: injeta saldo grande (sistema de creditos do CapCut 9.x)
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if not isinstance(d, dict):
        return raw, False
    c = d.get('credit')
    if isinstance(c, dict):
        big = 999999
        for k in list(c.keys()):
            if isinstance(c[k], (int, float)):
                c[k] = big
    d['credit'] = {'vip_credit': 999999, 'gift_credit': 999999, 'purchase_credit': 999999}
    if not isinstance(d.get('credits_detail'), dict) or not d.get('credits_detail'):
        d['credits_detail'] = {'vip_credit': {'amount': 999999, 'expire_time': int(time.time() * 1000) + 365 * 24 * 3600 * 1000}}
    return _reserialize(obj), True

def rewrite_pop_up(raw):
    # pop_up credit config
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if isinstance(d, dict) and isinstance(d.get('credit'), dict):
        cr = d['credit']
        cr['enable'] = True
        cr['vip_amount'] = 999999
        cr['standard_amount'] = 999999
        cr['gift_amount'] = 999999
        cr['ultra_amount'] = 999999
        cr['teams_amount'] = 999999
    return _reserialize(obj), True

def rewrite_resource_position(raw):
    # cards de marketing (personal_subscribeinfo_card etc.) — remover entraves de UI
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if not isinstance(d, dict):
        return raw, False
    ri = d.get('resource_info')
    changed = False
    if isinstance(ri, dict):
        for k in list(ri.keys()):
            if 'subscribe' in k.lower() or 'vip' in k.lower() or 'pro' in k.lower():
                ri[k] = {}
                changed = True
    rinfo = d.get('resource_infos')
    if isinstance(rinfo, dict):
        for k in list(rinfo.keys()):
            if isinstance(rinfo[k], list):
                rinfo[k] = [it for it in rinfo[k] if not (isinstance(it, dict) and
                            ('subscribe' in str(it.get('name', '')).lower() or
                             'vip' in str(it.get('name', '')).lower()))]
                changed = True
    if changed:
        log('  [resource_position] cards de subscribe removidos\n')
    return _reserialize(obj), True

def rewrite_lite_info(raw):
    # data.user_info: {vip:{flag,vip_level,end_time}, teams:{...}} — fonte do gate de export
    try:
        obj = json.loads(raw.decode('utf-8'))
    except Exception:
        return raw, False
    d = obj.get('data')
    if not isinstance(d, dict):
        return raw, False
    ui = d.get('user_info')
    if not isinstance(ui, dict):
        return raw, False
    now = int(time.time())
    far = now + 365 * 24 * 3600
    vip = ui.get('vip')
    if isinstance(vip, dict):
        vip['flag'] = True
        vip['vip_level'] = 'svip'
        vip['end_time'] = far
    for k, v in _load_extra().get('lite_extra', {}).items():
        ui[k] = v
    log('  [lite_info] vip.flag=true vip_level=svip\n')
    return _reserialize(obj), True

def rewrite_response(path, raw):
    p = path.lower()
    if 'get_user_lite_info' in p:
        return rewrite_lite_info(raw)
    if 'subscription/user_info' in p:
        return rewrite_user_info(raw)
    if 'v3/benefits/batch_get_user_benefit' in p:
        return rewrite_v3_benefit(raw)
    if 'v1/benefits/batch_get_user_benefit' in p:
        return rewrite_v1_benefit(raw)
    if 'vip_get_benefits' in p or 'vip/get_benefits' in p:
        return rewrite_vip_get_benefits(raw)
    if 'common/start_up' in p:
        return rewrite_start_up(raw)
    if 'workspace_creator_info' in p:
        return rewrite_workspace_creator(raw)
    if 'cc_price_list' in p:
        return rewrite_price_list(raw)
    if 'benefits/user_credit' in p:
        return rewrite_user_credit(raw)
    if 'subscription/pop_up' in p:
        return rewrite_pop_up(raw)
    if 'resource_position' in p:
        return rewrite_resource_position(raw)
    return raw, False

# ---------------- HTTP ----------------

def read_request(rfile):
    line = rfile.readline(65536)
    if not line:
        return None
    reqline = line.decode('latin1').strip()
    hlist = []
    headers = {}
    while True:
        hl = rfile.readline(65536)
        if not hl or hl in (b'\r\n', b'\n'):
            break
        txt = hl.decode('latin1').strip()
        hlist.append(txt)
        if ':' in txt:
            k, v = txt.split(':', 1)
            headers[k.strip().lower()] = v.strip()
    body = b''
    cl = headers.get('content-length')
    if cl and cl.isdigit():
        body = rfile.read(int(cl))
    return reqline, hlist, headers, body

def dechunk(rfile):
    out = b''
    while True:
        szline = rfile.readline(65536).strip()
        if not szline:
            break
        try:
            size = int(szline.split(b';')[0], 16)
        except ValueError:
            break
        if size == 0:
            while True:
                t = rfile.readline(65536)
                if t in (b'\r\n', b'\n', b''):
                    break
            break
        out += rfile.read(size)
        rfile.readline(65536)
    return out

def build_response(statusline, rheaders, body):
    resp = statusline + '\r\n'
    for h in rheaders:
        k = h.split(':', 1)[0].strip().lower()
        if k in ('content-length', 'transfer-encoding', 'connection', 'content-encoding'):
            continue
        resp += h + '\r\n'
    resp += 'Content-Length: %d\r\nConnection: close\r\n\r\n' % len(body)
    return resp.encode('latin1') + body

def handle(conn, addr):
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(os.path.join(BASE, 'server.crt'), os.path.join(BASE, 'server.key'))
        tls = ctx.wrap_socket(conn, server_side=True)
        rfile = tls.makefile('rb')
        req = read_request(rfile)
        if not req:
            tls.close()
            return
        reqline, hlist, headers, body = req
        parts = reqline.split(' ')
        method, path = (parts + ['GET', '/'])[:2]
        host = headers.get('host', '?')
        ts = time.strftime('%H:%M:%S')
        log('\n==== %s %s %s ====\n' % (ts, method, host + path))
        for h in hlist:
            log('  H ' + h + '\n')
        if body:
            p = save_body('req', host, path, body)
            log('  [REQ BODY %d] %s\n' % (len(body), p))
            log('  ' + body[:1200].decode('utf-8', 'replace') + '\n')

        real = REAL_IP.get(host)
        statusline = None
        rheaders = None
        rbody = None
        used_cache = False
        ckey = (host, path, hashlib.md5(body).hexdigest())
        if real:
            try:
                upctx = ssl.create_default_context()
                with socket.create_connection((real, 443), timeout=8) as up:
                    uptls = upctx.wrap_socket(up, server_hostname=host)
                    ureq = method + ' ' + path + ' HTTP/1.1\r\n'
                    for h in hlist:
                        k = h.split(':', 1)[0].strip().lower()
                        if k in ('host', 'connection'):
                            continue
                        ureq += h + '\r\n'
                    ureq += 'Host: ' + host + '\r\nConnection: close\r\n\r\n'
                    uptls.sendall(ureq.encode('latin1') + body)
                    urfile = uptls.makefile('rb')
                    statusline = urfile.readline(65536).decode('latin1').strip()
                    rheaders = []
                    while True:
                        hl = urfile.readline(65536)
                        if hl in (b'\r\n', b'\n', b''):
                            break
                        rheaders.append(hl.decode('latin1').strip())
                    clen = ''
                    for h in rheaders:
                        if h.lower().startswith('content-length:'):
                            clen = h.split(':', 1)[1].strip()
                    if clen and clen.isdigit():
                        rbody = urfile.read(int(clen))
                    else:
                        rbody = dechunk(urfile)
                    uptls.close()
            except Exception as e:
                log('  (upstream falhou: %r) -> cache/offline\n' % e)
                statusline = None
        if statusline is None:
            hit = _cache.get(ckey)
            if hit:
                statusline, rheaders, rbody = hit
                used_cache = True
                log('  (SERVINDO DO CACHE OFFLINE)\n')
            else:
                rbody = json.dumps({'ret': '1', 'errmsg': 'offline-no-cache'}).encode()
                statusline = 'HTTP/1.1 200 OK'
                rheaders = ['Content-Type: application/json; charset=utf-8']

        if rbody and statusline.startswith('HTTP/1.1 200'):
            plain = decompress(rbody)
            new, did = rewrite_response(path, plain)
            if did:
                log('  [REWRITE APLICADO]\n')
                rbody = new
            else:
                # CORPO PLANO SEMPRE: build_response remove Content-Encoding,
                # entao enviar body comprimido faria o cliente ver binario
                rbody = plain
            _cache[ckey] = (statusline, list(rheaders), rbody)

        p = save_body('resp', host, path, rbody)
        log('==== %s %s (body %d bytes, cache=%s) %s ====\n' % (statusline, 'CACHE' if used_cache else 'UPSTREAM', len(rbody or b''), used_cache, p))
        for h in rheaders:
            log('  H ' + h + '\n')
        try:
            log('  ' + (rbody or b'')[:2500].decode('utf-8', 'replace') + '\n')
        except Exception:
            pass

        tls.sendall(build_response(statusline, rheaders, rbody))
        tls.close()
    except Exception as e:
        try:
            log('!! erro conexao: %r\n' % e)
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 443))
    s.listen(64)
    log('\n\n##### servidor local TLS FASE2 no ar em %s (porta 443) #####\n' % time.strftime('%H:%M:%S'))
    print('ouvindo na 443 (fase 2)')
    while True:
        c, a = s.accept()
        threading.Thread(target=handle, args=(c, a), daemon=True).start()

if __name__ == '__main__':
    main()
