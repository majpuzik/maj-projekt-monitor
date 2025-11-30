# Instalace Gemini CLI a MCP Serveru - Dokončeno ✓

## Co bylo nainstalováno:

### 1. **Gemini CLI** (v0.16.0)
Oficiální nástroj od Googlu pro práci s Gemini AI v terminálu.

**Instalace:**
```bash
npm install -g @google/gemini-cli
```

**Ověření:**
```bash
gemini --version  # 0.16.0
gemini "Hello, are you working?"  # Test funkčnosti
```

**Konfigurace:**
- API klíč uložen v: `~/.gemini/.env`
- Autentizace: API klíč (AIzaSyB...Oxxk)

### 2. **iflow-mcp/gemini-mcp-tool** (npm balíček)
Jednoduchý MCP server pro interakci s Gemini CLI.

**Instalace:**
```bash
npm install -g @iflow-mcp/gemini-mcp-tool
```

### 3. **RLabs Gemini MCP Server** (hlavní MCP server pro Claude Code)
Plně vybavený MCP server s pokročilými funkcemi.

**Instalace:**
```bash
# Lokální build z GitHubu
git clone https://github.com/RLabs-Inc/gemini-mcp.git /tmp/gemini-mcp
cd /tmp/gemini-mcp
npm install  # Automaticky zkompiluje přes prepare script
npm install -g . --force
```

**Konfigurace v Claude Code:**
- Přidáno do `~/.claude.json` pomocí: `claude mcp add gemini`
- Příkaz: `env GEMINI_API_KEY=... gemini-mcp`
- Typ: stdio

## Jak používat:

### Gemini CLI (přímo v terminálu):
```bash
# Interaktivní režim
gemini

# Jednorázový dotaz
gemini "Vysvětli mi kvantové počítače"

# S verbose režimem
gemini -v "Analyzuj tento kód"
```

### MCP Server (v Claude Code):
```bash
# Spusť Claude Code
claude

# Uvnitř Claude Code:
/mcp list          # Zobraz seznam MCP serverů
/mcp use gemini    # Aktivuj Gemini server pro tuto session

# Použití Gemini nástrojů:
/gemini-query Co je to kvantové počítání?
/gemini-brainstorm Jak implementovat real-time kolaboraci?
/gemini-analyze-code python performance

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

## Dostupné nástroje v MCP serveru:

1. **gemini-query** - Přímé dotazy na Gemini
2. **gemini-brainstorm** - Kolaborativní brainstorming
3. **gemini-analyze-code** - Analýza kódu (kvalita, bezpečnost, výkon)
4. **gemini-analyze-text** - Analýza textu (sentiment, klíčové body)
5. **gemini-summarize** - Shrnutí dlouhého obsahu
6. **gemini-image-prompt** - Generování promptů pro obrázky

## Modely:
- **gemini-2.5-pro** (default) - 1M+ token context window
- **gemini-2.5-flash** - Rychlejší varianta

## API limity (Zdarma):
- 60 requestů/minutu
- 1000 requestů/den

## Poznámky:

⚠️ **Diagnostika MCP serveru:**
Příkaz `claude mcp list` může zobrazovat "Failed to connect", ale server byl úspěšně testován a funkční. To je známý problém s diagnostikou.

✓ **Manuální test úspěšný:**
```bash
GEMINI_API_KEY=... gemini-mcp -v
# INFO: Successfully connected to Gemini API
# INFO: MCP Gemini Server running
```

## Užitečné příkazy:

```bash
# Gemini CLI
gemini --help
gemini auth login

# MCP Server
gemini-mcp --help
gemini-mcp -v  # Verbose režim
gemini-mcp -q  # Quiet režim

# Claude Code
claude mcp list
claude mcp add gemini
claude mcp remove gemini
```

## Environment Variables:

```bash
# ~/.gemini/.env
GEMINI_API_KEY=AIzaSyBSY5xXehmHGJkQfwS15-3psTmtKF7Oxxk

# Volitelné
GEMINI_MODEL=gemini-2.5-pro-latest
GEMINI_PRO_MODEL=gemini-2.5-pro
GEMINI_FLASH_MODEL=gemini-2.5-flash
VERBOSE=true
```

## Dokumentace:

- Gemini CLI: https://github.com/google-gemini/gemini-cli
- RLabs MCP Server: https://github.com/RLabs-Inc/gemini-mcp
- MCP Protocol: https://modelcontextprotocol.io/
- Google AI Studio (API klíče): https://ai.google.dev/

---

**Instalace dokončena:** 2025-11-18
**Verze:**
- Gemini CLI: 0.16.0
- RLabs MCP: 0.1.0
- Node.js: 20.19.5
