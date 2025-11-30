# Rychlý start LM Studio

**LM Studio verze:** 0.3.31 (ARM64)
**Systém:** DGX Spark GB10
**Speciální optimalizace:** CUDA 13.0 pro DGX Spark

---

## 🚀 Spuštění LM Studio

### 1. Základní spuštění GUI
```bash
~/LMStudio-0.3.31-arm64.AppImage
```

### 2. Vytvoření symlinku (pro pohodlí)
```bash
sudo ln -s ~/LMStudio-0.3.31-arm64.AppImage /usr/local/bin/lms
# Pak můžete spustit jen:
lms
```

---

## 📥 Stažení prvních modelů

### Doporučené modely pro DGX Spark (128GB RAM):

#### **Pro rychlé testování:**
- **Qwen/Qwen2.5-7B** (7B parametrů, ~4-8 GB)
- **mistralai/Mistral-7B-v0.1** (7B parametrů, ~4-8 GB)

#### **Pro pokročilou práci:**
- **meta-llama/Llama-3.2-8B** (8B parametrů, ~5-10 GB)
- **Qwen/Qwen3-Coder-14B** (14B parametrů, ~8-16 GB)

#### **Velké modely (využijete 128GB RAM!):**
- **meta-llama/Llama-3-70B** (70B parametrů, ~40-80 GB)
- **Qwen/Qwen2.5-72B** (72B parametrů, ~40-80 GB)

### V GUI:
1. Kliknout na "🔍 Discover" nebo "📥 Download models"
2. Vyhledat model (např. "Qwen 7B")
3. Vybrat kvantizaci:
   - **Q4_K_M** - dobrý poměr velikost/kvalita (doporučeno)
   - **Q5_K_M** - lepší kvalita, větší soubor
   - **Q8_0** - téměř plná kvalita
4. Kliknout na "Download"

---

## 🌐 Spuštění jako LLM Server

### V GUI:
1. Načíst model (klik na model → "Load")
2. Přejít na "Developer" tab
3. Zaškrtnout "✅ Serve on Local Network"
4. Server poběží na `http://localhost:1234`

### Test serveru:
```bash
# Ověřit, že server běží
curl http://localhost:1234/v1/models

# Test chat completion
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🔗 OpenAI-kompatibilní API

LM Studio poskytuje OpenAI-kompatibilní API endpoint:

### Python příklad:
```python
from openai import OpenAI

# Připojit se k LM Studio serveru
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

# Chat completion
response = client.chat.completions.create(
    model="local-model",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ]
)

print(response.choices[0].message.content)
```

### Node.js/JavaScript příklad:
```javascript
const OpenAI = require('openai');

const client = new OpenAI({
  baseURL: 'http://localhost:1234/v1',
  apiKey: 'not-needed'
});

const response = await client.chat.completions.create({
  model: 'local-model',
  messages: [
    { role: 'user', content: 'Hello!' }
  ]
});

console.log(response.choices[0].message.content);
```

---

## 📦 Import vlastních GGUF modelů

Pokud máte GGUF soubory z jiných zdrojů:

1. **V GUI:** Model → Import → vybrat .gguf soubor
2. **Nebo zkopírovat do:** `~/.cache/lm-studio/models/`

### Sdílení modelů mezi Ollama a LM Studio:

**Z Ollama do LM Studio:**
```bash
# Najít Ollama model
ls ~/.ollama/models/blobs/

# Import do LM Studio (v GUI): Model → Import
```

**Z LM Studio do Ollama:**
```bash
# Najít LM Studio model
ls ~/.cache/lm-studio/models/

# Vytvořit Modelfile pro Ollama
cat > Modelfile <<EOF
FROM /cesta/k/modelu.gguf
PARAMETER temperature 0.7
EOF

# Vytvořit Ollama model
ollama create muj-model -f Modelfile
```

---

## ⚙️ Pokročilé nastavení

### GPU Acceleration (CUDA)
LM Studio automaticky detekuje NVIDIA GPU a používá CUDA 13.0.

**Ověření GPU:**
- V GUI: Settings → Hardware
- Měli byste vidět: "NVIDIA GB10"

### Úspora paměti
Pokud narazíte na problémy s pamětí (Unified Memory Architecture):
```bash
# Mimo LM Studio - vyčistit cache
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
```

### Remote Access
Pro přístup z jiných zařízení v síti:
1. GUI → Developer → "Serve on Local Network"
2. Server bude přístupný na: `http://<IP-adresa-sparku>:1234`

Zjistit IP adresu:
```bash
hostname -I | awk '{print $1}'
```

---

## 🆚 LM Studio vs Ollama

| Vlastnost | Ollama | LM Studio |
|-----------|--------|-----------|
| **Interface** | CLI | GUI + CLI |
| **Port** | 11434 | 1234 |
| **Model browser** | ❌ | ✅ (prohlížet HuggingFace) |
| **API** | REST | OpenAI-compatible |
| **Stejný engine** | ✅ llama.cpp | ✅ llama.cpp |
| **GGUF soubory** | ✅ | ✅ |

**Můžete provozovat OBA současně!**

---

## 🐛 Troubleshooting

### GUI se nespustí
```bash
# Zkontrolovat, zda je soubor executable
chmod +x ~/LMStudio-0.3.31-arm64.AppImage

# Zkontrolovat závislosti
ldd ~/LMStudio-0.3.31-arm64.AppImage
```

### Model se nenačte
- Zkontrolovat volnou paměť: `free -h`
- Vybrat menší kvantizaci (Q4_K_M místo Q8_0)

### Server nereaguje
```bash
# Zkontrolovat, zda server běží
curl http://localhost:1234/v1/models

# Zkontrolovat port
netstat -tulpn | grep 1234
```

---

## 📚 Další zdroje

- **Oficiální docs:** https://lmstudio.ai/docs/app
- **DGX Spark blog post:** https://lmstudio.ai/blog/dgx-spark
- **GitHub issues:** https://github.com/lmstudio-ai/lmstudio-bug-tracker
- **Discord:** https://discord.gg/lmstudio

---

**Užijte si lokální LLM na DGX Spark!** 🚀
