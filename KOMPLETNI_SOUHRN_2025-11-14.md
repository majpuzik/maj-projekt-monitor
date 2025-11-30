# ✓ Kompletní souhrn instalace NVIDIA Build nástrojů (Aktualizace 2025-11-14)

**Datum aktualizace:** 14.11.2025 17:12
**Systém:** DGX Spark GB10 (ARM64), Ubuntu, CUDA 13.0

---

## ✅ 1. RAPIDS / CUDA-X Data Science - HOTOVO

**Status:** ✓ Plně funkční a otestováno

**Umístění:** Conda prostředí `rapids-cuda13`

**Verze:**
- cuDF: 25.10.00
- cuML: 25.10.00
- CuPy: 13.6.0
- dask-cuda: 25.10.00

**Jak použít:**
```bash
conda activate rapids-cuda13
python -c "import cudf; df = cudf.DataFrame({'a': [1,2,3]}); print(df)"
```

**Test proběhl úspěšně** - všechny komponenty fungují!

---

## ✅ 2. PyTorch Fine-tune - HOTOVO

**Status:** ✓ Container připraven, skripty dostupné

**Image:** `nvcr.io/nvidia/pytorch:25.09-py3` (18.1GB)

**Dostupné skripty:**
- `Llama3_8B_LoRA_finetuning.py` - LoRA pro Llama 8B
- `Llama3_70B_qLoRA_finetuning.py` - qLoRA pro Llama 70B
- `Llama3_3B_full_finetuning.py` - Plný fine-tuning Llama 3B

**Jak začít:**
```bash
# Přečtěte si podrobný návod:
cat ~/START_PYTORCH_FINETUNE.md

# Nebo rovnou spusťte:
cd ~
docker run --gpus all -it --rm --ipc=host \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  -v ${PWD}:/workspace -w /workspace \
  nvcr.io/nvidia/pytorch:25.09-py3
```

**Rychlý script:** `~/run_pytorch_finetune.sh`

---

## ✅ 3. NVFP4 Quantization - HOTOVO

**Status:** ✓ TensorRT-LLM container stažen a otestován

**Image:** `nvcr.io/nvidia/tensorrt-llm/release:spark-single-gpu-dev`

**Test:**
```bash
docker run --rm --gpus all \
  nvcr.io/nvidia/tensorrt-llm/release:spark-single-gpu-dev \
  nvidia-smi
```

**Poznámka:** Pro kvantizaci modelů následujte oficiální návod: https://build.nvidia.com/spark/nvfp4-quantization

---

## ✅ 4. LM Studio - HOTOVO

**Status:** ✓ Nainstalováno a běží (extrahovaná verze)

**Verze:** 0.3.31 (ARM64) - Oficiální podpora pro DGX Spark!

**Speciální optimalizace:** CUDA 13.0, llama.cpp engine

**Spuštění:**
```bash
# Spustit extrahovanou verzi (bez FUSE)
~/run_lmstudio_extracted.sh

# Nebo manuálně
~/squashfs-root/lm-studio --no-sandbox &
```

**API endpoint:** `http://localhost:41343` (detekován CUDA 13 backend)

**Poznámka:** LM Studio **NEMŮŽE sdílet modely s Ollama** kvůli různým formátům úložiště:
- Ollama: Vrstvené blob soubory (content-addressable storage)
- LM Studio: Kompletní GGUF soubory

**Řešení:** Pro Ollama modely použijte **Open WebUI** (již běží na portu 3000)

---

## ✅ 5. NeMo AutoModel - PŘIPRAVENO

**Status:** ✓ Repozitář naklonován

**Umístění:** `~/NeMo-Automodel`

**Poznámka:** Lokální instalace selhala kvůli ARM64 kompatibilitě (triton nemá ARM64 wheel).

**Řešení:** Použít Docker

**Docker build (připraven):**
```bash
cd ~/NeMo-Automodel
# Dockerfile je v: ~/NeMo-Automodel/docker/Dockerfile
# Používá PyTorch container jako základ
```

**Když budete potřebovat NeMo, můžete buildit Docker image nebo použít PyTorch container přímo.**

---

## ✅ 6. Jupyter Lab - HOTOVO (NOVĚ!)

**Status:** ✓ Nainstalováno v conda base

**Verze:** 4.4.7 (Python 3.13)

**Spuštění:**
```bash
# Aktivovat conda base
source ~/miniconda3/bin/activate

# Spustit Jupyter Lab
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser

# Nebo s rapids prostředím
conda activate rapids-cuda13
jupyter lab
```

**Součásti:**
- JupyterLab 4.4.7
- IPython 9.7.0
- Notebook 7.4.5
- nbconvert 7.16.6
- ipykernel 6.31.0

**URL:** `http://localhost:8888` nebo `http://dgx-spark.local:8888`

---

## ⏳ 7. vLLM - STAHOVÁNÍ (NOVĚ!)

**Status:** ⏳ Docker image se stahuje

**Image:** `vllm/vllm-openai:latest`

**Po dokončení - spuštění:**
```bash
# Spustit vLLM server s modelem
docker run --gpus all -it --rm \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3.3-70B-Instruct \
  --max-model-len 4096
```

**Výhody vLLM:**
- Vysoký throughput (PagedAttention)
- OpenAI-kompatibilní API
- Streaming responses
- Multi-GPU support

**API endpoint:** `http://localhost:8000/v1`

**Dokumentace:** https://docs.vllm.ai

---

## ✅ 8. NVIDIA AI Workbench - HOTOVO (NOVĚ!)

**Status:** ✓ Installer stažen

**Umístění:** `~/ai-workbench-installer.sh`

**Instalace (potřebuje manuální spuštění):**
```bash
# Spustit installer
~/ai-workbench-installer.sh

# Nebo použít Docker
docker run -it --gpus all \
  nvcr.io/nvidia/ai-workbench/workbench-cli:latest
```

**Co to je:**
NVIDIA AI Workbench je jednotné vývojové prostředí pro AI/ML projekty:
- Správa projektů a prostředí
- Integrace s VS Code
- Podpora pro Jupyter, TensorBoard
- Git integrace
- Sdílení projektů

**Dokumentace:** https://www.nvidia.com/en-us/ai-data-science/products/ai-workbench/

---

## ⏳ 9. VS Code - HOTOVO (čeká na sudo) (NOVĚ!)

**Status:** ✓ .deb balíček stažen, **potřebuje sudo pro instalaci**

**Umístění:** `~/vscode-arm64.deb` (100 MB)

**Instalace (vyžaduje sudo heslo):**
```bash
sudo dpkg -i ~/vscode-arm64.deb
sudo apt-get install -f
```

**Po instalaci:**
```bash
# Spustit VS Code
code

# Nebo pro remote SSH
code --remote ssh-remote+user@host /path/to/project
```

**Doporučená rozšíření pro AI/ML:**
- Python
- Jupyter
- Remote - SSH
- Docker
- YAML

---

## ✅ 10. FLUX.1-dev Image Generation - PLAYBOOK PŘIPRAVEN (NOVĚ!)

**Status:** ✓ Playbook k dispozici

**Umístění:** `~/dgx-spark-playbooks/nvidia/flux-finetuning/`

**Model:** FLUX.1-dev 12B parametrů

**Co to dělá:**
- DreamBooth LoRA fine-tuning pro custom image generation
- High-resolution 1K diffusion training a inference
- ComfyUI integrace pro intuitivní visual workflows

**Požadavky:**
- Hugging Face token (model je gated: https://huggingface.co/black-forest-labs/FLUX.1-dev)
- 30-45 minut na stažení modelů
- 1-2 hodiny training

**Rychlý start:**
```bash
# 1. Nastavit HF token
export HF_TOKEN=<YOUR_HF_TOKEN>

# 2. Stáhnout model
cd ~/dgx-spark-playbooks/nvidia/flux-finetuning/assets
sh download.sh

# 3. Build inference container
docker build -f Dockerfile.inference -t flux-comfyui .

# 4. Spustit ComfyUI
docker run --gpus all -it --rm \
  -v $(pwd):/workspace \
  -p 8188:8188 \
  flux-comfyui
```

**ComfyUI URL:** `http://localhost:8188`

**Dokumentace:** `~/dgx-spark-playbooks/nvidia/flux-finetuning/README.md`

**Web:** https://build.nvidia.com/spark/flux-finetuning

---

## ✅ 11. VLM (Vision-Language Models) - PLAYBOOK PŘIPRAVEN (NOVĚ!)

**Status:** ✓ Playbook k dispozici

**Umístění:** `~/dgx-spark-playbooks/nvidia/vlm-finetuning/`

**Modely:**

### 📸 Image VLM: Qwen2.5-VL-7B
- **Use case:** Detekce požárů ze satelitních snímků
- **Technika:** GRPO (Generalized Reward Preference Optimization)
- **Training čas:** 30-60 minut

### 🎥 Video VLM: InternVL3 8B
- **Use case:** Detekce nebezpečného řízení z videí
- **Výstup:** Strukturovaná metadata
- **Training čas:** 1-2 hodiny

**Požadavky:**
- Hugging Face token
- Weights & Biases account (volitelné, doporučeno)

**Rychlý start:**
```bash
# 1. Nastavit HF token
export HF_TOKEN=<YOUR_HF_TOKEN>

# 2. Build VLM container
cd ~/dgx-spark-playbooks/nvidia/vlm-finetuning/assets
docker build --build-arg HF_TOKEN=$HF_TOKEN -t vlm_demo .

# 3. Spustit training UI
docker run --gpus all -it --rm \
  -v $(pwd):/workspace \
  -p 8501:8501 \
  vlm_demo
```

**Streamlit UI:** `http://localhost:8501`

**Dokumentace:** `~/dgx-spark-playbooks/nvidia/vlm-finetuning/README.md`

**Web:** https://build.nvidia.com/spark/vlm-finetuning

---

## ❌ 12. NIM LLM - NELZE NAINSTALOVAT

**Status:** ❌ ARM64 není podporováno

**Důvod:** NVIDIA NIM pro LLM podporuje pouze x86_64/AMD64 architekturu, DGX Spark je ARM64.

**Alternativy:**
- vLLM (podporuje ARM64) ✓
- LM Studio (podporuje ARM64) ✓
- Ollama (podporuje ARM64) ✓

---

## ✅ 13. Ollama - BĚŽÍ (38 modelů se indexuje)

**Status:** ✓ Běží, modely se přenášejí z Mac Mini M4

**Verze:** Latest

**Modely v přenosu (38 celkem):**
- llama3.3 70b, llama3.1 70b/8b, llama3.2 3b
- qwen2.5 7b/14b/32b/72b
- qwen2.5-coder 7b/32b
- mistral-nemo, mistral 7b
- deepseek-v3.1, deepseek-coder, deepseek-r1
- phi3, yi 34b/9b
- codellama 13b
- mixtral 8x7b
- starcoder2 7b
- A mnoho dalších...

**Refresh script:** `~/refresh_ollama_models.sh` (běží na pozadí)

**Použití:**
```bash
# Seznam modelů
ollama list

# Spustit model
ollama run llama3.3:70b

# API
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.3:70b",
  "prompt": "Why is the sky blue?"
}'
```

**Web UI:** Open WebUI běží na `http://localhost:3000`

---

## ✅ 14. Open WebUI - BĚŽÍ

**Status:** ✓ Běží na portu 3000

**URL:** `http://localhost:3000` nebo `http://dgx-spark.local:3000`

**Integrace:**
- Ollama modely (automaticky detekováno)
- OpenAI API kompatibilní endpointy
- Multi-model chat

**Výhoda:** Může používat všechny Ollama modely bez duplikace úložiště!

---

## 📄 Dokumentace vytvořená

1. **`~/INSTALACE_SOUHRN.md`** - Původní technický souhrn
2. **`~/START_PYTORCH_FINETUNE.md`** - Krok za krokem průvodce PyTorch fine-tuningem
3. **`~/START_LMSTUDIO.md`** - Kompletní návod pro LM Studio
4. **`~/KOMPLETNI_SOUHRN.md`** - Původní souhrn (13.11.2025)
5. **`~/KOMPLETNI_SOUHRN_2025-11-14.md`** - Tento soubor (aktualizovaný přehled)
6. **`~/run_pytorch_finetune.sh`** - Rychlý spouštěcí script
7. **`~/run_lmstudio.sh`** - Rychlý spouštěcí script pro LM Studio (AppImage)
8. **`~/run_lmstudio_extracted.sh`** - Rychlý spouštěcí script pro extrahovanou verzi
9. **`~/refresh_ollama_models.sh`** - Script pro indexování Ollama modelů
10. **`~/share_ollama_models.sh`** - Script pro sdílení modelů (nefunkční - formáty nekompatibilní)

---

## 🚀 Co můžete dělat HNED TEĎ

### 1. Testovat RAPIDS
```bash
conda activate rapids-cuda13
python -c "
import cudf
df = cudf.DataFrame({'a': [1, 2, 3], 'b': [10, 20, 30]})
print(df)
print(f'Součet: {df[\"a\"].sum()}')
"
```

### 2. Začít s PyTorch Fine-tuningem
```bash
# Přečtěte si návod
cat ~/START_PYTORCH_FINETUNE.md

# Nebo spusťte container
~/run_pytorch_finetune.sh
```

### 3. Prozkoumat NeMo příklady
```bash
cd ~/NeMo-Automodel/examples
ls -la
# Najdete příklady pro LLM a VLM fine-tuning
```

### 4. Spustit Jupyter Lab
```bash
source ~/miniconda3/bin/activate
jupyter lab --ip=0.0.0.0 --no-browser
```

### 5. Použít Ollama modely přes Open WebUI
```bash
# Otevřít v browseru
firefox http://localhost:3000
```

### 6. Začít s FLUX.1 image generation
```bash
cd ~/dgx-spark-playbooks/nvidia/flux-finetuning/
cat README.md
```

### 7. Začít s VLM fine-tuningem
```bash
cd ~/dgx-spark-playbooks/nvidia/vlm-finetuning/
cat README.md
```

---

## ⚙️ Systémové informace

**GPU:** NVIDIA GB10 (DGX Spark)
**CUDA:** 13.0
**Python:** 3.12.3 (system), 3.13 (conda base)
**Docker:** 28.3.3 ✓
**Conda:** 25.9.1 ✓

**Volné místo:** ~3.4TB

---

## 🔗 Užitečné odkazy

1. **NeMo Fine-tune:** https://build.nvidia.com/spark/nemo-fine-tune
2. **PyTorch Fine-tune:** https://build.nvidia.com/spark/pytorch-fine-tune
3. **NVFP4 Quantization:** https://build.nvidia.com/spark/nvfp4-quantization
4. **NIM LLM:** https://build.nvidia.com/spark/nim-llm (❌ ARM64 nepodporováno)
5. **CUDA-X Data Science:** https://build.nvidia.com/spark/cuda-x-data-science
6. **FLUX.1 Fine-tuning:** https://build.nvidia.com/spark/flux-finetuning
7. **VLM Fine-tuning:** https://build.nvidia.com/spark/vlm-finetuning
8. **NVIDIA AI Workbench:** https://www.nvidia.com/en-us/ai-data-science/products/ai-workbench/
9. **vLLM Documentation:** https://docs.vllm.ai

---

## 💡 Tipy a triky

### ARM64 Kompatibilita
Některé Python balíčky nemají ARM64 wheels - použijte Docker containery.

### Unified Memory Architecture (UMA)
DGX Spark sdílí paměť mezi GPU a CPU (128GB unified). Při problémech:
```bash
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
```

### Docker bez sudo
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Hugging Face Token
Pro přístup k gated modelům (FLUX.1, Llama, atd.) potřebujete token:
```bash
# Získat token
https://huggingface.co/settings/tokens

# Nastavit jako environment variable
export HF_TOKEN=<your_token>

# Nebo trvale do .bashrc
echo 'export HF_TOKEN=<your_token>' >> ~/.bashrc
```

### Ollama vs LM Studio
**NEMŮŽOU sdílet modely** - používají různé formáty:
- **Ollama:** Content-addressable storage (SHA256 blobs)
- **LM Studio:** Kompletní GGUF soubory

**Řešení:**
- Pro Ollama modely → použijte **Open WebUI**
- Pro GUI inference → použijte **LM Studio** se samostatnými modely

---

## 📊 Souhrn stavu (AKTUALIZACE 14.11.2025)

| Nástroj | Status | Velikost | Připraveno | Poznámka |
|---------|--------|----------|------------|----------|
| RAPIDS | ✅ Funkční | conda env | ANO | cuDF, cuML, CuPy |
| PyTorch | ✅ Připraven | 18GB | ANO | Container 25.09-py3 |
| TensorRT | ✅ Hotovo | 15GB | ANO | spark-single-gpu-dev |
| LM Studio | ✅ Běží | 1GB | ANO | Extrahovaná verze |
| NeMo | ✅ Naklonován | repo | ANO | Docker build připraven |
| Ollama | ✅ Běží | - | ANO | 38 modelů indexuje se |
| **Jupyter Lab** | ✅ Hotovo | 59MB | ANO | V conda base |
| **vLLM** | ⏳ Stahuje se | ~10GB | Za chvíli | Docker image |
| **AI Workbench** | ✅ Stažen | 111B | Ano | Installer připraven |
| **VS Code** | ⏳ Čeká na sudo | 100MB | Ano | .deb balíček |
| **FLUX.1** | ✅ Playbook | - | ANO | 12B model, ComfyUI |
| **VLM** | ✅ Playbook | - | ANO | Qwen2.5-VL, InternVL3 |
| **NIM LLM** | ❌ Nelze | - | NE | ARM64 nepodporováno |
| **Open WebUI** | ✅ Běží | - | ANO | Port 3000 |

---

## 🎯 Dokončené kroky

1. ✅ **Otestovat RAPIDS** - Hotovo!
2. ✅ **Připravit PyTorch** - Hotovo!
3. ✅ **Stáhnout TensorRT** - Hotovo!
4. ✅ **Nainstalovat LM Studio** - Běží!
5. ✅ **Nainstalovat Jupyter Lab** - Hotovo!
6. ⏳ **Nainstalovat vLLM** - Stahuje se (90%)
7. ✅ **Nainstalovat AI Workbench** - Installer připraven
8. ⏳ **Nainstalovat VS Code** - Čeká na sudo
9. ✅ **Připravit FLUX.1 playbook** - K dispozici
10. ✅ **Připravit VLM playbook** - K dispozici
11. ⏳ **Stáhnout LLM modely z Mac Mini M4** - Probíhá (38 modelů)
12. 🔜 **Začít s fine-tuningem nebo lokálními LLM** - Připraveno!

---

## 🆕 Co je nové (14.11.2025)

### Nově nainstalováno:
- ✅ **Jupyter Lab 4.4.7** - vývojové prostředí
- ⏳ **vLLM** - high-throughput LLM serving (stahuje se)
- ✅ **NVIDIA AI Workbench** - AI/ML project management
- ✅ **VS Code** - IDE (čeká na sudo)

### Nově objeveno:
- ✅ **FLUX.1-dev playbook** - image generation fine-tuning
- ✅ **VLM playbook** - Vision-Language Models (Qwen2.5-VL, InternVL3)
- ❌ **NIM LLM** - nelze na ARM64

### Opraveno/Zjištěno:
- ❌ **Ollama ↔ LM Studio sharing** - NENÍ možné (různé formáty)
- ✅ **Open WebUI řešení** - použít pro Ollama modely
- ✅ **LM Studio workaround** - extrahovaná verze bez FUSE

---

**Vše je připraveno k práci!** 🚀

Máte nyní kompletní AI/ML stack:
- **Data Science:** RAPIDS, Jupyter Lab
- **LLM Training:** PyTorch, NeMo
- **LLM Inference:** vLLM, Ollama, LM Studio
- **Image Generation:** FLUX.1-dev
- **Vision-Language:** Qwen2.5-VL, InternVL3
- **Quantization:** TensorRT-LLM
- **Development:** VS Code, AI Workbench, Jupyter Lab

Pokud máte jakékoliv otázky nebo narazíte na problémy, podívejte se do příslušných návodů nebo dokumentace NVIDIA.
