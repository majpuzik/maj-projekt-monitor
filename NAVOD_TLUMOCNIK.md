# 🎤 Živý oboustranný tlumočník - Návod

## ⚡ RYCHLÝ START

### 🏠 Pokud jste NA STEJNÉM počítači, kde běží aplikace:

```
http://localhost:5003
```
→ **Mikrofon bude fungovat!** ✅

---

### 🌐 Pokud přistupujete z JINÉHO počítače:

**MOŽNOST 1: Nahrát audio soubor**
```
1. Otevřete: http://192.168.10.200:5003
2. Použijte tlačítko "📁 Nahrát soubor"
3. Vyberte nahrané audio
```
→ **Funguje i přes HTTP** ✅

**MOŽNOST 2: SSH tunel**
```bash
# Na vašem počítači spusťte:
ssh -L 5003:localhost:5003 puzik@192.168.10.200

# Pak otevřete:
http://localhost:5003
```
→ **Mikrofon bude fungovat!** ✅

---

## 📋 Jak používat:

1. **Vyberte směr překladu** (např. 🇨🇿 → 🇬🇧)
2. **Klikněte na tlačítko:**
   - 🎤 Nahrát z mikrofonu (jen přes localhost/HTTPS)
   - 📁 Nahrát soubor (funguje vždy)
3. **Mluvte nebo nahrajte audio**
4. **Slyšíte překlad**
5. **Přepněte směr** a pokračujte v konverzaci!

---

## 🔄 Podporované směry:

- 🇨🇿 ↔ 🇬🇧 Čeština ↔ Angličtina
- 🇨🇿 ↔ 🇩🇪 Čeština ↔ Němčina
- 🇨🇿 ↔ 🇸🇰 Čeština ↔ Slovenština

---

## ❓ Časté problémy:

**"Chyba přístupu k mikrofonu"**
→ Používejte localhost nebo nahrajte soubor

**"Překlad trvá dlouho"**
→ Normální, Ollama potřebuje čas na překlad

**"Audio se nepřehraje"**
→ Zkontrolujte, zda máte povolené automatické přehrávání v prohlížeči

---

📝 **Pro HTTPS verzi kontaktujte správce**
