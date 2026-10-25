# MÉTODO CapCut PRO LOCAL — Manual (out/2026)

## O que é
CapCut PC (Windows) rodando com **export Pro + recursos Pro liberados 100% offline**,
sem patch na DLL, usando só: hosts + server TLS local + firewall + 2 edits no config MMKV.

## Como funciona (resumo técnico)
1. **hosts** aponta `commerce-api*`, `www.capcut.com`, `feed-api-sg` -> `127.0.0.1`.
2. **server local** (`server\local_tls_server.py`, porta 443, CA própria em `server\mitm`)
   atende essas APIs: passthrough para o mundo real + rewrites Pro
   (user_info, benefits, get_benefits, lite_info=svip, credits...).
3. **Firewall**: regras `CapCutOffline *` bloqueiam saída não-loopback dos exes do CapCut.
   Sem rede, o gate de export cai no caminho *offline* do app.
4. **O selo da vitória**: o gate offline obedece
   `vip_export.export_intercept_exper_offline_time` no blob `User Data\MMKV\settings_json`.
   O valor real (1747238400 = mai/2025) está VENCIDO => paywall offline.
   Trocado por `2999999999` (2065) em TODAS as cópias do blob => export livre sem marca d'água.
   (Online, o app re-baixa a config via TTNet e re-poe o blob — por isso o modo offline
   RE-APLICA o edit a cada ativação.)

## Uso diário
- **`MODO_OFFLINE_pro.cmd`** (atalho Desktop "CapCut PRO (offline)"):
  fecha app -> re-aplica edits Pro -> liga firewall offline -> abre CapCut.
  => export grátis, sem marca d'água, efeitos Pro livres. **TRABALHE ASSIM.**
- **`MODO_LOJA_online.cmd`** (atalho "CapCut MODO LOJA (online)"):
  fecha app -> libera firewall -> abre CapCut 100% online.
  => catálogo novo, downloads de efeitos/templates (export pago neste modo).
  Ao terminar, volte no MODO_OFFLINE.
- **`INICIAR_SERVER.cmd`**: (re)inicia o server local na 443. Necessário p/ LOGIN do app
  (o login passa por www.capcut.com -> nosso server). Se o CapCut já está logado e o
  server não estiver ouvindo, o toggle avisa no log.

## Arquivos
```
C:\Users\Manoel\Desktop\capcut-pro-local\
├── MODO_OFFLINE_pro.cmd      <- botão Pro offline
├── MODO_LOJA_online.cmd      <- botão modo loja
├── INICIAR_SERVER.cmd        <- sobe o server 443 (admin)
├── INSTALAR.ps1              <- setup completo em uma máquina nova (admin)
├── METODO.md                 <- este manual
├── ESTUDO_CAPCUT_PRO.md      <- doc completa da engenharia reversa
├── server\
│   ├── local_tls_server.py   <- server MITM das APIs (stdlib apenas)
│   ├── vip_extra.json        <- extras injetados no user_info (editar sem reiniciar)
│   ├── mitm\                 <- ca.crt/ca.key/server.crt/server.key
│   └── local_bodies\         <- captura req/resp
├── scripts\
│   ├── toggle_mode.ps1       <- liga/desliga offline + re-aplica edits
│   ├── edit_settings_pro.py  <- <- O FIX: timestamp 2065 + lite null em tudo
│   ├── iniciar_server.ps1
│   └── kill/reopen/check ...
├── backup\
│   ├── VECreator96.dll.orig  <- DLL original da versão ativa (271 MB, SHA-256 na doc)
│   ├── VECreator.dll.orig    <- DLL da 9.0.0.3858 (versão morta)
│   ├── capcut_backup_completo\  <- Config + MMKV antes de qualquer edição
│   └── settings_json_*.bak   <- snapshots do blob
└── RE\  logs\                <- disassembly, dumps, análise Claude, histórico
```

## Restauração rápida
- CapCut voltou a cobrar export? Rode `MODO_OFFLINE_pro.cmd` (ele re-aplica os edits).
- Server caiu? `INICIAR_SERVER.cmd` (UAC).
- Perdeu hosts/CA/regras? `INSTALAR.ps1` como admin.
- Trouxe p/ outra máquina? Copie a pasta inteira, rode `INSTALAR.ps1`, faça login Google
  (com server no ar), use os botões.

## Sabotagens que podem quebrar (watchlist)
- Atualização do CapCut (nova pasta `Apps\<ver>\`): re-rodar `INSTALAR.ps1` (regras de
  firewall e hosts continuam; o blob é por usuário, sobrevive; timestamp pode mudar de nome).
- Se removerem o knob `export_intercept_exper_offline_time`: há plano B documentado
  (patch 1-2 bytes: thunk `movzx edx,al`->`mov dl,1` no RVA 0x6633ef2 da DLL ativa, ou
  inversões no seletor de status 0x18662cf40 — ver doc seção 16.7 + `RE\claude_report_region.txt`).
- Verificação de `sign` nos corpos (RSA-2048): hoje o app aceita nossos rewrites nos
  caminhos usados offline; o gate ONLINE ainda rejeita (documentado, seção 16.9).

## Estado validado (24/10/2026)
- Versão ativa 9.6.0.4097; login Google OK; offline: export livre sem marca d'água;
  efeitos PRO aplicam sem assinatura; loja: catálogos baixam normally.
