# DGX Spark - Nainstalované aplikace a použití

## ✅ Co je nainstalováno

### 1. NGC CLI (4.9.17)
**Použití:**
```bash
ngc registry image list          # Seznam kontejnerů
ngc registry model list          # Seznam modelů  
ngc config current               # Aktuální konfigurace
```

### 2. NIM Llama 3.1 8B
**Port:** 8000
**Test:**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "meta/llama-3.1-8b-instruct", 
       "messages": [{"role":"user", "content":"Hello!"}],
       "max_tokens": 100}'
```

### 3. Ollama
**Port:** 11434
**Stažení modelu:**
```bash
docker exec -it ollama ollama pull llama3.1:8b
docker exec -it ollama ollama pull mistral
```

### 4. Open WebUI  
**URL:** http://localhost:3000
- Grafické rozhraní pro chat s modely
- Připojeno k Ollama

### 5. DGX Dashboard
**URL:** http://localhost:11000  
- System monitoring
- JupyterLab přístup

## 🚀 Rychlý start

### Použít NIM přes API:
```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="meta/llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Write a haiku"}]
)
print(response.choices[0].message.content)
```

### Použít Ollama:
```bash
docker exec -it ollama ollama run llama3.1:8b "Hello!"
```

### Použít Open WebUI:
1. Otevřít http://localhost:3000 v prohlížeči
2. Vytvořit účet (první uživatel je admin)
3. Vybrat model a chatovat

## 📊 Monitorování

### Kontrola běžících kontejnerů:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### GPU využití:
```bash
nvidia-smi
watch -n 1 nvidia-smi  # Realtime monitoring
```

### Logy kontejneru:
```bash
docker logs nim-llama-8b
docker logs ollama
docker logs open-webui
```

## 🔧 Správa

### Restart služeb:
```bash
docker restart nim-llama-8b
docker restart ollama
docker restart open-webui
```

### Zastavit vše:
```bash
docker stop nim-llama-8b ollama open-webui
```

## 📚 Užitečné odkazy

- NGC Catalog: https://catalog.ngc.nvidia.com
- NIM Docs: https://docs.nvidia.com/nim
- Ollama Models: https://ollama.com/library
- DGX Spark Docs: https://docs.nvidia.com/dgx/dgx-spark
- Build Playbooks: https://build.nvidia.com/spark

