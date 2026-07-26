# Simulateur d'assemblage — TinyHoop MK1

Ouvre [`build.html`](build.html) par double-clic : tu prends les pièces une par
une et tu les **emboîtes** virtuellement jusqu'au drone complet.

## Pourquoi c'est fidèle au visualisateur

`build.html` est **généré par le même script** que le visualisateur 3-D
([`../viz/gen_viewer.py`](../viz/)) : c'est **la même page**, avec le panneau
d'assemblage activé par défaut. Le simulateur ne redéfinit **aucune** pièce ni
position — il réutilise les groupes déjà construits par le viewer.

Conséquence : géométrie, cotes, matériaux, couleurs, batterie DOGCOM (étiquette
+ bords arrondis), supports caméra, bumpers, hélices, antennes… **tout est
identique par construction**, et ne peut pas diverger.

```bash
python3 TinyHoopMK1/viz/gen_viewer.py   # écrit viz/drone_viewer.html ET build/build.html
```

## Utilisation

- **21 pièces** dans l'ordre du montage (plaque basse → moteurs → entretoises →
  FC → air unit → cage + caméra → plaque haute → TPU → RX → antenne VTX → condo
  → GPS → buzzer → câbles → visserie → hélices → batterie).
- Les pièces non posées attendent **autour** du drone ; leur logement est
  indiqué par un **fantôme bleu**.
- Dans la liste de gauche : **un clic surligne** la pièce dans la 3-D,
  **un double-clic l'emboîte** toute seule.
- **Glisser-déposer** : lâchée près de son logement, la pièce s'emboîte.
- **Tout assembler** joue le montage complet ; **Éparpiller** remet tout autour.
- **Fantômes** : affiche/masque les repères translucides.

Le reste du viewer reste disponible dans la même page : **sélecteur de caméra**
(O4 Lite / nano analogique), **sélecteur d'antenne VTX** (5 modèles),
**sélecteurs de couleur** par pièce, vue éclatée, fil de fer, thème clair/sombre.

## Variantes d'URL

| URL | Effet |
|---|---|
| `build.html` | simulateur d'assemblage (par défaut) |
| `build.html?nobuild=1` | même page, panneau d'assemblage masqué |
| `../viz/drone_viewer.html?build=1` | le visualisateur avec le panneau d'assemblage |

Le guide texte du montage réel (PCB, impression, bring-up) reste
[`../../docs/build_guide.md`](../../docs/build_guide.md).
