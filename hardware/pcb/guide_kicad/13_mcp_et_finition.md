# 13 — MCP KiCad + finition sur ta machine (vers le prêt-à-commander)

Ce chapitre te fait **terminer** la carte là où c'est possible : **sur ta machine
locale**, avec KiCad 9 et — si tu veux — un **serveur MCP KiCad** qui permet à
Claude de piloter KiCad (DRC, export fab, DFM). C'est ici que se scelle le
« 100 % prêt à commander », parce que la dernière étape de **routage** exige le
routeur interactif de KiCad (impossible en environnement distant sans écran —
voir `../KNOWN_GAPS.md` §1).

> 🔴 **Pourquoi pas 100 % automatique ?** Il reste **~108 liaisons** autour du
> QFN du P4 qui demandent du *push-and-shove* (le routeur pousse les pistes
> voisines) — seul le routeur interactif de KiCad (ou un autorouteur de bureau)
> sait le faire. De plus, certains points ne se valident qu'avec le vrai
> composant (CL du quartz, polarité caméra) — cf. `../VERIFY_RESOLVED.md`.

## 1. Le MCP KiCad est déjà configuré dans le repo

Un fichier **`.mcp.json`** (racine du repo) déclare le serveur **`kicad`**
(`kicad-mcp-pro`). Quand tu ouvres ce repo avec **Claude Code sur ta machine**,
il te proposera d'activer le serveur MCP « kicad » — **accepte**.

### Prérequis locaux

- **KiCad 9** installé (le MCP l'appelle via `kicad-cli`/`pcbnew`).
- **uv** ≥ 0.8 (`pip install uv` ou <https://docs.astral.sh/uv/>) — lance
  `uvx kicad-mcp-pro`.
- (Pour l'autoroutage) **Docker** ou **Java 21** (Freerouting).

### Ce que fait `kicad-mcp-pro`

- **ERC / DRC** via les moteurs de KiCad.
- **Export fabrication** (gerbers/drill) et **BOM/CPL**.
- **Analyse DFM** (estimations premier ordre).
- ⚠️ Sa propre doc le dit : *« les sorties générées nécessitent une revue humaine
  qualifiée avant fabrication »* — exactement notre position. Il **ne** fait pas
  l'autoroutage.
- Réf : <https://github.com/oaslananka/kicad-mcp>.

### Alternatives (selon ton besoin)

| Serveur | Points forts |
|---------|--------------|
| [oaslananka/kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp) | DRC + export fab + DFM (celui du `.mcp.json`) |
| [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) | **Autoroutage Freerouting** (Java/Docker) |
| [Seeed-Studio/kicad-mcp-server](https://github.com/Seeed-Studio/kicad-mcp-server) | analyse schéma/PCB (KiCad 9, pcbnew) |
| [lamaalrajih/kicad-mcp](https://github.com/lamaalrajih/kicad-mcp) | DRC + analyse (KiCad 9) |

> Pour ajouter le serveur d'autoroutage, ajoute une 2ᵉ entrée dans `.mcp.json`
> selon le README de mixelpixx (il embarque Freerouting via Docker).

## 2. La finition, étape par étape

Ouvre `../stratosdrone.kicad_pcb` dans KiCad 9 (il contient déjà le placement,
les zones et **~90 % du routage**, plus les correctifs récents : quartz 40 MHz,
R32).

### a. Router les ~108 liaisons restantes

1. **Autoroutage** (facultatif, gros du travail) : exporte le `.dsn`
   (**File → Export → Specctra DSN**), autoroute via **Docker Freerouting**
   (`docker run … freerouting`, voir `../ROUTING.md` Fallback), réimporte le
   `.ses` (**File → Import → Specctra Session**).
   - Ou via le serveur MCP **mixelpixx** : demande à Claude « autoroute the board
     with Freerouting ».
2. **Finir au routeur interactif** (indispensable pour les nets bloqués autour du
   P4) : touche **`X`**, mode **« Shove »** (pousse les pistes voisines). Route les
   dernières liaisons jaunes du chevelu (`F8` pour l'afficher), **dont R32**
   (GPIO36) et les paires diff si l'autorouteur les a évitées (ch. 11).
3. **Remplis les zones** : touche **`B`**.

### b. Vérifier — DRC = 0

- Via le MCP : demande à Claude « run DRC and list violations ».
- Ou dans KiCad : **Inspecter → DRC**. Vise **zéro erreur** (les « unconnected »
  doivent tomber à 0 une fois tout routé).

### c. Régler les résidus VERIFY (voir `../VERIFY_RESOLVED.md`)

- **C8/C9** : mettre la valeur = `2·(CL − Cstray)` pour la **CL** du quartz
  **C2831465** commandé (confirme la CL sur JLC).
- **Caméra** : si l'image ne vient pas au bench, tester l'inversion de polarité
  P/N côté firmware (config lanes MIPI).

### d. Exporter la fabrication

- Via le MCP (`kicad-mcp-pro`) : « export gerbers, drill, BOM and CPL for JLCPCB ».
- Ou KiCad : **File → Plot** (gerbers) + **Generate Drill Files**, et les
  BOM/CPL (`../jlcpcb/bom.csv` / `cpl.csv` sont déjà à jour côté composants).

### e. Commander

Suis **[`../ORDER_CHECKLIST.md`](../ORDER_CHECKLIST.md)** — la checklist finale
bloquante — puis le chapitre **[12](12_drc_fab_et_commande.md)** pour les options
JLCPCB (4 couches, JLC04161H-7628, ENIG, PCBA 2 faces).

## 3. Résumé honnête

Ce que **le sandbox a déjà fait** pour toi : correctifs design (quartz 40 MHz,
strap GPIO36), BOM/CPL à jour, zones remplies, gerbers **préliminaires**, et la
vérification documentée des points VERIFY. Ce qui **reste chez toi** : router les
~108 dernières liaisons (routeur interactif), DRC = 0, régler C8/C9 selon la CL,
et signer la checklist. **C'est cette finition locale qui rend la carte
réellement commandable.**

⬅️ Retour au **[sommaire](README.md)**
