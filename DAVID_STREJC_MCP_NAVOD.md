# 🚀 David Strejc MCP Servery - Kompletní Návod

Nainstalované MCP servery od Davida Strejce pro Claude Code.

---

## 📦 Nainstalované Servery

### 1️⃣ **SAGE-MCP** ⭐⭐⭐⭐⭐
**Lokace:** `~/sage-mcp/`
**Stav:** ✅ Nainstalováno
**Funkce:** Univerzální AI asistent s různými režimy

#### Režimy:
- 💬 **Chat** - Obecná diskuze
- 🔍 **Analyze** - Analýza kódu
- 📝 **Review** - Code review
- 🐛 **Debug** - Debugging
- 📋 **Plan** - Plánování projektů
- 🧪 **Test** - Generování testů
- ♻️ **Refactor** - Refaktoring kódu
- 🧠 **Think** - Hloubková analýza

#### Konfigurace:
```bash
# Edituj API klíče a nastavení
nano ~/sage-mcp/.env
```

**Důležité:**
- Defaultně používá **Ollama (ZDARMA)**
- Fallback: Gemini API (máš klíč v .env)
- Model: `qwen2.5-coder:32b` nebo `auto`

#### Použití v Claude:
```
Můžeš říct: "Use SAGE in debug mode to find bugs in this code"
```

---

### 2️⃣ **Gmail MCP Server**
**Lokace:** `~/gmail-mcp-server/`
**Stav:** ⚠️ Nainstalováno, vyžaduje konfiguraci
**Funkce:** Práce s Gmailem přímo z Claude

#### Funkce:
- 📧 Čtení emailů
- 📤 Posílání emailů
- 🏷️ Správa labelů
- 🔍 Vyhledávání v emailech
- 📎 Práce s přílohami

#### Konfigurace (POTŘEBA UDĚLAT):
```bash
# 1. Jdi na Google Account
https://myaccount.google.com/apppasswords

# 2. Vygeneruj "App Password" pro Mail

# 3. Edituj .env
nano ~/gmail-mcp-server/.env

# 4. Vyplň:
GMAIL_EMAIL=tvuj.email@gmail.com
GMAIL_PASSWORD=tvuj_app_password_zde

# 5. Restartuj Claude Code
```

**Bez konfigurace nebude fungovat!**

---

### 3️⃣ **LaskoBOT** (Browser Automation)
**Lokace:** `~/laskobot/`
**Stav:** ⚠️ Nainstalováno, vyžaduje dodatečný setup
**Funkce:** Ovládání prohlížeče z Claude

#### Funkce:
- 🌐 Navigace na webové stránky
- 👆 Klikání na elementy
- ⌨️ Vyplňování formulářů
- 📸 Screenshots
- 🔍 Vyhledávání elementů
- 📋 Multi-tab management

#### Dodatečný Setup (POTŘEBA UDĚLAT):

1. **Spusť HTTP server:**
   ```bash
   cd ~/laskobot
   node dist/index-http.cjs
   ```

   Nebo lepší - nastav systemd service:
   ```bash
   cd ~/laskobot
   ./scripts/systemd-user-install.sh
   ```

2. **Nainstaluj browser extension:**
   - **Chrome:**
     - Otevři `chrome://extensions/`
     - Zapni "Developer mode"
     - "Load unpacked" → `~/laskobot/chrome-extension/`

   - **Firefox:**
     - Otevři `about:debugging#/runtime/this-firefox`
     - "Load Temporary Add-on" → `~/laskobot/firefox-extension/manifest.json`

3. **Ověř spojení:**
   - Browser extension se připojí na `ws://localhost:8765`
   - HTTP MCP server běží na `http://localhost:3000/mcp`

**Bez těchto kroků nebude fungovat!**

---

## 🎯 Jak Používat MCP Servery v Claude

### Automatická Detekce
Claude Code automaticky načte všechny MCP servery z `.mcp.json` souborů.

### Manuální Kontrola
```bash
# Zobraz všechny MCP servery
claude mcp list

# Zobraz detaily konkrétního serveru
claude mcp info sage
claude mcp info gmail
claude mcp info laskobot
```

### Enable/Disable
```bash
# Vypni server (pokud nefunguje)
claude mcp disable sage

# Zapni zpět
claude mcp enable sage
```

---

## 📊 Stav MCP Serverů

| Server | Status | Vyžaduje Setup? |
|--------|--------|-----------------|
| **SAGE-MCP** | ✅ Funguje | ❌ Ne (používá Ollama) |
| **Gmail MCP** | ⚠️ Nefunguje | ✅ Ano (API key) |
| **LaskoBOT** | ⚠️ Nefunguje | ✅ Ano (systemd + extension) |

---

## 🔧 Řešení Problémů

### SAGE-MCP nefunguje
```bash
# Zkontroluj, jestli Ollama běží
curl http://localhost:11434/api/tags

# Zkontroluj logy
cd ~/sage-mcp
python3 server.py
```

### Gmail MCP nefunguje
```bash
# Zkontroluj .env
cat ~/gmail-mcp-server/.env

# Testuj server
cd ~/gmail-mcp-server
source .venv/bin/activate
python src/email_client/server.py
```

### LaskoBOT nefunguje
```bash
# Zkontroluj, jestli HTTP server běží
curl http://localhost:3000/mcp

# Spusť manuálně
cd ~/laskobot
node dist/index-http.cjs
```

---

## 📚 Dokumentace

### Oficiální Repozitáře:
- **SAGE-MCP:** https://github.com/david-strejc/sage-mcp
- **Gmail MCP:** https://github.com/david-strejc/gmail-mcp-server
- **LaskoBOT:** https://github.com/david-strejc/laskobot

### Lokální Dokumentace:
- SAGE: `~/sage-mcp/CLAUDE.md`
- Gmail: `~/gmail-mcp-server/README.md`
- LaskoBOT: `~/laskobot/CLAUDE.md`

---

## 🚀 Quick Start Checklist

### Pro SAGE (hned k použití):
- [x] Nainstalováno
- [x] Nakonfigurováno s Ollama
- [x] Přidáno do Claude Code
- [ ] Vyzkoušej: "Use SAGE in chat mode"

### Pro Gmail (vyžaduje setup):
- [x] Nainstalováno
- [ ] Vygeneruj App Password
- [ ] Vyplň ~/gmail-mcp-server/.env
- [ ] Restartuj Claude Code
- [ ] Vyzkoušej: "Check my recent emails"

### Pro LaskoBOT (vyžaduje setup):
- [x] Nainstalováno
- [ ] Spusť HTTP server (systemd nebo manuálně)
- [ ] Nainstaluj browser extension
- [ ] Vyzkoušej: "Navigate to google.com"

---

## 💡 Tipy

1. **SAGE používej pro coding** - má nejlepší režimy pro vývoj
2. **Gmail pro automatizaci emailů** - skvělé pro hromadné operace
3. **LaskoBOT pro web scraping** - ale vyžaduje více setupu

---

Vytvořeno: 2025-11-19
Autor: Claude Code (instalace MCP serverů od Davida Strejce)
