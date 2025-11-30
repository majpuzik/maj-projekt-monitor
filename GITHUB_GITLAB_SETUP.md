# 🔐 GitHub a GitLab Setup pro DGX Spark

**Vytvořeno:** 14.11.2025
**Systém:** DGX Spark GB10

---

## 📋 Tvoje účty:

### GitHub:
- **Primární:** majpuzik@gmail.com
- **Sekundární:** majpuzik-ops
- **Cíl:** Sloučit do jednoho účtu

### GitLab:
- TBD (přidáme později)

---

## 🔑 SSH Klíč (už vytvořen):

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE1aGM3KwhUCRtS5pK5gbA3PQG/32YTW6zqR0fESm9ar puzik@spark-47f9
```

**Umístění:** `~/.ssh/id_ed25519.pub`

---

## 📝 KROK 1: Přidání SSH klíče do GitHub (OBA účty)

### A) Primární účet (majpuzik@gmail.com):

1. **Zkopíruj SSH klíč:**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
   Nebo prostě zkopíruj:
   ```
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE1aGM3KwhUCRtS5pK5gbA3PQG/32YTW6zqR0fESm9ar puzik@spark-47f9
   ```

2. **Přidej do GitHub:**
   - Jdi na: https://github.com/settings/keys
   - Klikni **"New SSH key"**
   - Title: `DGX Spark GB10`
   - Key: *vlož SSH klíč*
   - Klikni **"Add SSH key"**

3. **Test připojení:**
   ```bash
   ssh -T git@github.com
   ```
   Mělo by to vypsat: `Hi majpuzik! You've successfully authenticated...`

### B) Sekundární účet (majpuzik-ops):

1. **Přihlaš se do druhého účtu:**
   - Jdi na: https://github.com/settings/keys
   - Klikni **"New SSH key"**
   - Title: `DGX Spark GB10 (shared)`
   - Key: *stejný SSH klíč jako výše*
   - Klikni **"Add SSH key"**

---

## 🔄 KROK 2: Sloučení GitHub účtů

GitHub **nedovoluje přímé sloučení** účtů, ale můžeš přenést repozitáře:

### Možnost A: Přenést repozitáře z majpuzik-ops → majpuzik@gmail.com

1. **Přihlaste se do majpuzik-ops účtu**
2. Pro každý repozitář:
   - Jdi do **Settings** → **General**
   - Scrolluj dolů na **"Transfer ownership"**
   - Zadej svůj primární username nebo email
   - Potvrď transfer

3. **Smazat majpuzik-ops účet (volitelné):**
   - Jdi na: https://github.com/settings/account
   - Scrolluj dolů na **"Delete account"**
   - Následuj instrukce

### Možnost B: Ponechat oba účty (doporučeno pro organizace)

Pokud `majpuzik-ops` používáš pro pracovní/organizační projekty:
- Nech oba účty
- Přidej SSH klíč do obou
- Použij Git config per-repository (viz níže)

---

## 📝 KROK 3: Přidání SSH klíče do GitLab

1. **Zkopíruj SSH klíč** (stejný jako pro GitHub)
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

2. **Přidej do GitLab:**
   - Jdi na: https://gitlab.com/-/profile/keys
   - Klikni **"Add new key"**
   - Title: `DGX Spark GB10`
   - Key: *vlož SSH klíč*
   - Expiration date: *nechat prázdné nebo nastavit datum*
   - Klikni **"Add key"**

3. **Test připojení:**
   ```bash
   ssh -T git@gitlab.com
   ```
   Mělo by to vypsat: `Welcome to GitLab, @your_username!`

---

## ⚙️ KROK 4: Git konfigurace (už nastaveno)

```bash
git config --global user.name "puzik"
git config --global user.email "majpuzik@gmail.com"
```

### Ověření:
```bash
git config --global --list
```

---

## 🔧 Pokročilá konfigurace: Více GitHub účtů

Pokud chceš používat **oba GitHub účty** na stejném stroji:

### 1. Vytvoř SSH config:
```bash
nano ~/.ssh/config
```

Přidej:
```
# Primární GitHub účet (majpuzik@gmail.com)
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519

# Sekundární GitHub účet (majpuzik-ops)
Host github-ops
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
```

### 2. Pro klonování z majpuzik-ops:
```bash
# Místo:
git clone git@github.com:majpuzik-ops/repo.git

# Použij:
git clone git@github-ops:majpuzik-ops/repo.git
```

### 3. Per-repository Git config:
```bash
# V repozitáři od majpuzik-ops:
cd /path/to/repo
git config user.name "puzik"
git config user.email "ops@example.com"  # nebo jiný email
```

---

## 🧪 Test připojení

### GitHub:
```bash
ssh -T git@github.com
```
Očekávaný výstup:
```
Hi majpuzik! You've successfully authenticated, but GitHub does not provide shell access.
```

### GitLab:
```bash
ssh -T git@gitlab.com
```
Očekávaný výstup:
```
Welcome to GitLab, @your_username!
```

---

## 📦 Rychlé příkazy:

### Klonovat repozitář (GitHub):
```bash
git clone git@github.com:username/repo.git
```

### Klonovat repozitář (GitLab):
```bash
git clone git@gitlab.com:username/repo.git
```

### Nastavit remote pro existující projekt:
```bash
cd ~/my-project
git init
git remote add origin git@github.com:username/repo.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

### Změnit email pro konkrétní projekt:
```bash
cd ~/work-project
git config user.email "majpuzik-ops@users.noreply.github.com"
```

---

## 🔐 Bezpečnost:

### SSH klíč je chráněn:
- Soukromý klíč (`~/.ssh/id_ed25519`) má permissions `600` - pouze ty ho můžeš číst
- Veřejný klíč (`~/.ssh/id_ed25519.pub`) můžeš sdílet - je bezpečný

### Pokud chceš passwordem chránit SSH klíč:
```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
```
(Zadáš nové heslo, které budeš muset zadat při každém použití)

---

## 📊 Souhrn kroků:

- [x] Git config nastaven (name: puzik, email: majpuzik@gmail.com)
- [ ] SSH klíč přidán do GitHub primárního účtu
- [ ] SSH klíč přidán do GitHub sekundárního účtu (majpuzik-ops)
- [ ] Rozhodnout o sloučení/ponechání účtů
- [ ] SSH klíč přidán do GitLab
- [ ] Test připojení GitHub
- [ ] Test připojení GitLab

---

## 🆘 Troubleshooting:

### "Permission denied (publickey)" error:
```bash
# Zkontroluj, že SSH agent běží:
eval "$(ssh-agent -s)"

# Přidej klíč:
ssh-add ~/.ssh/id_ed25519

# Test znovu:
ssh -T git@github.com
```

### Změnit default branch z master na main:
```bash
git config --global init.defaultBranch main
```

### Zobrazit všechny remotes:
```bash
git remote -v
```

---

**Pro další pomoc:**
- GitHub SSH docs: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
- GitLab SSH docs: https://docs.gitlab.com/ee/user/ssh.html
- Sloučení GitHub účtů: https://support.github.com (kontaktuj support)

---

**Připraven začít!** 🚀

1. Přidej SSH klíč do GitHub (oba účty)
2. Přidej SSH klíč do GitLab
3. Otestuj připojení
4. Začni používat Git!
