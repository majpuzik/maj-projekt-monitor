# Claude Code - Přepínač Předplatné/API Kredity

## 🎯 Jak to funguje

Vytvořil jsem ti dva režimy pro Claude Code:

### 1. **`claude`** - Předplatné (OAuth) ✅ VÝCHOZÍ
```bash
claude
```
- Používá tvoje **předplatné** přes OAuth
- Neměří kredity, neomezený usage podle plánu

### 2. **`claude-api`** - API Kredity 💳
```bash
claude-api
```
- Používá **API klíč** s kredity
- **Automaticky zobrazuje zůstatek** před a po každém použití
- Volitelně použij jiný klíč:
  - `claude-api --pro` (výchozí: Pro CLI klíč)
  - `claude-api --code` (claude.ai/code klíč)

---

## 📋 Příkazy

### Spustit Claude Code
```bash
# Předplatné (OAuth)
claude

# API kredity (zobrazí zůstatek)
claude-api

# API kredity s konkrétním klíčem
claude-api --code
```

### Zkontrolovat aktuální režim
```bash
claude-status
```

### Rychlé přepnutí (bez startu)
```bash
# Přepni na předplatné
claude-abo

# Přepni na API kredity
claude-kredit
```

---

## 🔧 Technické detaily

### Co se děje na pozadí

**`claude`** (předplatné):
1. Odstraní `ANTHROPIC_API_KEY` z prostředí
2. Spustí `/usr/local/bin/claude` s OAuth
3. Používá tvoje předplatné

**`claude-api`** (API kredity):
1. Nastaví `ANTHROPIC_API_KEY`
2. Volá Anthropic API pro zjištění zůstatku kreditů
3. Spustí Claude Code
4. Po skončení znovu zobrazí zůstatek

### Soubory
- **Wrapper skript**: `~/.local/bin/claude-api-wrapper`
- **Bash funkce**: `~/.bashrc` (na konci)

---

## 💡 Příklady použití

### Jednorázový task na předplatné
```bash
claude -p "vysvětli mi async/await"
```

### Vývoj s API kredity (měření nákladů)
```bash
claude-api
# Zobrazí zůstatek před startem
# ... pracuješ s Claude ...
# Zobrazí zůstatek po ukončení
```

### Zkontrolovat, co právě používám
```bash
claude-status
# 📱 PŘEDPLATNÉ (OAuth)
# nebo
# 💳 API KREDITY (sk-ant-api03-...)
```

---

## 🆘 Řešení problémů

### "Nelze získat zůstatek"
- Zkontroluj API klíč v `~/.local/bin/claude-api-wrapper`
- Ověř, že klíč je platný na https://console.anthropic.com/

### Funkce `claude` nefunguje
```bash
# Reload bashrc
source ~/.bashrc

# Nebo restartni shell
exec bash
```

### Chci změnit API klíče
Uprav soubor: `~/.local/bin/claude-api-wrapper`
```bash
nano ~/.local/bin/claude-api-wrapper
```

---

## 📊 Formát zobrazení zůstatku

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Zjišťuji zůstatek API kreditů...
📊 Zůstatek: 15.42 USD
📉 Spotřeba: 2.13 USD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ✅ Shrnutí

| Příkaz | Režim | Zobrazuje zůstatek? |
|--------|-------|---------------------|
| `claude` | Předplatné (OAuth) | ❌ Ne |
| `claude-api` | API Kredity | ✅ Ano (před + po) |
| `claude-status` | - | Zobrazí aktuální režim |

**Doporučení:**
- Pro běžnou práci: `claude` (neomezené)
- Pro sledování nákladů: `claude-api` (měří kredity)

---

Vytvořeno: $(date +%Y-%m-%d)
