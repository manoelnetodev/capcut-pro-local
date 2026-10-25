# Contribuindo / Contributing

## pt-BR

Bem-vindo! Este projeto documenta e automatiza um método de **configuração**
(sem patch em binários) para liberar o gate de export Pro do CapCut PC em modo offline.

### Como testar uma mudança
1. Tenha o CapCut PC instalado (a versão validada atual é **9.6.0.4097**).
2. Rode `INSTALAR.ps1` como administrador (hosts + CA + firewall + server).
3. Suba o server: `INICIAR_SERVER.cmd` (porta 443; mata quem ocupava a porta antes).
4. Aplique o modo Pro: `MODO_OFFLINE_pro.cmd` (fecha o app, re-aplica
   `scripts/edit_settings_pro.py`, ativa as regras `CapCutOffline*`, reabre).
5. Abra um projeto e exporte — deve exportar **sem paywall e sem marca d'água**.

### Regras importantes
- **Edição no blob MMKV (`settings_json`): só substituições de MESMO tamanho.**
  O MMKV não tolera mudança de tamanho de valor; escrita sempre `r+b` sem truncar,
  com o app **fechado** (mate também `parfait_crash_handler` e auxiliares por caminho —
  ver `scripts/kill_all_capcut.ps1`).
- O app online re-poluía o blob pela rede TTNet; por isso o fix precisa ser
  **re-aplicado a cada ativação do modo offline** (o toggle já faz isso).
- O server usa **apenas stdlib** do Python 3. Não adicione dependências pip.
- Não commite `backup/`, `logs/`, `*.bak` nem chaves privadas (`server/mitm/*.key`).
- Certificados: gere com `scripts/gen_ca.py` e `scripts/gen_cert.py`
  (o cert do server precisa de SANs para todos os hosts interceptados).

### Descobertas bem-vindas
Documente na `ESTUDO_CAPCUT_PRO.md` (seções numeradas, data no título):
novos knobs de config, mudanças em atualizações do CapCut, hosts de comércio novos,
e resultados de experimentos (inclusive negativos — eles valem muito).

### Portabilidade
Scripts não podem ter caminho de usuário hardcoded:
- PowerShell: use `$PSScriptRoot` / `$env:LOCALAPPDATA` (os `.cmd` usam `%~dp0`).
- Python: use `__file__` / `os.environ['LOCALAPPDATA']`.
- Os `.ps1` de sistema se auto-elevam (UAC) quando necessário.

## English

Short version: config-only method (no binary patches). MMKV blob edits must be
**equal-length byte substitutions** with the app closed. Server is stdlib-only Python.
Reproduce with `INSTALAR.ps1` → `INICIAR_SERVER.cmd` → `MODO_OFFLINE_pro.cmd` → export.
Document findings (positive or negative) in `ESTUDO_CAPCUT_PRO.md` as dated numbered sections.
Keep user-specific paths out of scripts; keep `backup/`, logs, `*.bak` and private keys out of git.
