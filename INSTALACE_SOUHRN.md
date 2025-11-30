# Souhrn instalace NVIDIA Build nástroj ů

**Datum:** 13.11.2025
**Systém:** DGX Spark GB10 (ARM64) - Ubuntu, CUDA 13.0

## ✓ Úspěšně nainstalováno

### 1. RAPIDS / CUDA-X Data Science ✓
**Umístění:** Conda prostředí `rapids-cuda13`
**Verze:**
- cuDF: 25.10.00
- cuML: 25.10.00
- CuPy: 13.6.0
- dask-cuda: 25.10.00

**Aktivace:**
```bash
conda activate rapids-cuda13
python -c "import cudf, cuml, cupy; print('RAPIDS OK')"
```

### 2. PyTorch Fine-tune ✓
**Umístění:** Docker container
**Image:** `nvcr.io/nvidia/pytorch:25.09-py3`
**Repozitář:** `~/dgx-spark-playbooks`

**Spuštění:**
```bash
# Pomocný script
~/run_pytorch_finetune.sh

# Nebo ručně:
docker run --gpus all -it --rm --ipc=host \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  -v ${PWD}:/workspace -w /workspace \
  nvcr.io/nvidia/pytorch:25.09-py3

# Uvnitř containeru:
pip install transformers peft datasets "trl==0.19.1" "bitsandbytes==0.48"
huggingface-cli login
cd dgx-spark-playbooks/nvidia/pytorch-fine-tune/assets
python Llama3_8B_LoRA_finetuning.py
```

### 3. NVFP4 Quantization ⏳
**Status:** Container se stahuje
**Image:** `nvcr.io/nvidia/tensorrt-llm/release:spark-single-gpu-dev`

**Spuštění (po dokončení stahování):**
```bash
docker run --rm --gpus all \
  nvcr.io/nvidia/tensorrt-llm/release:spark-single-gpu-dev \
  nvidia-smi
```

### 4. NeMo AutoModel ⚠️
**Umístění:** `~/NeMo-Automodel`
**Status:** Repo naklonováno, lokální instalace selh ala (ARM64 problém s triton)
**Řešení:** Použít Docker

**Docker build (připraven Dockerfile):**
```bash
cd ~/NeMo-Automodel
# Dockerfile už existuje v ~/NeMo-Automodel/docker/Dockerfile
# Používá PyTorch image jako základ
```

## ⏸️ Neproveden o

### NIM LLM
**Důvod:** Vyžaduje NGC API klíč
**Návod:** https://build.nvidia.com/spark/nim-llm

**Pro aktivaci:**
1. Vytvořit NGC účet: https://ngc.nvidia.com/setup/api-key
2. Nastavit klíč: `export NGC_API_KEY="váš-klíč"`
3. Stáhnout NIM container

## Návody a odkazy

1. **NeMo Fine-tune:** https://build.nvidia.com/spark/nemo-fine-tune
2. **PyTorch Fine-tune:** https://build.nvidia.com/spark/pytorch-fine-tune
3. **NVFP4 Quantization:** https://build.nvidia.com/spark/nvfp4-quantization
4. **NIM LLM:** https://build.nvidia.com/spark/nim-llm
5. **CUDA-X Data Science:** https://build.nvidia.com/spark/cuda-x-data-science

## Důležité poznámky

### ARM64 Kompatibilita
- **Problém:** Některé balíčky (např. triton) nemají ARM64 wheels
- **Řešení:** Použít Docker containery, které jsou optimalizované pro DGX Spark

### Unified Memory Architecture (UMA)
DGX Spark používá UMA - sdílená paměť mezi GPU a CPU. Při problémech s pamětí:
```bash
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
```

### Docker bez sudo
Pokud chcete Docker bez sudo:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

## Testování

### Test GPU
```bash
nvidia-smi
```

### Test RAPIDS
```bash
conda activate rapids-cuda13
python -c "import cudf; df = cudf.DataFrame({'a': [1,2,3]}); print(df)"
```

### Test Docker GPU
```bash
docker run --rm --gpus all nvcr.io/nvidia/cuda:13.0.1-devel-ubuntu24.04 nvidia-smi
```

## Další kroky

1. Dokončit stahování TensorRT-LLM containeru
2. Sestavit NeMo Docker image (pokud potřebujete NeMo)
3. Získat NGC API klíč (pokud chcete NIM)
4. Začít s fine-tuningem modelů!
