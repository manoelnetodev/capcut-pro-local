# CapCut Pro Local

**Run CapCut PC (Windows) with the Pro export gate opened in 100% offline mode — no DLL patch, no account tricks.** Just hosts + a local TLS server + Windows Firewall + two equal-length edits in CapCut's own config blob.

> Research/preservation project. Not affiliated with ByteDance/CapCut. You are responsible for complying with CapCut's Terms of Service in your jurisdiction. Binary was analyzed, not modified.

## What it does

| Mode | What you get | Export |
|---|---|---|
| **PRO offline** (default work mode) | Pro effects/filters apply free; export runs **free, no watermark** | 🆓 |
| **STORE online** | App fully online: browse new catalogs, download new assets | 💰 paid |

## How it works (30s version)

1. `hosts` redirects CapCut's commerce APIs to `127.0.0.1`.
2. `server/local_tls_server.py` (port 443, own CA) answers those APIs: passthrough to the real servers + Pro rewrites (user_info, benefits, get_benefits, lite_info, credits).
3. Firewall rules (`CapCutOffline *`) block the app's non-loopback egress → the export gate falls into the app's **offline decision path**.
4. That offline path is gated by CapCut's own config knob
   `vip_export.export_intercept_exper_offline_time` inside `User Data\MMKV\settings_json`.
   Its shipped value (`1747238400`, May 2025) is expired → paywall. We replace **every copy**
   of the blob with `2999999999` (2065) — equal-length byte surgery, MMKV-safe.
   When the app runs online it re-fetches config via TTNet and re-pollutes the blob, so the
   offline toggle **re-applies the edits on every activation**.

## Requirements

- Windows 10/11 with CapCut PC installed (validated on 9.6.0.4097; see docs for other versions).
- Python 3 (stdlib only, no pip packages).
- Admin rights (hosts, firewall, port 443).

## Quick start

```bat
:: 1) copy this folder anywhere, then:
powershell -ExecutionPolicy Bypass -File INSTALAR.ps1   :: admin; sets hosts + CA + firewall + starts server

:: 2) start CapCut once ONLINE (server running) and log in (Google login passes through our server)

:: 3) daily use:
MODO_OFFLINE_pro.cmd    :: work mode: Pro export free, fully offline
MODO_LOJA_online.cmd    :: store mode: online, download new effects/templates, then go back
INICIAR_SERVER.cmd      :: (re)start the local server (needed for login)
scripts\create_shortcuts.ps1   :: creates the 3 Desktop shortcuts
```

## Layout

```
MODO_OFFLINE_pro.cmd / MODO_LOJA_online.cmd / INICIAR_SERVER.cmd   the three buttons
INSTALAR.ps1                    fresh-machine setup
METODO.md                       full manual (pt-BR)
ESTUDO_CAPCUT_PRO.md            complete reverse-engineering log (pt-BR)
server/                         TLS MITM server + certs + captured extras
scripts/                        fixer (edit_settings_pro.py), toggles, helpers
RE/                             disassembly dumps and analysis notes
backup/                         original DLLs and config snapshots (kept OUT of git — large)
```

## Known limits

- Online mode still shows the paywall (server-side entitlement is real; see docs §16.9 — a 1–2 byte DLL patch plan exists in `RE/`).
- `REAL_IP` table in the server may need refreshing (`scripts/dns_commerce.ps1`).
- A CapCut major update may rename the config knob; watchlist in `METODO.md`.

## License

MIT — see `LICENSE`. Research artifacts (`ESTUDO_CAPCUT_PRO.md`, `RE/`) document how the gate works; nothing here modifies CapCut binaries.
