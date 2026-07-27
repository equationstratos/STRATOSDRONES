# Atelier build FPV + Stratos FPV League

Le site et les affiches de l'**atelier de construction de drone FPV** — avec l'option
« **repars avec ton drone** » à la fin de la journée — et de son projet annexe, la
**Stratos FPV League** (classement à l'année, manches programmées **et** impromptues,
cadeaux en fin de saison).

## Contenu

| Fichier | Usage |
|---|---|
| **`index.html`** | Le site. Une seule page autonome (aucune dépendance, aucun script externe) : programme, tarifs, kits, ligue, FAQ, réservation. |
| **`affiche-atelier-a4.pdf`** | Affiche de l'atelier, A4, thème sombre — la version phare. |
| **`affiche-atelier-a3.pdf`** | La même en **A3**, pour les panneaux d'affichage. |
| **`affiche-atelier-a4-claire.pdf`** | Version **thème clair**, économe en encre. |
| **`affiche-ligue-a4.pdf`** / **`-a3.pdf`** | Affiche de la **ligue FPV** (barème, prix, « restez à l'écoute »). |
| `affiche-*.png` | Aperçus des mêmes visuels, pour le web ou un coup d'œil rapide. |
| `make_affiches.py` | Générateur des affiches (HTML autonome + `manifest.json`). |
| `render.cjs` | Rend le `manifest.json` en PDF d'impression + PNG d'aperçu. |

## Régénérer

```bash
python3 atelier/make_affiches.py    # -> 3 HTML autonomes + manifest.json
node    atelier/render.cjs          # -> 5 PDF (A4/A3) + 5 PNG d'aperçu
```

Tout le contenu modifiable — prix, horaires, barème de points, lots, coordonnées —
est regroupé en haut de `make_affiches.py` dans les dictionnaires `CONTACT`,
`ATELIER` et `LIGUE`. Le QR code est calculé **hors-ligne** par l'encodeur pur-Python
vendorisé dans [`../outreach/tools/qrcodegen.py`](../outreach/tools/) (MIT, Project
Nayuki) et inséré en **SVG vectoriel** : net à n'importe quelle taille d'impression,
aucun réseau requis.

Le site, lui, s'édite directement dans `index.html`. Deux blocs valent le détour :

- `SEASON` (bas du fichier) — le classement de la ligue. Passe `started` à `true` et
  remplis `rows` après la première manche ; le tableau se trie tout seul par points.
- les appels à `mailto(...)` — les trois boutons de réservation et le formulaire
  « restez à l'écoute » ouvrent le logiciel de mail avec un message pré-rempli.
  **Il n'y a pas de backend** : rien n'est stocké, rien n'est envoyé sans action de
  l'utilisateur. Si un vrai formulaire est voulu un jour, c'est le seul endroit à changer.

## Ce qui est décidé et ce qui ne l'est pas

Les **contenus pédagogiques** (déroulé de la journée, compétences, sécurité LiPo,
composition des kits) sont alignés sur ce que le dépôt sait réellement faire :
le drone monté à l'atelier est le **TinyHoop MK1** décrit dans
[`../TinyHoopMK1/`](../TinyHoopMK1/), avec la nomenclature de
[`../TinyHoopMK1/hardware/README.md`](../TinyHoopMK1/hardware/).

En revanche les **prix, dates, lieux et lots** sont des valeurs de départ cohérentes,
**pas des tarifs négociés** : ils se changent en un endroit chacun (voir ci-dessus)
et doivent être confirmés avant impression en série. Même chose pour la ligue : la
saison 1 n'a pas encore couru, le classement du site est donc explicitement vide.

> ⚠️ **Avant d'imprimer en série : scanne le QR** pour vérifier qu'il ouvre bien le site.
> Il pointe vers `https://equationstratos.github.io/STRATOSDRONES/atelier/` — si GitHub
> Pages n'est pas actif, change `CONTACT["url"]` dans `make_affiches.py` et régénère.

Une précision assumée sur l'affiche et le site : le drone monté à l'atelier vole sous
**Betaflight**, il n'est pas programmable. Le firmware ouvert (vol programmé, figures,
essaim) est développé en parallèle dans ce dépôt et n'a pas volé — la FAQ le dit
explicitement plutôt que de le vendre.

## Licence

Textes et mises en page : © 2026 Patrick Ardanny — réutilisables pour la promotion du projet.
`../outreach/tools/qrcodegen.py` : MIT (Project Nayuki), voir l'en-tête du fichier.
