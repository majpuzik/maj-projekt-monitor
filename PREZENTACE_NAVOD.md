# Návod: Jak použít prezentaci ALMQUIST

## 📄 Soubory

- **Prezentace:** `/home/puzik/ALMQUIST_PREZENTACE.md`
- **Technická zpráva:** `/home/puzik/ALMQUIST_TECHNICKA_ZPRAVA_CVUT.md`
- **Tento návod:** `/home/puzik/PREZENTACE_NAVOD.md`

---

## 🎯 Možnosti prezentace

### 1. Reveal.js (HTML prezentace)

**Nejlepší pro:** Interaktivní prezentace v browseru

```bash
# Instalace reveal.js
npm install -g reveal-md

# Spuštění prezentace
reveal-md /home/puzik/ALMQUIST_PREZENTACE.md

# Export do HTML
reveal-md /home/puzik/ALMQUIST_PREZENTACE.md --static almquist-prezentace
```

**Výhody:**
- ✅ Krásné animace
- ✅ Navigace klávesami
- ✅ Speaker notes
- ✅ Exportovatelné do PDF

### 2. Pandoc → PDF (Beamer)

**Nejlepší pro:** PDF prezentace ve stylu LaTeX

```bash
# Instalace pandoc a LaTeX
sudo apt install pandoc texlive-latex-base texlive-fonts-recommended texlive-latex-extra

# Generování PDF
pandoc /home/puzik/ALMQUIST_PREZENTACE.md \
  -t beamer \
  -o ALMQUIST_PREZENTACE.pdf \
  --pdf-engine=xelatex \
  -V theme:Madrid \
  -V colortheme:beaver

# Nebo jednodušeji:
pandoc /home/puzik/ALMQUIST_PREZENTACE.md -o ALMQUIST_PREZENTACE.pdf
```

**Výhody:**
- ✅ Akademický look (LaTeX Beamer)
- ✅ Profesionální typografie
- ✅ Printovatelné

### 3. Pandoc → PowerPoint

**Nejlepší pro:** Editovatelný PowerPoint

```bash
# Generování PPTX
pandoc /home/puzik/ALMQUIST_PREZENTACE.md \
  -o ALMQUIST_PREZENTACE.pptx

# S custom template:
pandoc /home/puzik/ALMQUIST_PREZENTACE.md \
  -o ALMQUIST_PREZENTACE.pptx \
  --reference-doc=cvut_template.pptx
```

**Výhody:**
- ✅ Editovatelné v PowerPoint
- ✅ Kompatibilní všude
- ✅ Možnost doladit design

### 4. Marp (Markdown Presentation)

**Nejlepší pro:** Rychlé, moderní prezentace

```bash
# Instalace
npm install -g @marp-team/marp-cli

# Export PDF
marp /home/puzik/ALMQUIST_PREZENTACE.md --pdf

# Export PPTX
marp /home/puzik/ALMQUIST_PREZENTACE.md --pptx

# HTML
marp /home/puzik/ALMQUIST_PREZENTACE.md --html
```

---

## 🎨 Doporučené nastavení

### Pro akademickou prezentaci (ČVUT):
```bash
pandoc /home/puzik/ALMQUIST_PREZENTACE.md \
  -t beamer \
  -o ALMQUIST_PREZENTACE_CVUT.pdf \
  --pdf-engine=xelatex \
  -V theme:Madrid \
  -V colortheme:beaver \
  -V fontsize:11pt \
  -V aspectratio:169
```

### Pro webovou prezentaci:
```bash
reveal-md /home/puzik/ALMQUIST_PREZENTACE.md \
  --theme white \
  --highlight-theme github \
  --static almquist-web
```

---

## 📊 Struktura prezentace

**Celkem:** ~70 slidů (včetně příloh)

### Hlavní část (45 min):
1. Úvod (5 slidů) - 5 min
2. ALQUIST (5 slidů) - 7 min
3. Paradigma shift (4 slidy) - 6 min
4. Architektura (7 slidů) - 10 min
5. Implementace (6 slidů) - 8 min
6. Výsledky (5 slidů) - 5 min
7. Porovnání (4 slidy) - 6 min
8. Závěr (5 slidů) - 8 min

### Přílohy (6 slidů):
- A1: Detailní architektura
- A2: Training pipeline
- A3: DB schéma
- A4: Extended comparison
- A5: Technology decisions
- A6: References

### Rychlá verze (20 min):
Přeskoč: A1-A6 přílohy
Zkrať: Implementace (3 slidy místo 6)

---

## 🎤 Tips pro prezentaci

### Časování:
- **Krátká verze:** 20 min (bez příloh)
- **Střední verze:** 35 min (vybrané přílohy)
- **Plná verze:** 55 min (všechno)

### Klíčové slidy:
1. **Slide 6** - ALQUIST úspěchy (SGC winner)
2. **Slide 22** - Architektura diagram
3. **Slide 43** - Výsledky (porovnání)
4. **Slide 54** - ALQUIST vs ALMQUIST table

### Interaktivní části:
- **Slide 51** - "Kdy použít co?" (diskuse s publikem)
- **Slide 65** - Q&A

### Demo možnosti:
- Live RAG query (pokud Qdrant běží)
- Ukázka centrální DB (maj-almquist-log show)
- Conversation example (almqist_inference.py)

---

## 🚀 Quick start

### Varianta 1: Reveal.js (doporučeno)
```bash
cd /home/puzik
npm install -g reveal-md
reveal-md ALMQUIST_PREZENTACE.md
# Otevři browser na http://localhost:1948
```

### Varianta 2: PDF
```bash
cd /home/puzik
pandoc ALMQUIST_PREZENTACE.md -o ALMQUIST_PREZENTACE.pdf
xdg-open ALMQUIST_PREZENTACE.pdf
```

### Varianta 3: PowerPoint
```bash
cd /home/puzik
pandoc ALMQUIST_PREZENTACE.md -o ALMQUIST_PREZENTACE.pptx
libreoffice ALMQUIST_PREZENTACE.pptx
```

---

## 📝 Editace prezentace

### Formát:
- `---` = Nový slide
- `# Title` = Nadpis slidu
- `## Subtitle` = Podnadpis
- Standard Markdown pro obsah

### Přidat slide:
```markdown
---

## Nový slide

- Bullet point 1
- Bullet point 2

### Subsection
Text...
```

### Změnit theme (Reveal.js):
V YAML header (první řádky):
```yaml
theme: "black"  # nebo white, league, sky, beige...
```

---

## 🎓 Pro akademickou obhajobu

### Doporučená struktura (30 min):

1. **Úvod** (3 min)
   - Slidy 1-4

2. **Analýza ALQUIST** (5 min)
   - Slidy 6-9
   - Zdůrazni SGC úspěchy

3. **Paradigma shift** (4 min)
   - Slidy 12-15
   - Tabulka srovnání

4. **ALMQUIST architektura** (8 min)
   - Slidy 17-23
   - Diagram A1 (příloha)

5. **Implementace** (5 min)
   - Slidy 25-30
   - Dataset stats

6. **Výsledky** (3 min)
   - Slidy 32-36
   - Zdůrazni +18.8% empathy

7. **Závěr** (2 min)
   - Slidy 57-60

8. **Q&A** (5 min)

### Očekávané otázky:

**Q1:** "Proč ne fine-tune GPT-4?"
**A:** Open source requirement, cost, Czech optimization

**Q2:** "Jak řešíte halucinace?"
**A:** RAG grounding, planned safety layer

**Q3:** "Latence 15s je moc, ne?"
**A:** Ano, identified issue, GPU inference planned

**Q4:** "Porovnání s ALQUIST 5.0?"
**A:** Complementary, not replacement. Hybrid approach best.

---

## 🔗 Odkazy

- **Dokumentace:** `/home/puzik/ALMQUIST_TECHNICKA_ZPRAVA_CVUT.md`
- **Repository:** `/home/puzik/almqist/`
- **Centrální DB:** `/home/puzik/almquist-central-log/`
- **ALQUIST papers:** `/home/puzik/almqist/knowledge_base/alquist_papers/`

---

## ✅ Checklist před prezentací

- [ ] Export do PDF/PPTX
- [ ] Test zobrazení na projektoru
- [ ] Příprava demo (optional)
- [ ] Zkouška časování
- [ ] Backup na USB
- [ ] Presenter mode notes

---

**Vytvořeno:** 25. listopadu 2025
**Format:** Markdown (Reveal.js compatible)
**License:** CC BY-SA 4.0
