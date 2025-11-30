# Rychlý start PyTorch Fine-tuning

## Krok 1: Spusťte PyTorch container

```bash
cd ~
docker run --gpus all -it --rm --ipc=host \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  -v ${PWD}:/workspace -w /workspace \
  nvcr.io/nvidia/pytorch:25.09-py3
```

## Krok 2: Uvnitř containeru - nainstalujte dependencies

```bash
pip install transformers peft datasets "trl==0.19.1" "bitsandbytes==0.48"
```

## Krok 3: Přihlaste se k Hugging Face

```bash
huggingface-cli login
# Zadejte svůj Hugging Face token
# Pro "Add token as git credential?" odpovězte: n
```

**Jak získat Hugging Face token:**
1. Jděte na: https://huggingface.co/settings/tokens
2. Vytvořte nový token (nebo použijte existující)
3. Zkopírujte token

## Krok 4: Přejděte do adresáře s příklady

```bash
cd dgx-spark-playbooks/nvidia/pytorch-fine-tune/assets
```

## Krok 5: Spusťte fine-tuning

### Možnost A: LoRA na Llama3-8B (doporučeno pro začátek)
```bash
python Llama3_8B_LoRA_finetuning.py
```

### Možnost B: qLoRA na Llama3-70B (větší model)
```bash
python Llama3_70B_qLoRA_finetuning.py
```

### Možnost C: Plný fine-tuning Llama3-3B
```bash
python Llama3_3B_full_finetuning.py
```

## Poznámky

- První spuštění stáhne model z Hugging Face (může trvat)
- Pro některé modely potřebujete požádat o přístup na Hugging Face
- Llama modely vyžadují přijetí licenčních podmínek

## Tipy pro DGX Spark

Pokud narazíte na problémy s pamětí:
```bash
# Vyčištění cache paměti (spusťte mimo container)
sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
```

## Alternativa: Rychlý test bez fine-tuningu

Pokud jen chcete otestovat, že vše funguje:

```bash
python -c "
import torch
import transformers
print(f'PyTorch: {torch.__version__}')
print(f'Transformers: {transformers.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print('✓ Všechno funguje!')
"
```
