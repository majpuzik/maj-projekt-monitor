# CHYBĚJÍCÍ SOUDY V ALMQUIST RAG

## ✅ CO UŽ MÁME (běží crawlery)

1. **Nejvyšší soud (NS)** - sbirka.nsoud.cz ✅
2. **Nejvyšší správní soud (NSS)** - sbirka.nssoud.cz ✅
3. **Vrchní + Krajské soudy** - rozhodnuti.justice.cz API ✅ (~546,000 rozhodnutí)
4. **Zákony** - zakonyprolidi.cz ✅

## ❌ CO NÁM CHYBÍ

### ÚSTAVNÍ SOUD

**nalus.usoud.cz** - NALUS databáze
- Nálezy a usnesení Ústavního soudu
- Potřebuje Selenium (ASP.NET formuláře)

## 📊 POKRYTÍ SOUDŮ

| Úroveň | Počet | Status | Důležitost |
|--------|-------|--------|------------|
| Nejvyšší soud | 1 | ✅ CRAWLUJE | ⭐⭐⭐⭐⭐ |
| Nejvyšší správní soud | 1 | ✅ CRAWLUJE | ⭐⭐⭐⭐⭐ |
| Ústavní soud | 1 | ❌ TODO (NALUS) | ⭐⭐⭐⭐⭐ |
| Vrchní soudy | 2 | ✅ CRAWLUJE (Justice API) | ⭐⭐⭐ |
| Krajské soudy | 8 | ✅ CRAWLUJE (Justice API) | ⭐⭐ |
| Okresní soudy (vybraná) | ~86 | ✅ CRAWLUJE (Justice API) | ⭐ |

## 🎯 DALŠÍ KROKY

### 1. Vysoká priorita
- [x] Crawler pro rozhodnuti.justice.cz (vrchní + krajské soudy) - **HOTOVO ✅**
- [ ] Selenium crawler pro NALUS (Ústavní soud)

### 2. Střední priorita  
- [ ] API integrace s judikaty.info (600k+ rozhodnutí)
- [ ] Iudictum.cz integrace

### 3. Nízká priorita
- [ ] Okresní soudy (individuálně)

## 💡 POZNÁMKY

- **rozhodnuti.justice.cz** má OpenData REST API! 🎉
  - Od roku 2020 (~546,000 rozhodnutí)
  - Obsahuje VYBRANÁ rozhodnutí (ne všechna)
  - API endpoints: `/api/opendata/{rok}/{mesic}/{den}`
- **Crawlery běží paralelně:**
  - Laws: ~10,000-15,000 zákonů
  - NS: ~10,000-20,000 rozhodnutí
  - NSS: ~5,000-10,000 rozhodnutí
  - Justice: ~546,000 rozhodnutí
- **Celkem očekáváno**: ~570,000+ dokumentů
