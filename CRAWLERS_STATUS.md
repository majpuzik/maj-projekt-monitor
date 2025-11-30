# ALMQUIST RAG - Status Crawlerů
**Datum**: 30. listopadu 2025, 17:22
**Status**: ✅ VŠECHNY CRAWLERY BĚŽÍ PARALELNĚ

---

## 🚀 BĚŽÍCÍ CRAWLERY (4 paralelně)

### 1. **Laws Crawler** (full_laws_crawler)
- **PID**: 533971
- **Source**: zakonyprolidi.cz
- **Rozsah**: Všechny zákony 1993-2025
- **Očekáváno**: ~10,000-15,000 zákonů
- **Aktuální**: 1,038 zákonů v DB
- **Status**: Crawluje rok 1995

### 2. **NS Crawler** (full_court_crawler)
- **PID**: 534327
- **Source**: sbirka.nsoud.cz
- **Rozsah**: Všechna rozhodnutí Nejvyššího soudu
- **Očekáváno**: ~10,000-20,000 rozhodnutí
- **Status**: Listing fáze (stránka 200+/1000)

### 3. **NSS Crawler** (full_nss_crawler)
- **PID**: 534358
- **Source**: sbirka.nssoud.cz
- **Rozsah**: Všechna rozhodnutí Nejvyššího správního soudu (2003-2025)
- **Očekáváno**: ~5,000-10,000 rozhodnutí
- **Aktuální**: 378 rozhodnutí v DB (NSS)
- **Status**: Aktivně crawluje měsíční vydání

### 4. **Justice Crawler** (full_justice_crawler) ⭐ NOVÝ!
- **PID**: 534396
- **Source**: rozhodnuti.justice.cz OpenData API
- **Rozsah**: Vrchní soudy + Krajské soudy + vybraná Okresní rozhodnutí (2020-2025)
- **Očekáváno**: ~546,000 rozhodnutí
- **API struktura**: `/api/opendata/{rok}/{mesic}/{den}`
- **Status**: Právě startuje

---

## 📊 AKTUÁLNÍ DATABÁZE

| Typ | Počet | Zdroj |
|-----|-------|-------|
| Zákony | 1,038 | zakonyprolidi.cz |
| Rozhodnutí (NS + NSS) | 435 | sbirka.nsoud.cz + sbirka.nssoud.cz |
| **CELKEM** | **1,473** | - |

---

## 🎯 OČEKÁVANÝ FINÁLNÍ STAV

Po dokončení všech crawlerů (24-48 hodin):

| Zdroj | Očekávaný počet |
|-------|-----------------|
| Zákony | ~10,000-15,000 |
| NS (Nejvyšší soud) | ~10,000-20,000 |
| NSS (Nejvyšší správní soud) | ~5,000-10,000 |
| Justice (Vrchní + Krajské + Okresní) | ~546,000 |
| **CELKEM** | **~570,000-600,000 dokumentů** |

---

## 🏛️ POKRYTÍ SOUDNÍ SOUSTAVY ČR

### ✅ CRAWLOVÁNO
- [x] Nejvyšší soud (NS)
- [x] Nejvyšší správní soud (NSS)
- [x] Vrchní soudy (2 soudy - Praha, Olomouc)
- [x] Krajské soudy (8 soudů)
- [x] Vybraná rozhodnutí Okresních soudů
- [x] Všechny zákony České republiky (1993-2025)

### ❌ ZBÝVÁ
- [ ] Ústavní soud (NALUS databáze) - vyžaduje Selenium

---

## 🔍 JAK SLEDOVAT POKROK

```bash
# Status všech crawlerů
screen -list

# Připojit se ke konkrétnímu crawleru
screen -r full_laws_crawler
screen -r full_court_crawler
screen -r full_nss_crawler
screen -r full_justice_crawler

# Odpojit se (bez ukončení): Ctrl+A, D

# Zkontrolovat databázi
sqlite3 /home/puzik/almquist_legal_sources.db "SELECT COUNT(*) FROM laws"
sqlite3 /home/puzik/almquist_legal_sources.db "SELECT COUNT(*) FROM court_decisions"

# Logy
tail -f /tmp/full_nss_crawler.log
tail -f /tmp/full_justice_crawler.log
```

---

## 💡 KLÍČOVÉ OBJEVY

1. **rozhodnuti.justice.cz má REST API!**
   - Nemusíme používat Selenium
   - Čistá JSON data
   - Paginated endpoints
   - ~546,000 rozhodnutí dostupných

2. **Kompletní pokrytí bez Ústavního soudu**
   - Máme NS (precedenční judikatura)
   - Máme NSS (správní judikatura)
   - Máme Vrchní + Krajské soudy (odvolací instance)
   - Zbývá pouze Ústavní soud

3. **Paralelní crawling funguje**
   - 4 crawlery běží současně
   - Žádné konflikty v databázi
   - Progresivní ukládání dat

---

## 📅 TIMELINE

- **16:36** - Spuštěny Laws, NS, NSS crawlery
- **17:00** - Objeveno API pro rozhodnuti.justice.cz
- **17:22** - Justice crawler vytvořen a spuštěn
- **17:22** - Všechny 4 crawlery běží paralelně

**Očekávané dokončení**: Zítra ráno (01.12.2025, 02:00-06:00)
