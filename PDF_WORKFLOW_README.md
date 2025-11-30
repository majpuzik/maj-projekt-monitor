# PDF Workflow: DGX Spark ↔ Mac M4 + Adobe Creative Cloud

## Shrnutí
Kompletní systém pro práci s PDF mezi ARM64 DGX Spark (Linux) a Mac M4 (macOS) s Adobe Creative Cloud.

## Architektura
```
┌─────────────────────────────────────────────────────────────┐
│  DGX Spark (ARM64 Linux)                                     │
│  - Python PDF nástroje (pypdf, pdfplumber, ocrmypdf)        │
│  - Sdílená složka: ~/mac_m4_share                           │
│  - SSH přístup na Mac M4 přes Tailscale                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ sshfs + SSH
                       │ (100.92.179.61)
┌──────────────────────▼──────────────────────────────────────┐
│  Mac M4 (macOS 26.2)                                         │
│  - Adobe Acrobat DC 2025                                     │
│  - Adobe Photoshop 2025/2026                                 │
│  - Adobe Illustrator 2025/2026                               │
│  - Adobe Premiere Pro 2025                                   │
│  - Další Adobe CC aplikace...                                │
│  - PDF workspace: ~/PDF_workspace                            │
└─────────────────────────────────────────────────────────────┘
```

## Instalace

### 1. Připojení Mac M4 přes sshfs
```bash
# Mount (běží automaticky, ale pro ruční restart):
sshfs -o IdentityFile=/home/puzik/.ssh/id_ed25519 \\
      m.a.j.puzik@100.92.179.61:/Users/m.a.j.puzik/PDF_workspace \\
      ~/mac_m4_share

# Odpojení
fusermount -u ~/mac_m4_share
```

### 2. Kontrola připojení
```bash
df -h ~/mac_m4_share
ls ~/mac_m4_share/
```

## Použití

### A) Python PDF nástroje (lokální na DGX)

**Formát příkazů:**
```bash
python3 /home/puzik/pdf_tools.py <příkaz> [argumenty]
```

**Dostupné příkazy:**

#### 1. Sloučení PDF souborů
```bash
python3 /home/puzik/pdf_tools.py merge dokument1.pdf dokument2.pdf dokument3.pdf -o vysledek.pdf
```

#### 2. Rozdělení PDF na jednotlivé stránky
```bash
python3 /home/puzik/pdf_tools.py split dokument.pdf -o vystupni_slozka/
# Vytvoří: vystupni_slozka/page_001.pdf, page_002.pdf, ...
```

#### 3. Extrakce textu z PDF
```bash
# Do souboru
python3 /home/puzik/pdf_tools.py extract dokument.pdf -o text.txt

# Na stdout
python3 /home/puzik/pdf_tools.py extract dokument.pdf
```

#### 4. Informace o PDF
```bash
python3 /home/puzik/pdf_tools.py info dokument.pdf
# Zobrazí: počet stránek, autor, název, datum vytvoření
```

#### 5. OCR rozpoznání textu (vyžaduje Tesseract)
```bash
# Instalace Tesseract (pokud není nainstalován)
sudo apt install tesseract-ocr tesseract-ocr-ces tesseract-ocr-eng

# OCR s českou a anglickou podporou
python3 /home/puzik/pdf_tools.py ocr scanovany_dokument.pdf -o vysledek_ocr.pdf -l ces+eng

# Jen anglicky
python3 /home/puzik/pdf_tools.py ocr scanovany_dokument.pdf -o vysledek_ocr.pdf -l eng
```

### B) Adobe Acrobat na Mac M4 (vzdálené)

**Formát příkazů:**
```bash
/home/puzik/adobe_pdf_remote.sh <příkaz> [argumenty]
```

**Dostupné příkazy:**

#### 1. Otevřít PDF v Adobe Acrobat
```bash
/home/puzik/adobe_pdf_remote.sh open dokument.pdf
# Automaticky přenese soubor na Mac a otevře v Acrobatu
```

#### 2. Sloučení PDF (Adobe kvalita)
```bash
/home/puzik/adobe_pdf_remote.sh merge doc1.pdf doc2.pdf doc3.pdf -o vysledek.pdf
# Otevře soubory v Acrobatu, proveďte merge ručně:
# Tools → Combine Files → Add Files → Combine
```

#### 3. OCR přes Adobe Acrobat
```bash
/home/puzik/adobe_pdf_remote.sh ocr scanovany.pdf vysledek_ocr.pdf
# Otevře v Acrobatu, proveďte OCR ručně:
# Tools → Scan & OCR → Recognize Text → In This File
```

#### 4. Konverze PDF → Word
```bash
/home/puzik/adobe_pdf_remote.sh convert-word dokument.pdf vysledek.docx
# Otevře v Acrobatu, proveďte export ručně:
# File → Export To → Microsoft Word → Word Document
```

#### 5. Seznam souborů na Mac M4
```bash
/home/puzik/adobe_pdf_remote.sh list
```

## Workflow příklady

### Příklad 1: Sloučit 3 PDF rychle (Python)
```bash
cd /path/to/pdfs
python3 /home/puzik/pdf_tools.py merge report_Q1.pdf report_Q2.pdf report_Q3.pdf -o annual_report.pdf
```

### Příklad 2: OCR scan → prohledávatelné PDF (Python)
```bash
python3 /home/puzik/pdf_tools.py ocr sken_faktury.pdf faktura_searchable.pdf -l ces
```

### Příklad 3: Konverze PDF → Word přes Adobe
```bash
# Přenést na Mac a otevřít v Acrobatu
/home/puzik/adobe_pdf_remote.sh convert-word smlouva.pdf smlouva.docx

# Po dokončení konverze na Macu, stáhnout zpět:
cp ~/mac_m4_share/smlouva.docx ./
```

### Příklad 4: Kompletní workflow (DGX → Mac → zpět)
```bash
# 1. Vytvoření testovacích PDF na DGX
echo "Dokument 1" > doc1.txt
echo "Dokument 2" > doc2.txt
libreoffice --headless --convert-to pdf doc1.txt doc2.txt

# 2. Sloučení lokálně (Python)
python3 /home/puzik/pdf_tools.py merge doc1.pdf doc2.pdf -o merged.pdf

# 3. Přenést na Mac a otevřít v Adobe Acrobat pro finální úpravy
/home/puzik/adobe_pdf_remote.sh open merged.pdf

# 4. Po úpravách na Macu, soubor je automaticky dostupný:
ls ~/mac_m4_share/merged.pdf
```

## Nastavení pro automatické připojení při startu

Přidejte do `~/.bashrc`:
```bash
# Automatické připojení Mac M4
if ! mountpoint -q ~/mac_m4_share; then
    sshfs -o IdentityFile=/home/puzik/.ssh/id_ed25519 \\
          m.a.j.puzik@100.92.179.61:/Users/m.a.j.puzik/PDF_workspace \\
          ~/mac_m4_share 2>/dev/null
fi

# Aliasy pro rychlý přístup
alias pdfmerge='python3 /home/puzik/pdf_tools.py merge'
alias pdfsplit='python3 /home/puzik/pdf_tools.py split'
alias pdfextract='python3 /home/puzik/pdf_tools.py extract'
alias pdfinfo='python3 /home/puzik/pdf_tools.py info'
alias pdfocr='python3 /home/puzik/pdf_tools.py ocr'
alias adobe='~/adobe_pdf_remote.sh'
```

Po restartu terminálu:
```bash
source ~/.bashrc

# Použití aliasů
pdfmerge doc1.pdf doc2.pdf -o result.pdf
adobe open result.pdf
```

## Technické detaily

### Komunikace
- **SSH**: Port 22 přes Tailscale VPN (100.92.179.61)
- **sshfs**: FUSE filesystem pro transparentní sdílení souborů
- **Authentication**: SSH klíč `/home/puzik/.ssh/id_ed25519`

### Instalované nástroje
**DGX Spark:**
- Python 3.13 (Miniconda)
- pypdf 6.3.0
- pdfplumber 0.11.8
- ocrmypdf 16.12.0
- pikepdf 10.0.2
- LibreOffice (pro TXT→PDF konverzi)

**Mac M4:**
- macOS 26.2 (Sequoia beta)
- Adobe Acrobat DC 2025
- Kompletní Adobe Creative Cloud 2025/2026

### Limity
- **ARM64**: VirtualBox nepodporuje ARM64, proto vzdálený přístup na Mac
- **Adobe API**: Plná automatizace vyžaduje Adobe Acrobat JavaScript API (pro pokročilé operace)
- **OCR**: Python ocrmypdf vyžaduje Tesseract-OCR nainstalovaný na systému

## Troubleshooting

### Problém: sshfs není připojený
```bash
# Kontrola
mountpoint ~/mac_m4_share

# Opětovné připojení
fusermount -u ~/mac_m4_share  # Odpojit
sshfs -o IdentityFile=/home/puzik/.ssh/id_ed25519 \\
      m.a.j.puzik@100.92.179.61:/Users/m.a.j.puzik/PDF_workspace \\
      ~/mac_m4_share
```

### Problém: SSH timeout
```bash
# Kontrola Tailscale připojení
tailscale status | grep majmacminim4

# Test ping
ping -c 2 100.92.179.61

# Test SSH
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 m.a.j.puzik@100.92.179.61 "echo OK"
```

### Problém: Adobe Acrobat se neotevře
```bash
# Kontrola, zda je Acrobat spuštěný na Macu
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 m.a.j.puzik@100.92.179.61 \\
    "ps aux | grep -i acrobat | grep -v grep"

# Restartovat Acrobat
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 m.a.j.puzik@100.92.179.61 \\
    "killall AdobeAcrobat && open -a '/Applications/Adobe Acrobat DC/Adobe Acrobat.app'"
```

## Kontakt a další info
- DGX Spark: `puzik@spark-47f9` (Ubuntu 24.04 ARM64)
- Mac M4: `m.a.j.puzik@majmacminim4` (macOS 26.2)
- Tailscale VPN: 100.92.179.61

---
**Vytvořeno:** 2025-11-26
**Verze:** 1.0
**Status:** ✅ Plně funkční
