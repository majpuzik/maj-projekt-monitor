# 🚀 Coding CLI Nástroje - Kompletní Průvodce

## 📋 Tvoje Možnosti (od nejlevnějších)

### 1️⃣ **Claude-Ollama** (ZDARMA) ⭐⭐⭐⭐⭐
```bash
# Základní použití
co                     # Interactive mode
co "naprogramuj fibonacci"

# Různé modely
co-32b                 # Qwen Coder 32B (nejlepší)
co-70b                 # Llama 3.3 70B (pomalejší, ale chytřejší)
co-deepseek            # DeepSeek Coder 33B
```

**Výhody:**
- ✅ Zcela ZDARMA
- ✅ Rychlé (lokální)
- ✅ Offline funguje
- ✅ Přístup ke všem souborům

**Nevýhody:**
- ❌ Horší než Claude Sonnet 4
- ❌ Vyžaduje GPU (máš ✅)

---

### 2️⃣ **Continue.dev** (VS Code Extension)

Instalace:
```bash
# 1. Otevři VS Code
# 2. Extensions → hledej "Continue"
# 3. Nainstaluj

# 4. Konfigurace (~/.continue/config.json):
{
  "models": [
    {
      "title": "Qwen Coder 32B",
      "provider": "ollama",
      "model": "qwen2.5-coder:32b"
    }
  ]
}
```

**Funkce:**
- 💬 Chat v editoru (Ctrl+L)
- ⚡ Autocomplete (Tab)
- 📝 Edit mode (Ctrl+I)
- 🔍 Hledání v codebase

---

### 3️⃣ **Gemini API** (LEVNÉ kredity)

Máš už API klíč! Gemini je **50x levnější** než Claude:

```bash
# Instalace
pip install google-generativeai

# Použití
export GEMINI_API_KEY="AIzaSyBu32DiGnro7gFrtd540EAJVrZN6jFQ4Bo"

# V Pythonu
import google.generativeai as genai
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')
response = model.generate_content("naprogramuj quicksort")
```

**Ceny:**
- Gemini 2.0 Flash: $0.10 / 1M tokenů (input)
- Claude Sonnet 4: $3.00 / 1M tokenů
- **= 30x levnější!**

---

### 4️⃣ **OpenRouter** (Aggregátor API)

https://openrouter.ai
- Přístup ke všem modelům (Claude, GPT, Llama...)
- Levnější než přímé API
- Platíš jen co použiješ

---

## 🎯 DOPORUČENÁ STRATEGIE

```
┌─────────────────────────────────────────┐
│  DENNÍ WORK FLOW                        │
├─────────────────────────────────────────┤
│                                         │
│  1. Běžné úkoly (70%)                   │
│     → claude-ollama qwen2.5-coder:32b   │
│     → ZDARMA                            │
│                                         │
│  2. Složitější debug (20%)              │
│     → Continue.dev + Ollama             │
│     → ZDARMA                            │
│                                         │
│  3. Opravdu těžké problémy (10%)        │
│     → claude.ai/code                    │
│     → Promo kredity ($850)              │
│                                         │
└─────────────────────────────────────────┘
```

---

## 💰 Srovnání Nákladů (10h denně)

| Nástroj | Měsíční náklady (200h) |
|---------|------------------------|
| **Ollama (local)** | $0 |
| **Gemini Flash** | ~$5 |
| **Claude API** | ~$200-300 |
| **Claude Subscription** | Týdenní limit (vyčerpáno) |

---

## 🔧 Další Užitečné Nástroje

### **Aider** (až bude fungovat s Python 3.11)
```bash
# Vytvoř conda env s Python 3.11
conda create -n aider python=3.11
conda activate aider
pip install aider-chat

# Použití s Ollama
aider --model ollama/qwen2.5-coder:32b
```

### **TabNine** (VS Code autocomplete)
- Bezplatný tier
- AI autocomplete
- Funguje offline s lokálními modely

### **GitHub Copilot** (placené)
- $10/měsíc
- Skvělé autocomplete
- Ale dražší než Ollama ZDARMA

---

## 📝 Příklady Použití

### Quick debugging
```bash
# Najdi bug v souboru
co "Zkontroluj bugs v: $(cat my_script.py)"

# Vysvětli kód
code-explain "$(cat complex_function.js)"

# Optimalizuj
code-optimize "$(cat slow_algorithm.py)"
```

### Interaktivní session
```bash
co

You: Potřebuji napsat FastAPI endpoint pro upload souborů
AI: [odpověď...]

You: /read api/routes.py
AI: [zobrazí soubor...]

You: Přidej to do tohoto souboru
AI: [návod...]
```

---

## ✅ Co Dělat TEĎ

1. **Aktivuj aliasy**
   ```bash
   source ~/.bashrc
   ```

2. **Vyzkoušej claude-ollama**
   ```bash
   co "ahoj, jak funguje quicksort?"
   ```

3. **Nainstaluj Continue.dev** (VS Code)
   - Extensions → Continue
   - Nastav Ollama backend

4. **Strategicky používej kredity**
   - Ollama pro 90% práce
   - Claude.ai/code jen pro těžké úkoly

---

## 🆘 Řešení Problémů

### Model je pomalý
```bash
# Použij menší model
co qwen2.5-coder:7b "prompt"

# Nebo rychlejší
co llama3.2:3b "prompt"
```

### Chci lepší kvalitu
```bash
# Největší model (42GB RAM potřeba)
co llama3.3:70b "složitý problém"
```

### Offline fungování
```bash
# Všechno funguje offline (Ollama)
# Jen claude.ai/code potřebuje internet
```

---

Vytvořeno: $(date +%Y-%m-%d)
