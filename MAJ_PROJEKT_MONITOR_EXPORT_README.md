# MAJ-PROJEKT-MONITOR - Export a tisk dokumentace

## 📋 Přehled

Systém pro export a tisk kompletní projektové dokumentace v různých formátech.

### Podporované formáty:
- **Markdown** (.md) - Textový formát pro GitHub, dokumentaci
- **PDF** (.pdf) - Profesionální dokumenty pro tisk a předání
- **Přímý tisk** - Odeslání na tiskárnu (CUPS)

### Co se exportuje:
1. **Zadání projektu** - Specifikace, požadavky, analýzy
2. **Dokumentace** - Kompletní technická dokumentace
3. **Grafická zobrazení** - Diagramy, grafy (v Markdown formátu)
4. **Výsledky testů** - Všechny testy včetně chyb
5. **Protokoly** - Log událostí projektu
6. **Předávací protokol** - Kontrolní seznam pro handover

---

## 🚀 Instalace

### 1. Instalace závislostí

```bash
# Pro PDF export
pip3 install reportlab

# Pro tisk (Linux)
sudo apt-get install cups cups-client
```

### 2. Zkontrolovat tiskárny

```bash
# Zobrazit dostupné tiskárny
lpstat -p

# Nastavit výchozí tiskárnu
lpoptions -d <printer_name>
```

---

## 💻 Použití

### CLI rozhraní

```bash
# Export do Markdown
python3 maj-projekt-monitor-export.py <project_id> markdown [cesta]

# Export do PDF
python3 maj-projekt-monitor-export.py <project_id> pdf [cesta]

# Tisk (výchozí tiskárna)
python3 maj-projekt-monitor-export.py <project_id> print pdf

# Tisk (konkrétní tiskárna)
python3 maj-projekt-monitor-export.py <project_id> print pdf <printer_name>
```

### Příklady

```bash
# Export projektu #1 do Markdown
python3 maj-projekt-monitor-export.py 1 markdown

# Export projektu #2 do PDF s vlastní cestou
python3 maj-projekt-monitor-export.py 2 pdf /tmp/projekt2.pdf

# Vytisknout projekt #1
python3 maj-projekt-monitor-export.py 1 print pdf

# Vytisknout na konkrétní tiskárnu
python3 maj-projekt-monitor-export.py 1 print pdf HP_LaserJet
```

---

## 🌐 Web rozhraní

Dashboard: **http://192.168.10.200:5050**

### Export tlačítka na každém projektu:
- **📄 MD** - Stáhnout jako Markdown
- **📑 PDF** - Stáhnout jako PDF
- **🖨️ Print** - Vytisknout přímo na tiskárnu

### API endpointy:

```bash
# Stáhnout Markdown
GET /api/project/<id>/export/markdown

# Stáhnout PDF
GET /api/project/<id>/export/pdf

# Vytisknout
GET /api/project/<id>/print/<format>
```

---

## 📊 Obsah exportu

### 1. Hlavička projektu
- Název, ID, status
- Fáze projektu
- Kvalitní skóre
- Zákazník, prostředí
- GitHub repository

### 2. Zadání a specifikace
- Analýzy projektu
- Požadavky
- Cíle a milníky

### 3. Dokumentace
- Technická dokumentace
- Doporučení z analýz
- TODOs a jejich stav

### 4. Programové moduly
- Seznam všech souborů
- Počet řádků kódu
- Jazyk a komplexita

### 5. Výsledky testů
- Celková statistika (úspěšnost)
- Poslední testy (10 nejnovějších)
- Chybové zprávy

### 6. Metriky kvality
- Kvalita kódu
- Pokrytí testy
- Dokumentace
- Bezpečnost
- Výkon
- Udržovatelnost

### 7. Protokoly událostí
- Poslední 50 událostí
- Timestamp, typ, metadata

### 8. Předávací protokol
- Kontrolní seznam pro handover
- Co musí být hotovo před předáním

---

## 🎨 Formáty exportu

### Markdown (.md)
✅ **Výhody:**
- Čitelný v textovém editoru
- Perfektní pro GitHub
- Snadno se upravuje
- Velký soubor (~15MB s logy)

📝 **Použití:**
- Dokumentace v repozitáři
- Wiki stránky
- Online preview

### PDF (.pdf)
✅ **Výhody:**
- Profesionální vzhled
- Připraveno k tisku
- Konzistentní formátování
- Malý soubor (~5-10KB)

📝 **Použití:**
- Tisk pro zákazníka
- Oficiální dokumentace
- Archivace
- Emailová příloha

### Přímý tisk
✅ **Výhody:**
- Okamžitý tisk
- Bez manuálního stahování
- Automatizace workflow

📝 **Použití:**
- Meeting dokumenty
- Rychlé review
- Podpisy

---

## 🔧 Konfigurace tisku

### Linux (CUPS)

```bash
# Zobrazit tiskárny
lpstat -p

# Přidat tiskárnu
sudo lpadmin -p <name> -E -v <device-uri>

# Nastavit výchozí
lpoptions -d <name>

# Test tisku
echo "Test" | lpr
```

### Síťové tiskárny

```bash
# HP tiskárna
sudo lpadmin -p HP_Office -E -v socket://192.168.1.100:9100

# PDF tiskárna (virtuální)
sudo apt-get install cups-pdf
```

---

## 📁 Výstupní soubory

### Automatické pojmenování:

```
MAJ_PROJECT_<id>_EXPORT_<timestamp>.md
MAJ_PROJECT_<id>_EXPORT_<timestamp>.pdf
```

### Příklad:
```
MAJ_PROJECT_1_EXPORT_20251203_203000.md
MAJ_PROJECT_1_EXPORT_20251203_203000.pdf
```

### Výchozí umístění:
```
/home/puzik/MAJ_PROJECT_*.md
/home/puzik/MAJ_PROJECT_*.pdf
```

---

## 🐛 Řešení problémů

### PDF export nefunguje

```bash
# Instalovat ReportLab
pip3 install reportlab

# Ověřit instalaci
python3 -c "import reportlab; print(reportlab.Version)"
```

### Tisk nefunguje

```bash
# Zkontrolovat CUPS
systemctl status cups

# Spustit CUPS
sudo systemctl start cups

# Zkontrolovat tiskárny
lpstat -p

# Zkontrolovat frontu tisku
lpq
```

### "Database is locked"

```bash
# Počkat na dokončení scanu
ps aux | grep "maj-projekt-monitor"

# Nebo zkusit znovu za chvilku
sleep 5 && python3 maj-projekt-monitor-export.py 1 markdown
```

### "Malformed JSON" v logs

- Automaticky ošetřeno
- Špatné JSON záznamy se přeskočí
- Export pokračuje normálně

---

## 📈 Příklady použití

### Scénář 1: Předání projektu zákazníkovi

```bash
# 1. Export do PDF
python3 maj-projekt-monitor-export.py 1 pdf /tmp/projekt_predani.pdf

# 2. Odeslat email s přílohou
# (nebo použít web dashboard tlačítko PDF)
```

### Scénář 2: GitHub dokumentace

```bash
# Export do Markdown
python3 maj-projekt-monitor-export.py 1 markdown /path/to/repo/DOCUMENTATION.md

# Commit do Git
cd /path/to/repo
git add DOCUMENTATION.md
git commit -m "Update project documentation"
git push
```

### Scénář 3: Týmový meeting

```bash
# Vytisknout dokumentaci pro všechny
python3 maj-projekt-monitor-export.py 1 print pdf

# Nebo z web dashboardu - kliknout 🖨️ Print
```

### Scénář 4: Audit/Review

```bash
# Export všech projektů
for id in 1 2; do
    python3 maj-projekt-monitor-export.py $id pdf /tmp/project_${id}_audit.pdf
done

# Výsledek: project_1_audit.pdf, project_2_audit.pdf
```

---

## 🔄 Integrace s workflow

### Automatický export při změně fáze

Přidat do `maj-projekt-monitor-bot.py`:

```python
if project_phase_changed:
    exporter = ProjectExporter(project_id)
    exporter.export_pdf(f"/archive/project_{project_id}_phase_{new_phase}.pdf")
```

### Denní backup dokumentace

Cron job:

```bash
# Každý den v 23:00
0 23 * * * /usr/bin/python3 /home/puzik/maj-projekt-monitor-export.py 1 pdf /backup/daily/project1_$(date +\%Y\%m\%d).pdf
```

---

## 📚 API Reference

### ProjectExporter class

```python
from maj_projekt_monitor_export import ProjectExporter

# Vytvořit exporter
exporter = ProjectExporter(project_id=1)

# Export Markdown
md_path = exporter.export_markdown()
md_path = exporter.export_markdown("/custom/path.md")

# Export PDF
pdf_path = exporter.export_pdf()
pdf_path = exporter.export_pdf("/custom/path.pdf")

# Tisk
success = exporter.print_document(format='pdf')
success = exporter.print_document(format='pdf', printer='HP_LaserJet')
```

---

## 🎯 Best Practices

### 1. Před předáním projektu
✅ Exportovat PDF + Markdown
✅ Zkontrolovat všechny sekce
✅ Vytisknout pro podpis

### 2. Pravidelná dokumentace
✅ Týdenní Markdown export do GitHub
✅ Měsíční PDF archiv
✅ Automatizovat cronem

### 3. Team collaboration
✅ Používat Markdown pro diskuze
✅ PDF pro formální review
✅ Print pro face-to-face meetings

### 4. Archivace
✅ PDF pro dlouhodobé uložení
✅ Název s datem a verzí
✅ Backup na NAS

---

## 📞 Podpora

### Problémy?

1. Zkontrolovat `/tmp/web-server.log`
2. Spustit test: `python3 maj-projekt-monitor-export.py 1 markdown /tmp/test.md`
3. Zkontrolovat závislosti: `pip3 list | grep reportlab`

### Nové funkce?

- Export do HTML
- Export do Word (.docx)
- Export grafů jako obrázky
- Batch export všech projektů

---

## 🏆 Výsledek

✅ **Kompletní export systém**
- 3 formáty (Markdown, PDF, Print)
- Web interface s tlačítky
- CLI rozhraní
- Automatické pojmenování
- Robustní error handling

✅ **Profesionální dokumenty**
- Strukturovaný obsah
- Všechny projektové artefakty
- Předávací protokol
- Připraveno k tisku

✅ **Snadné použití**
- Jedno kliknutí v dashboardu
- Nebo jednoduchý příkaz v CLI
- Automatický download

---

*Vygenerováno: 2025-12-03*
*Autor: Claude + Maj*
*Verze: 1.0*
