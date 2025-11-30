# 🎤 Jak používat hlasový překladač

## 📌 Máte DVĚ možnosti:

---

## 🌐 **1. WEBOVÉ ROZHRANÍ (Nejjednodušší)**

### Samostatný překladač s webovým rozhraním:
```bash
# Spustit (pokud neběží):
cd ~/voice_translator && python3 translator_api.py &

# Otevřít v prohlížeči:
http://192.168.10.200:5002
```

### Co můžete dělat:
- ✅ Nahrát audio soubor (WAV, MP3, OGG)
- ✅ Nahrát přímo z mikrofonu
- ✅ Vybrat cílový jazyk (EN/DE/SK)
- ✅ Stáhnout přeložené audio

---

## 💬 **2. ALQUIST CHATBOT (Konverzační rozhraní)**

### Spuštění Alquist:
```bash
# Zkontrolovat, jestli běží:
docker ps | grep alquist

# Pokud NE, spustit:
docker run -d \
  -v /home/puzik/alquist/bots:/alquist/bots \
  -p 5001:5000 \
  --name alquist \
  alquist
```

### Test přes API:
```bash
# 1. Inicializace
curl -X POST http://192.168.10.200:5001/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "",
    "state": "init",
    "context": {},
    "session": "moje_session",
    "bot": "voice_translator",
    "payload": {}
  }'

# 2. Výběr jazyka (zkopírovat state a context z odpovědi výše)
curl -X POST http://192.168.10.200:5001/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "🇬🇧 Angličtina",
    "state": "NAHRADIT_STATE_Z_ODPOVEDI",
    "context": {},
    "session": "moje_session",
    "bot": "voice_translator",
    "payload": {"button": "set_english"}
  }'

# 3. Překlad textu
curl -X POST http://192.168.10.200:5001/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Dobrý den, jak se máte?",
    "state": "NAHRADIT_STATE_Z_ODPOVEDI",
    "context": {"target_lang": "en", "lang_name": "angličtinu"},
    "session": "moje_session",
    "bot": "voice_translator",
    "payload": {}
  }'
```

---

## 🔧 **Řešení problémů**

### Alquist nereaguje:
```bash
# Zkontrolovat logy:
docker logs alquist

# Restartovat:
docker restart alquist
```

### Standalone API nefunguje:
```bash
# Zkontrolovat, jestli běží:
ps aux | grep translator_api

# Spustit znovu:
cd ~/voice_translator && python3 translator_api.py &
```

### Ollama model chybí:
```bash
# Nainstalovat qwen2.5:14b:
ollama pull qwen2.5:14b
```

---

## 📊 **Podporované jazyky**

- 🇨🇿 **Zdrojový jazyk:** Čeština
- 🇬🇧 **Cílové jazyky:** Angličtina
- 🇩🇪 Němčina
- 🇸🇰 Slovenština

---

## ⚡ **Rychlý start**

Pro nejrychlejší použití:
```bash
# 1. Otevřít prohlížeč na:
http://192.168.10.200:5002

# 2. Nahrát audio nebo nahrát z mikrofonu
# 3. Vybrat cílový jazyk
# 4. Kliknout "Přeložit"
# 5. Stáhnout přeložené audio
```

---

📝 **Vytvořeno pomocí Claude Code**
