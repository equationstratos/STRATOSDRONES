# 08 — PCB : stackup, règles, contour, trous M2

On configure la carte **4 couches** puis on dessine son contour exact.

## 1. Stackup 4 couches

Éditeur de PCB → **Fichier → Paramètres du circuit imprimé (Board Setup)** →
**Piles de couches (Physical Stackup)** :

- **Nombre de couches cuivre : 4**.
- Épaisseur totale **1.6 mm**.
- Chez JLCPCB, choisis le stackup **JLC04161H-7628** (impédance contrôlée pour
  les paires USB/CSI — utile au ch. 11).

Attribution des couches (rôles) :

| Couche | Usage dans ce design |
|--------|----------------------|
| **F.Cu** | signaux + plan GND |
| **In1.Cu** | plan **GND** |
| **In2.Cu** | plan **3V3** |
| **B.Cu** | signaux + plan **VBAT** |

## 2. Règles de conception (Design Rules / Net Classes)

Toujours dans **Board Setup → Contraintes** et **Net Classes** :

- **Classe par défaut** : largeur de piste **0.15 mm**, clearance **0.15 mm**,
  via **0.6/0.3 mm** (ces valeurs correspondent à ce que fait le générateur —
  routage à deux niveaux 0.15→0.127 mm dans les zones denses).
- **Classe « power »** (VBAT, 3V3, GND, VDD_CORE) : pistes plus larges,
  **0.3–0.5 mm**, pour le courant.
- **Classe « diff »** (paires USB et CSI) : voir ch. 11 — largeur/gap adaptés à
  l'impédance différentielle du stackup JLC04161H-7628.

> Ces réglages te donnent une DRC réaliste. Tu pourras les affiner en routant.

## 3. Contour de la carte (Edge.Cuts)

Cible : rectangle **38 × 74 mm**, coins arrondis **r = 6 mm**. Origine (0,0) au
**coin du nez**, `y` croissant vers l'arrière.

1. Sélectionne la couche **Edge.Cuts**.
2. Trace un **rectangle arrondi** : le plus simple est de tracer 4 segments de
   ligne (`Ctrl+Shift+L` ou l'outil ligne) et 4 arcs de rayon 6 aux coins.
   - Coins du rectangle : (0,0), (38,0), (38,74), (0,74).
   - Remplace chaque coin par un **arc r=6** (outil arc), tangent aux deux bords.
3. Vérifie les dimensions avec l'outil de mesure (`Ctrl+Shift+M`).

> 💡 Repère les valeurs dans `design.py` → `BOARD = dict(w=38.0, h=74.0,
> corner_r=6.0, mount_pitch_x=26.0, mount_pitch_y=62.0, mount_d=2.2)`.

## 4. Trous de montage M2 (NPTH)

4 trous **non métallisés (NPTH)** de Ø **2.2 mm**, nichés dans les coins arrondis,
au **pas 26 × 62 mm centré** → positions **(6,6), (32,6), (6,68), (32,68)**
(chacun à ~4.9 mm des bords).

- Pose un **Mounting Hole** (empreinte `MountingHole:MountingHole_2.2mm_M2`) à
  chaque position, **ou** un pad NPTH rond Ø2.2 (comme le fait `gen_pcb.py`).
- Les composants et le routage doivent **contourner** ces trous (ce sont des
  obstacles des deux côtés).

## 5. Origine et grille

- Place l'**origine de perçage/placement** au coin (0,0) : **Placer → Point
  d'origine de la grille** au coin nez. Ça facilite la saisie des coordonnées de
  placement du ch. 09.
- Grille de travail : **0.5 mm** pour le gros placement, **0.05–0.1 mm** pour le
  fin.

## Vérification

- Contour fermé (pas de trou dans Edge.Cuts) : lance la **DRC** (ch. 12) — elle
  se plaint si le contour n'est pas fermé.
- 4 trous M2 aux bonnes positions.

➡️ **[09_pcb_placement.md](09_pcb_placement.md)**
