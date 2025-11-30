# 🚀 NVIDIA NIM na DGX Spark - Kompletní návod

**Datum vytvoření:** 14.11.2025
**Systém:** DGX Spark GB10 (ARM64), CUDA 13.0

---

## 📖 Co je NVIDIA NIM?

**NVIDIA NIM (NVIDIA Inference Microservices)** je kontejnerizovaný software pro rychlé a spolehlivé poskytování AI modelů a inference na NVIDIA GPU.

### Výhody NIM:
- ✅ **Production-ready** - optimalizováno pro produkci
- ✅ **GPU-accelerated** - plné využití GB10
- ✅ **OpenAI-compatible API** - snadná integrace
- ✅ **Předkonfigurované** - žádné složité nastavení
- ✅ **ARM64 podpora** - speciální containery pro DGX Spark

---

## 🎯 Dostupné modely pro DGX Spark

### 1. Llama 3.1 8B Instruct
- **Container:** `nvcr.io/nim/meta/llama-3.1-8b-instruct:1.2.4`
- **Velikost:** ~10GB
- **Paměť:** ~16GB GPU RAM
- **Vhodné pro:** Obecné text generation, chat, Q&A

### 2. Qwen3-32B (Spark-optimized)
- **Container:** `nvcr.io/nim/qwen/qwen3-32b-dgx-spark:latest`
- **Velikost:** ~20GB
- **Paměť:** ~40GB GPU RAM
- **Vhodné pro:** Advanced reasoning, multimodal tasks
- **Poznámka:** Speciální verze optimalizovaná pro DGX Spark!

---

## 🔑 Krok 1: Získání NGC API Key

### A) Přejděte na NGC:
```
https://ngc.nvidia.com/
```

### B) Přihlaste se nebo vytvořte účet
- Použijte firemní nebo osobní email
- NVIDIA účet je zdarma

### C) Vygenerujte API Key:
1. Přejděte na: https://ngc.nvidia.com/setup/api-key
2. Klikněte na **"Generate API Key"**
3. Zkopírujte klíč (86 znaků, končí na `==`)

### D) Nastavte jako environment variable:

#### Dočasně (pro aktuální session):
```bash
export NGC_API_KEY=<your_api_key_here>
```

#### Trvale (pro všechny session):
```bash
echo 'export NGC_API_KEY=<your_api_key_here>' >> ~/.bashrc
source ~/.bashrc
```

### E) Ověřte nastavení:
```bash
echo $NGC_API_KEY | grep -E '^[a-zA-Z0-9]{86}=='
```

Měli byste vidět: `✓` (checkmark) pokud je formát správný.

---

## 🚀 Krok 2: Instalace NIM

### Metoda 1: Automatický script (doporučeno)

```bash
# Spustit instalační script
~/setup_nim.sh
```

Script vás provede:
1. Ověřením NGC API key
2. Přihlášením do NGC registry
3. Výběrem modelu (Llama 3.1 8B nebo Qwen3-32B)
4. Stažením a spuštěním NIM containeru

### Metoda 2: Manuální instalace

#### Krok 2.1: Přihlášení do NGC
```bash
echo $NGC_API_KEY | docker login nvcr.io -u '$oauthtoken' --password-stdin
```

#### Krok 2.2: Stažení NIM containeru

**Pro Llama 3.1 8B:**
```bash
docker pull nvcr.io/nim/meta/llama-3.1-8b-instruct:1.2.4
```

**Pro Qwen3-32B (Spark-specific):**
```bash
docker pull nvcr.io/nim/qwen/qwen3-32b-dgx-spark:latest
```

#### Krok 2.3: Vytvoření cache adresáře
```bash
mkdir -p ~/.cache/nim
```

#### Krok 2.4: Spuštění NIM

**Pro Llama 3.1 8B:**
```bash
docker run -d \
  --name nim-llama31-8b \
  --gpus all \
  --shm-size=16GB \
  -e NGC_API_KEY \
  -v ~/.cache/nim:/opt/nim/.cache \
  -p 8000:8000 \
  nvcr.io/nim/meta/llama-3.1-8b-instruct:1.2.4
```

**Pro Qwen3-32B:**
```bash
docker run -d \
  --name nim-qwen3-32b \
  --gpus all \
  --shm-size=16GB \
  -e NGC_API_KEY \
  -v ~/.cache/nim:/opt/nim/.cache \
  -p 8000:8000 \
  nvcr.io/nim/qwen/qwen3-32b-dgx-spark:latest
```

---

## 🧪 Krok 3: Testování NIM

### A) Zkontrolovat, že NIM běží:
```bash
docker ps | grep nim
```

Měli byste vidět běžící container.

### B) Sledovat logy (čekáme na "Server started"):
```bash
docker logs -f nim-llama31-8b   # nebo nim-qwen3-32b
```

Počkejte, dokud neuvidíte:
```
✓ Server started on 0.0.0.0:8000
```

### C) Test API - základní completion:

**Llama 3.1 8B:**
```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta/llama-3.1-8b-instruct",
    "prompt": "Once upon a time",
    "max_tokens": 64,
    "temperature": 0.7
  }'
```

**Qwen3-32B:**
```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen3-32b",
    "prompt": "Once upon a time",
    "max_tokens": 64,
    "temperature": 0.7
  }'
```

### D) Test API - chat completion:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta/llama-3.1-8b-instruct",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "max_tokens": 100
  }'
```

### E) OpenAI Python klient:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-used"  # NIM nepotřebuje API key pro lokální použití
)

response = client.chat.completions.create(
    model="meta/llama-3.1-8b-instruct",
    messages=[
        {"role": "user", "content": "Hello, who are you?"}
    ],
    max_tokens=100
)

print(response.choices[0].message.content)
```

---

## 📊 Monitoring a správa

### Zobrazit běžící NIM:
```bash
docker ps | grep nim
```

### Zobrazit logy:
```bash
docker logs -f nim-llama31-8b   # nebo nim-qwen3-32b
```

### Zkontrolovat GPU využití:
```bash
nvidia-smi
```

### Zkontrolovat využití paměti:
```bash
docker stats nim-llama31-8b   # nebo nim-qwen3-32b
```

### Zastavit NIM:
```bash
docker stop nim-llama31-8b   # nebo nim-qwen3-32b
```

### Spustit znovu:
```bash
docker start nim-llama31-8b   # nebo nim-qwen3-32b
```

### Restartovat NIM:
```bash
docker restart nim-llama31-8b   # nebo nim-qwen3-32b
```

### Odstranit container:
```bash
docker stop nim-llama31-8b
docker rm nim-llama31-8b
```

### Vymazat cache (uvolní disk space):
```bash
rm -rf ~/.cache/nim
```

---

## 🔧 Troubleshooting

### Problém: NIM se nespustí

**Řešení 1:** Zkontrolujte NGC API key
```bash
echo $NGC_API_KEY
```

**Řešení 2:** Zkontrolujte Docker a GPU
```bash
docker run --rm --gpus all nvcr.io/nvidia/cuda:13.0.1-devel-ubuntu24.04 nvidia-smi
```

**Řešení 3:** Zkontrolujte logy
```bash
docker logs nim-llama31-8b
```

### Problém: Port 8000 již používán

**Řešení:** Použijte jiný port
```bash
# Zastavte jiný service na portu 8000, nebo změňte port:
docker run -d \
  --name nim-llama31-8b \
  --gpus all \
  --shm-size=16GB \
  -e NGC_API_KEY \
  -v ~/.cache/nim:/opt/nim/.cache \
  -p 8001:8000 \
  nvcr.io/nim/meta/llama-3.1-8b-instruct:1.2.4

# Pak použijte: http://localhost:8001/v1
```

### Problém: Out of memory

**Řešení:** Použijte menší model nebo zvyšte swap
```bash
# Zkontrolujte paměť
free -h

# Llama 3.1 8B potřebuje ~16GB
# Qwen3-32B potřebuje ~40GB

# Použijte Llama 3.1 8B místo Qwen3-32B
```

### Problém: Slow inference

**Řešení 1:** Zkontrolujte GPU utilization
```bash
nvidia-smi -l 1
```

**Řešení 2:** Zkontrolujte, že neběží jiné GPU procesy
```bash
ps aux | grep -E "python|ollama|lmstudio"
```

---

## 📖 Dokumentace a resources

### Oficiální dokumentace:
- **NIM Release Notes:** https://docs.nvidia.com/nim/large-language-models/1.14.0/release-notes.html
- **NGC Catalog:** https://catalog.ngc.nvidia.com/
- **DGX Spark NGC Guide:** https://docs.nvidia.com/dgx/dgx-spark/ngc.html

### API dokumentace:
- **OpenAI API Spec:** https://platform.openai.com/docs/api-reference
- NIM je kompatibilní s OpenAI API

### Další NIM modely:
Prohlédněte si NGC Catalog pro více modelů:
```bash
# Přihlaste se a prohledejte:
https://catalog.ngc.nvidia.com/orgs/nim
```

---

## 💡 Tipy a triky

### 1. Použití s Ollama a LM Studio současně
NIM používá port 8000, Ollama 11434, LM Studio 41343. Můžete je všechny provozovat zároveň!

### 2. Benchmark performance
```bash
# Nainstalujte vegeta (HTTP load testing)
go install github.com/tsenart/vegeta@latest

# Test throughput
echo "GET http://localhost:8000/v1/models" | vegeta attack -duration=10s -rate=10 | vegeta report
```

### 3. Persistent storage
Cache v `~/.cache/nim` obsahuje stažené modely. Nesmažte, pokud nechcete znovu stahovat!

### 4. Multiple NIM instances
Můžete běžet více NIM současně na různých portech:
```bash
# Llama 3.1 8B na portu 8000
docker run -d --name nim-llama-8000 -p 8000:8000 ...

# Qwen3-32B na portu 8001
docker run -d --name nim-qwen-8001 -p 8001:8000 ...
```

---

## 🎯 Use Cases

### 1. Lokální development
Používejte NIM místo OpenAI API pro testování bez cloudu:
```python
# Změňte pouze base_url
client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
```

### 2. Production inference
NIM je optimalizovaný pro high-throughput inference v produkci.

### 3. Fine-tuned models
Můžete nasadit svoje fine-tuned modely přes NIM (vyžaduje custom build).

---

**Máte NIM připravený k použití!** 🎉

Pro otázky nebo problémy:
- Čtěte dokumentaci: `/home/puzik/START_NIM.md`
- Použijte instalační script: `~/setup_nim.sh`
- Podívejte se na kompletní souhrn: `~/KOMPLETNI_SOUHRN_2025-11-14.md`
