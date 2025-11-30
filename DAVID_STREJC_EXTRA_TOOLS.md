# 🎯 David Strejc - Další Nástroje

Nainstalované další nástroje od Davida Strejce.

---

## 1️⃣ Claude Powerline Rust ⚡⚡⚡⚡⚡

**Lokace:** `~/claude-powerline-rust/`
**Status:** ✅ NAINSTALOVÁNO A NAKONFIGUROVÁNO
**Funkce:** Ultra rychlý statusline pro Claude Code

### Co zobrazuje:
```
📂 Adresář  ⎇ Git  💰 Spending  🎪 Quota  🧠 Context  🤖 Model
```

### Rychlost:
- **Rust:** 150ms
- **TypeScript:** 1260ms
- **Zrychlení:** 8.4x ⚡

### Konfigurace:

#### Aktuální nastavení (`~/.claude/settings.json`):
```json
{
  "statusLine": {
    "command": "claude-powerline",
    "args": [],
    "theme": "dark",
    "style": "powerline"
  }
}
```

#### Dostupné témata:
- `dark` (výchozí)
- `light`
- `nord`
- `tokyo-night`
- `rose-pine`

#### Dostupné styly:
- `powerline` (výchozí) - Plná powerline s šipkami
- `minimal` - Jednoduchý styl

#### Změna tématu:
```bash
# Edituj
nano ~/.claude/settings.json

# Změň na:
{
  "statusLine": {
    "command": "claude-powerline",
    "theme": "tokyo-night",
    "style": "minimal"
  }
}

# Restartuj Claude Code
```

### Testování:
```bash
# Spusť samostatně
claude-powerline

# Měl bys vidět barevný statusline s info
```

### Výstup:
```
/your/directory  ⎇ main ♯abc1234 ✓  💰 $5.39  🎪 3.2MT Reset@:19:54->21:00  🧠 138.0K (10%)  🤖 Sonnet 4
```

---

## 2️⃣ Code Graph System 🕸️

**Lokace:** `~/code-graph-system/`
**Status:** ⚠️ PYTHON DEPENDENCIES NAINSTALOVÁNO, VYŽADUJE NEO4J
**Funkce:** Code analysis pomocí Neo4j grafu

### Co dělá:
Transformuje source code do queryable grafu v Neo4j databázi:
```
Source Code → Tree-sitter → SQLite → Neo4j → Cypher Queries
```

### Podporované jazyky:
- ✅ TypeScript/TSX (React, Next.js)
- ✅ JavaScript/JSX
- ✅ PHP (optimalizováno pro EspoCRM)
- 🚧 Python (coming soon)
- 🚧 Java (coming soon)

### Příklady dotazů:
```cypher
# Najdi nepoužívané React komponenty
MATCH (c:ReactComponent)
WHERE NOT EXISTS(()-[:IMPORTS]->(c))
RETURN c.name, c.file_path

# Najdi komponenty, které renderují Button
MATCH (c:ReactComponent)-[:RENDERS]->(e {name: "Button"})
RETURN c, e

# Zjisti circular imports
MATCH path = (m1:Module)-[:IMPORTS*]->(m1)
RETURN path
```

### Instalace Neo4j (POTŘEBA PRO FUNKČNOST):

#### Pomocí Docker:
```bash
docker run -d \
  --name neo4j-code \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# Ověř
curl http://localhost:7474
```

#### Nebo nativní instalace:
```bash
# Debian/Ubuntu
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j
```

### Použití:

#### 1. Připrav projekt config:
```bash
# Vytvoř config pro tvůj projekt
nano ~/code-graph-system/my-project.yaml
```

```yaml
name: my-project
source_dirs:
  - /path/to/your/project/src
exclude_patterns:
  - node_modules
  - "*.test.ts"
  - "*.spec.ts"
language: typescript
```

#### 2. Parsuj codebase:
```bash
cd ~/code-graph-system
python src/indexer/main.py --config my-project.yaml
```

#### 3. Importuj do Neo4j:
```bash
python tools/ultra_fast_neo4j_import.py \
  --config my-project.yaml \
  --bolt-parallel
```

#### 4. Query v Neo4j:
```bash
# Otevři browser
firefox http://localhost:7474

# Login: neo4j / password
# Spusť Cypher query
```

### Performance:
| Dotaz | grep/ripgrep | Neo4j | Zlepšení |
|-------|--------------|-------|----------|
| Find components rendering Button | ❌ Nezvládne | 24ms | ∞ |
| Component dependencies | ❌ Nereálné | 50ms | N/A |
| Circular imports | Custom script | 30ms | 100x |

---

## 📊 Stav Nástrojů

| Nástroj | Status | Vyžaduje Setup? |
|---------|--------|-----------------|
| **claude-powerline-rust** | ✅ Funguje hned | ❌ Ne |
| **code-graph-system** | ⚠️ Vyžaduje Neo4j | ✅ Ano (Docker) |

---

## 🔧 Troubleshooting

### Claude Powerline nefunguje

**Problém:** Statusline se nezobrazuje v Claude Code

**Řešení:**
```bash
# 1. Ověř, že binary funguje
claude-powerline

# 2. Zkontroluj settings
cat ~/.claude/settings.json

# 3. Restartuj Claude Code
```

### Code Graph System nefunguje

**Problém:** Neo4j není dostupný

**Řešení:**
```bash
# Zkontroluj Docker
docker ps | grep neo4j

# Spusť Neo4j
docker start neo4j-code

# Ověř
curl http://localhost:7474
```

---

## 💡 Kdy Co Použít?

### Claude Powerline:
- ✅ **Vždy** - zobrazuje užitečné info v realtime
- ✅ Rychlý náhled na spending
- ✅ Sledování context usage
- ✅ Git status na první pohled

### Code Graph System:
- ✅ Velké codebasy (1000+ souborů)
- ✅ Analýza dependencies
- ✅ Finding unused code
- ✅ Impact analysis před refactoring
- ❌ Malé projekty (overkill)

---

## 📚 Odkazy

### GitHub Repozitáře:
- **claude-powerline-rust:** https://github.com/david-strejc/claude-powerline-rust
- **code-graph-system:** https://github.com/david-strejc/code-graph-system

### Dokumentace:
- Claude Powerline: `~/claude-powerline-rust/README.md`
- Code Graph: `~/code-graph-system/README.md`

---

Vytvořeno: 2025-11-19
Autor: Claude Code (instalace nástrojů od Davida Strejce)
