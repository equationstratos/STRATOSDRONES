# 10 — PCB : zones de cuivre (plans)

On remplit les 4 couches avec leurs plans, dont la **fenêtre capteurs** dans le
plan du dessous.

## Le plan de remplissage

| Couche | Net de la zone |
|--------|----------------|
| **F.Cu** (dessus) | `GND` |
| **In1.Cu** | `GND` |
| **In2.Cu** | `3V3` |
| **B.Cu** (dessous) | `VBAT` (avec fenêtre capteurs) |

Chaque zone est un rectangle **inséré de 0.3 mm** par rapport au bord de carte
→ contour de zone : (0.3, 0.3) → (37.7, 0.3) → (37.7, 73.7) → (0.3, 73.7).

## Créer une zone

1. Sélectionne la couche cible (ex. **In1.Cu**).
2. Outil **Ajouter une zone de remplissage** (`Ctrl+Shift+Z` ou icône).
3. Dans la boîte de dialogue : choisis le **net** (ex. `GND`), la couche, puis
   trace le rectangle inséré ci-dessus.
4. Paramètres (pour coller au générateur) :
   - **Clearance** : 0.2 mm
   - **Épaisseur mini** : 0.25 mm
   - **Thermal gap** : 0.5 mm, **thermal bridge** : 0.5 mm
   - Hachurage de bord (hatch) : optionnel.
5. Répète pour **In2.Cu / 3V3**, **F.Cu / GND**.

## La zone B.Cu / VBAT + fenêtre capteurs

La zone du **dessous** porte `VBAT`, mais avec un **trou** pour dégager le champ
optique de U8 (ToF) et U9 (flux). C'est un polygone avec une **découpe interne** :

- **Contour externe** : le rectangle inséré (0.3 → 37.7 / 73.7).
- **Découpe (fenêtre capteurs)** : rectangle **X 12 → 26 mm, Y 28 → 50 mm**.

Deux façons de faire dans KiCad :

- **Simple** : crée la zone VBAT sur B.Cu (contour externe), puis ajoute une
  **« Zone de non-remplissage » (keepout / rule area)** sur B.Cu couvrant
  X 12–26 / Y 28–50 avec « interdire le remplissage de cuivre ». Résultat
  identique : pas de cuivre VBAT sous les capteurs.
- **Fidèle au générateur** : dessine directement le polygone VBAT avec le trou
  (outil zone → tracer le contour, puis ajouter un contour intérieur).

> ✅ Avant de remplir : **vérifie que la fenêtre est bien alignée** avec la
> position réelle de U8/U9 (ch. 09). Si tu as bougé les capteurs, ajuste la
> fenêtre en conséquence (`KNOWN_GAPS.md` §13).

## Remplir les zones

- Touche **`B`** : KiCad calcule et remplit toutes les zones.
- Touche **`N`** : masque le remplissage pour voir les pistes (l'inverse de B).

Fais **`B`** après le placement (pour visualiser) **et** de nouveau à la fin du
routage (obligatoire avant l'export fab).

## Couture (stitching) des plans

Pour bien relier les plans GND entre couches et donner un retour de courant
propre, sème des **vias GND** (via GND ↔ plans GND) le long des bords et près des
zones sensibles. Le générateur ajoute ~51 vias de couture d'alim vérifiés en
clearance ; fais-en autant à la main aux endroits denses.

## Vérification

- Les 4 zones existent, sur les bonnes couches, avec les bons nets.
- La fenêtre VBAT du dessous est vide de cuivre et couvre U8/U9.
- `B` remplit sans erreur de géométrie.

➡️ **[11_pcb_routage.md](11_pcb_routage.md)**
