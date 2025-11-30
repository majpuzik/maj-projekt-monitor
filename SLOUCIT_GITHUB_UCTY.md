# 🔄 Sloučení GitHub účtů (majpuzik-ops → majpuzik)

**Datum:** 14.11.2025
**Cíl:** Přenést všechny repozitáře z **majpuzik-ops** na **majpuzik** (puzik@outlook.com) a smazat starý účet

---

## ⚠️ DŮLEŽITÉ: GitHub neumožňuje přímé sloučení účtů

GitHub **nepodporuje automatické sloučení účtů**. Můžeš ale:
1. Přenést všechny repozitáře z jednoho účtu na druhý
2. Smazat starý účet
3. Výsledek: všechny repozitáře budou na jednom účtu

---

## 📋 KROK 1: Zjistit, jaké repozitáře máš na majpuzik-ops

1. **Přihlaš se** do GitHub jako **majpuzik-ops**
2. Jdi na: https://github.com/majpuzik-ops?tab=repositories
3. **Zapiš si** všechny repozitáře, které tam máš
4. Pokud **nemáš žádné repozitáře**, přeskoč na KROK 3

---

## 📦 KROK 2: Přenést repozitáře (pokud nějaké máš)

Pro **každý repozitář** na majpuzik-ops účtu:

### A) Přenos přes GitHub UI (doporučeno):

1. **Přihlaš se** jako **majpuzik-ops**
2. Jdi do repozitáře, který chceš přenést
3. Klikni na **"Settings"** (ozubené kolo nahoře)
4. Scrolluj úplně dolů na sekci **"Danger Zone"**
5. Klikni **"Transfer ownership"**
6. Do pole **"New owner's username"** zadej: **majpuzik**
7. Zadej název repozitáře pro potvrzení
8. Klikni **"I understand, transfer this repository"**

### B) Alternativa: Fork repozitáře

Pokud transfer nefunguje:

1. **Přihlaš se** jako **majpuzik**
2. Jdi na repozitář: `https://github.com/majpuzik-ops/nazev-repo`
3. Klikni **"Fork"**
4. Vyber **majpuzik** jako cíl forku
5. Po dokončení smaž originál na majpuzik-ops

---

## 🗑️ KROK 3: Smazat majpuzik-ops účet

**PŘED smazáním zkontroluj:**
- ✅ Všechny repozitáře jsou přeneseny
- ✅ Nemáš tam žádné důležité Gists
- ✅ Nemáš tam žádné issues nebo pull requesty

### Postup mazání účtu:

1. **Přihlaš se** jako **majpuzik-ops**
2. Jdi na: https://github.com/settings/account
3. Scrolluj úplně dolů na **"Delete account"**
4. Klikni **"Delete your account"**
5. Přečti si varování
6. Zadej své **uživatelské jméno** (majpuzik-ops) pro potvrzení
7. Zadej své **heslo**
8. Klikni **"Delete this account"**

---

## 🎯 KROK 4: Aktualizovat Git konfiguraci na DGX Spark

Po smazání majpuzik-ops účtu aktualizuj SSH config:

```bash
# Odeber konfiguraci pro starý účet
nano ~/.ssh/config
```

**Odstraň tyto řádky:**
```
# GitHub - Primární účet (majpuzik@gmail.com)
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
```

**Ponech pouze:**
```
# GitHub - Hlavní účet (puzik@outlook.com / majpuzik)
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_outlook
  IdentitiesOnly yes
```

**Ulož a zavři** (Ctrl+O, Enter, Ctrl+X)

---

## ✅ KROK 5: Test připojení

```bash
ssh -T git@github.com
```

Mělo by to vypsat:
```
Hi majpuzik! You've successfully authenticated, but GitHub does not provide shell access.
```

---

## 📝 Po dokončení

### Máš nyní:
- ✅ Jeden GitHub účet: **majpuzik** (puzik@outlook.com)
- ✅ Všechny repozitáře na jednom účtu
- ✅ SSH klíč správně nakonfigurován
- ✅ Git global config: `git config --global user.email "puzik@outlook.com"`

### Aktualizuj Git global email (pokud chceš):

```bash
git config --global user.email "puzik@outlook.com"
git config --global --list
```

---

## 🆘 Troubleshooting

### "You can't transfer to yourself"
- To znamená, že se účty **sdílejí stejný primární email**
- Řešení: Změň email na jednom účtu před transferem

### "Repository name already exists"
- Repozitář se stejným názvem už existuje na cílovém účtu
- Řešení: Přejmenuj repozitář před transferem

### "Transfer failed"
- GitHub sometimes requires extra verification
- Řešení: Kontaktuj GitHub Support: https://support.github.com

---

## 📞 Kontakt na GitHub Support

Pokud narazíš na problémy, GitHub Support může pomoci se sloučením účtů:
- **Web:** https://support.github.com
- **Téma:** Account and profile → Merge accounts
- **Zpráva:** "I would like to merge my accounts majpuzik-ops and majpuzik. I want to keep majpuzik and delete majpuzik-ops after transferring all repositories."

---

**Ready to start!** 🚀

1. Zjisti, jaké repozitáře máš na majpuzik-ops
2. Přenes je na majpuzik
3. Smaž majpuzik-ops účet
4. Aktualizuj SSH config
5. Test připojení
