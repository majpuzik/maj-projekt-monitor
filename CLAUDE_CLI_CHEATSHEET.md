# 🚀 Claude CLI - Quick Reference

## 🎯 Tvoje Možnosti

| Příkaz | Použití | Cena | Rychlost |
|--------|---------|------|----------|
| `~/.local/bin/claude-ollama` | Lokální coding | **ZDARMA** | ⚡⚡⚡ |
| `claude` | Originální CLI | Týdenní limit ❌ | ⚡⚡⚡⚡ |
| `claude.ai/code` | Web interface | $850 kreditů ✅ | ⚡⚡⚡ |

---

## ⚡ Rychlé Příkazy

### Claude-Ollama (ZDARMA)
```bash
# Nejrychlejší cesta
~/.local/bin/claude-ollama "napiš quicksort v pythonu"

# Po aktivaci (source ~/.bashrc):
co "prompt"                # qwen2.5-coder:32b (výchozí)
co-32b "prompt"           # Qwen 32B (nejlepší)
co-70b "prompt"           # Llama 70B (pomalý, chytřejší)
co-deepseek "prompt"      # DeepSeek 33B (debugging)
```

### Helper Funkce
```bash
code-explain "$(cat script.py)"
code-fix "můj buggy kód"
code-optimize "pomalý algoritmus"
```

### Interaktivní Režim
```bash
co

You: naprogramuj REST API v FastAPI
AI: [odpověď...]

You: /files
# Zobrazí soubory

You: /read api.py
# Přečte soubor

You: /exit
# Ukončí
```

---

## 📊 Porovnání Modelů

### Pro Coding:
```
🥇 qwen2.5-coder:32b    → Nejlepší pro Python/JS/TS
🥈 deepseek-coder:33b   → Skvělý na debugging
🥉 codellama:70b        → Dobrý na dokumentaci
🏅 llama3.3:70b         → Univerzální (ale pomalý)
```

### Pro Rychlost:
```
⚡⚡⚡ qwen2.5-coder:7b   → Nejrychlejší
⚡⚡  qwen2.5-coder:32b  → Optimální
⚡   llama3.3:70b        → Pomalý
```

---

## 💡 Best Practices

### Denní Workflow (10h)
```
┌────────────────────────────────────────┐
│  1. Debug kódu (40%)                   │
│     → co-deepseek                      │
│                                        │
│  2. Nové funkce (40%)                  │
│     → co-32b                           │
│                                        │
│  3. Code review (10%)                  │
│     → co-70b                           │
│                                        │
│  4. Složité architektury (10%)         │
│     → claude.ai/code ($850)            │
└────────────────────────────────────────┘
```

### Optimalizace Nákladů
```bash
# ŠPATNĚ (drahé):
claude -p "simple task"  # Spotřebuje kredit

# DOBŘE (zdarma):
co "simple task"         # Lokální, ZDARMA
```

---

## 🔧 Problémy a Řešení

### Model je pomalý
```bash
# Přepni na menší model
co qwen2.5-coder:7b "prompt"
```

### Chci lepší kvalitu
```bash
# Použij největší model
co llama3.3:70b "složitý problém"
```

### Ollama neběží
```bash
# Start Ollama
systemctl --user start ollama

# Ověř
ollama list
```

### Bashrc nefunguje
```bash
# Reload
source ~/.bashrc

# Nebo restart shell
exec bash
```

---

## 📚 Dokumentace

| Soubor | Obsah |
|--------|-------|
| `~/CODING_CLI_NAVOD.md` | Kompletní průvodce |
| `~/CLAUDE_PREPINAC_NAVOD.md` | Přepínání abo/API |
| `~/.claude/memory/coding-cli.md` | Memory poznámky |

---

## ⚙️ Konfigurace

### Soubory:
```
~/.local/bin/claude-ollama          # Hlavní wrapper
~/.local/bin/claude-api-wrapper     # API kredity wrapper
~/.bashrc                           # Aliasy a funkce
```

### Aktivace:
```bash
source ~/.bashrc
```

---

## 🎓 Příklady

### Debug Python skriptu
```bash
co-deepseek "Zkontroluj chyby: $(cat script.py)"
```

### Vysvětli složitý kód
```bash
code-explain "$(cat complex_algorithm.js)"
```

### Optimalizuj algoritmus
```bash
code-optimize "$(cat slow_function.py)"
```

### Nový feature
```bash
co "Napiš FastAPI endpoint pro upload souborů s validací"
```

### Interaktivní debug session
```bash
co

You: Mám problém s async/await v Pythonu
AI: [vysvětlení...]

You: Ukaž příklad
AI: [kód...]

You: Jak to testovat?
AI: [testing guide...]
```

---

Vytvořeno: 2025-11-19
Poslední update: $(date +%Y-%m-%d)
