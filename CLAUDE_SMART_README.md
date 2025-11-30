# Claude Smart Wrapper 🤖

**Automatický fallback na lokální Ollama při problémech s Claude API**

## ✨ Features

- 🔄 **Automatická detekce** Claude API dostupnosti
- 🚀 **Instant fallback** na lokální Ollama při výpadku
- 💻 **Plnohodnotný code assistant** s Ollama modely
- ⚡ **Rychlé aliasy** pro časté operace
- 🎯 **Interaktivní režim** s příkazy jako v Claude

---

## 🚀 Instalace

Vše je již nainstalováno! Jen **reload terminal**:

```bash
source ~/.bashrc
```

---

## 📝 Použití

### 1. Claude Smart Wrapper (místo `claude`)

```bash
# Místo 'claude' použij:
c

# Nebo plný příkaz:
~/claude-smart
```

**Co to dělá:**
1. ✅ Zkontroluje Claude API (5s timeout)
2. ✅ Pokud OK → spustí normální Claude Code
3. ❌ Pokud FAIL → automaticky spustí Ollama assistant

### 2. Ollama Assistant (přímý přístup)

```bash
# Interaktivní režim
ollama-code
# nebo
oc

# Přímo review souboru
code-review file.py

# Navrhni opravu
code-fix buggy.js

# Vysvětli kód
code-explain complex.cpp
```

---

## 🎯 Ollama Assistant - Příkazy

### Interaktivní režim:

```bash
ollama> /review src/app.py          # Review souboru
ollama> /fix tests/broken.js        # Navrhni opravu
ollama> /explain lib/utils.go       # Vysvětli kód
ollama> /model qwen2.5-coder:7b     # Změň model (rychlejší)
ollama> jak optimalizovat SQL query? # Zeptej se

ollama> /exit                        # Ukončit
```

### CLI režim (bez interakce):

```bash
# Review
~/ollama-assistant --review src/main.py

# Fix
~/ollama-assistant --fix buggy.js

# Explain
~/ollama-assistant --explain api.go

# Ask
~/ollama-assistant --ask "jak napsat rekurzivní funkci?"

# Změna modelu
~/ollama-assistant --model codellama:70b --review src/app.py
```

---

## ⚙️ Konfigurace

Edituj `~/.claude-smart.conf`:

```bash
nano ~/.claude-smart.conf
```

### Doporučené modely podle úkolu:

| Úkol | Model | Velikost | Rychlost |
|------|-------|----------|----------|
| **Coding (nejlepší)** | `qwen2.5-coder:32b` | 19 GB | Střední |
| **Coding (rychlý)** | `qwen2.5-coder:7b` | 4.7 GB | ⚡ Rychlý |
| **Coding (beast)** | `deepseek-coder-v2:236b` | 132 GB | 🐌 Pomalý |
| **Chat/Debug** | `qwen2.5:72b` | 47 GB | Střední |
| **Univerzální** | `llama3.3:70b` | 42 GB | Střední |

### Změna modelu:

```bash
# V configu
OLLAMA_MODEL="qwen2.5-coder:7b"

# Nebo přímo v příkazu
~/ollama-assistant --model codellama:13b
```

---

## 🔧 Scénáře použití

### 1. Claude padla během práce

```bash
$ claude
# ❌ Claude API není dostupná, přepínám na Ollama...

ollama> /review src/app.py
# ✓ Funguje!
```

### 2. Claude je moc pomalá

```bash
# Přepni na rychlý lokální model
$ oc
ollama> /model qwen2.5-coder:7b
ollama> vysvětli mi asyncio v pythonu
# ⚡ Okamžitá odpověď
```

### 3. Rychlý code review bez čekání

```bash
$ code-review src/auth.py
# Review za 5 sekund místo 30s s Claude API
```

### 4. Offline coding

```bash
# Funguje i bez internetu!
$ oc
ollama> jak napsat webserver v Go?
# ✓ Lokální model, žádný internet
```

---

## 🎨 Příklady

### Review pull requestu:

```bash
$ git diff main > changes.diff
$ ollama-code
ollama> /review changes.diff
```

### Ladění bugu:

```bash
$ code-fix src/buggy-function.js
# Navrhne opravu + vysvětlení
```

### Learning nového frameworku:

```bash
$ oc
ollama> jak začít s FastAPI?
ollama> ukaž příklad REST API
ollama> jak přidat autentizaci?
```

---

## 🚨 Troubleshooting

### Ollama není dostupná

```bash
# Spusť Ollama server
ollama serve

# Nebo jako systemd service
sudo systemctl start ollama
```

### Model není nainstalován

```bash
# Stáhni model
ollama pull qwen2.5-coder:32b

# Seznam dostupných modelů
ollama list
```

### Claude wrapper nefunguje

```bash
# Zkontroluj konfiguraci
cat ~/.claude-smart.conf

# Test Claude API
curl -I https://api.anthropic.com

# Test Ollama
curl http://localhost:11434/api/tags
```

---

## 📊 Porovnání

| Feature | Claude API | Ollama (local) |
|---------|-----------|----------------|
| **Rychlost** | 5-30s | 1-5s |
| **Dostupnost** | Závisí na internetu | Vždy |
| **Cena** | Platba per token | Zdarma |
| **Kvalita** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Privacy** | Data jdou ven | 100% lokální |

---

## 🎯 Best Practices

1. **Pro produkční kód** → používej Claude (lepší kvalita)
2. **Pro rychlé otázky** → používej Ollama (rychlejší)
3. **Pro citlivý kód** → používej Ollama (privacy)
4. **Když Claude padne** → automatický fallback na Ollama

---

## 📚 Další příkazy

```bash
# Seznam všech Ollama modelů
ollama list

# Stáhni nový model
ollama pull llama3.3:70b

# Smaž model
ollama rm old-model

# Info o modelu
ollama show qwen2.5-coder:32b
```

---

## 🔄 Aktualizace

```bash
# Aktualizuj Claude Code
npm install -g @anthropic-ai/claude-code

# Aktualizuj Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Aktualizuj modely
ollama pull qwen2.5-coder:32b
```

---

**Vytvořeno:** 2025-11-17
**Verze:** 1.0
**Autor:** MAJ

**Užij si kódování bez obav o výpadky API! 🚀**
