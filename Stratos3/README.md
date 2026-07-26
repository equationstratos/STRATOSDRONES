# STRATOS 3 (Fr4n30-001) — 3" FPV freestyle imprimable

Un **3 pouces** style freestyle : plaques carbone + **toutes les pièces TPU**
imprimables, et **5 canopées** au choix pour lui donner sa gueule.

Tout est paramétrique dans [`cad/frame3.scad`](cad/frame3.scad) — change le bloc
`TUNE`, ré-exporte, c'est tout.

```bash
./cad/export.sh          # écrit cad/stl/*.stl (+ aperçus)
```

## Géométrie

| | |
|---|---|
| Entraxe | **142 mm** (diagonale moteur à moteur) |
| Hélices | **3"** (76 mm) |
| Moteurs | 1404 / 1804, entraxe **12 mm** M2 |
| Stack | **30,5 × 30,5** M3 |
| Plaques | basse **3 mm**, haute **2 mm** carbone |
| Hauteur de corps | 22 mm entre plaques |
| Caméra | nano/micro 19 mm, **inclinaison 30°** |

## Les 5 canopées

| | Style | Haut. | Pour qui |
|---|---|---|---|
| **A** | Cinewhoop wrap — coque enveloppante | 26 mm | look propre, protège tout, cinématique |
| **B** | Racer low — basse et effilée | 17 mm | racing, traînée mini, le plus léger |
| **C** | Split aero — nervures latérales | 22 mm | style Split-X, rigidité en plus |
| **D** | Cage ajourée — grandes ouïes | 21 mm | vol chaud / été, refroidissement maxi |
| **E** | Duck bill — bec avant plongeant | 23 mm | freestyle, protège l'objectif en crash |

Toutes partagent **les mêmes fixations** (trame 30,5 + vis avant) et les mêmes
sorties : fenêtre caméra inclinée à 30°, deux passages d'antenne à l'arrière,
accès **USB/bind** sur le flanc droit, ouïes d'entrée et de sortie d'air.
Tu peux donc les échanger sans rien remonter d'autre.

## Pièces TPU

`tpu_cam_mount_top` + `tpu_cam_mount_bottom` (berceau caméra en deux coquilles) ·
`tpu_rear_bay` (poteau antenne VTX à 22° **Ø6,6** + fourreau antenne RX + canal
de câble) · `tpu_cap_holder` (condensateur **couché**) · `tpu_rx_holder` (bac
récepteur) · `tpu_gps_mount` (platine GPS à l'avant) · `tpu_arm_guard` (×4 :
pare-chocs de bras **+ canal pour les 3 fils de phase**) · `tpu_batt_pad`
(patins antidérapants sous la sangle).

## Réglages d'impression

- **TPU 95A** pour tout ce qui commence par `tpu_` et pour les canopées :
  buse 0,4 · couche **0,2 mm** · **3 périmètres** · remplissage **20 %** gyroïde ·
  **pas de support** (tout est dessiné auto-portant ≤ 45°) · 25-30 mm/s.
- Canopées : poser **la face ouverte sur le plateau**, ça évite tout support et
  donne la meilleure finition sur le dessus.
- `tpu_arm_guard` : imprimer **×4**, canal de câble vers l'intérieur.
- Plaques carbone : **découpe** (CNC/laser), pas impression — les `.stl` servent
  de gabarit, `cad/dxf/` pour l'atelier.

## Détails de conception (les pièges déjà réglés)

- **Fente XT30 dans la plaque haute** : le fil de batterie descend **droit** vers
  les pads de l'ESC au lieu de frotter sur un bord carbone. C'est la découpe
  rectangulaire arrière de `top_plate` (8 × 8 mm + jeu).
- **Condensateur couché** dans son support : il ne dépasse plus jamais du
  châssis et ne prend pas un coup au premier crash.
- **Fils moteur** : 3 phases par bras, guidées dans le canal du `tpu_arm_guard`
  — les hélices ne peuvent plus les trancher.
- **Antenne VTX à 22°** : l'alésage du poteau (**Ø6,6**) correspond à une
  Foxeer/RHCP standard, tête vers le haut, hors du carbone.
- **GPS à l'avant**, loin du VTX (moins de bruit sur la réception).
- **Jeu d'ajustement `CLR = 0,25 mm`** appliqué sur toutes les portées : c'est le
  paramètre à toucher en premier si ton imprimante sort serré ou lâche.

## Astuces de montage

1. Monte **les moteurs avant tout** : vis M2 par le dessous, frein-filet, et
   vérifie qu'aucune vis ne dépasse dans le bobinage.
2. Passe les 3 fils de phase **avant** de clipser les `tpu_arm_guard`.
3. Soude l'**XT30 en dernier**, condensateur d'abord — plus de place au fer.
4. Fais passer le fil de batterie **par la fente** de la plaque haute, puis
   remonte la canopée : elle cache la soudure et le fil est protégé.
5. Antennes **avant** de visser la canopée : elles s'engagent par le dessous.
6. Sangle : patins `tpu_batt_pad` collés sur la plaque haute, ça évite que la
   LiPo glisse en virage.

## Honnêteté

Ces pièces sont **générées et vérifiées géométriquement** (export STL OK,
cotes contrôlées), mais **jamais imprimées ni volées** : c'est un point de départ
propre, pas un kit validé en vol. Avant de lancer une série, imprime **une**
pièce test (`tpu_cap_holder`, la plus rapide) pour valider `CLR` sur ta machine,
et fais un montage à blanc avec tes composants réels — les cotes de la caméra,
du récepteur et du condensateur varient d'une marque à l'autre.
