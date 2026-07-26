# STRATOS 3 (Fr4n30-001) — 3" FPV freestyle imprimable

Un **3 pouces** style freestyle : plaques carbone + **toutes les pièces TPU**
imprimables, et **5 side panels** (flancs) au choix pour lui donner sa gueule.

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

## Les 5 side panels (flancs)

Ils ferment le corps **entre les deux plaques** : protègent le stack des impacts
latéraux, gardent les débris dehors, et donnent son look au build.
La forme est **symétrique** — le même STL fait le côté gauche **et** le droit,
donc tu en imprimes simplement **2**.

| | Style | Pour qui |
|---|---|---|
| **A** | Nervurée — pleine, nervures embossées | protection maxi, look plein |
| **B** | Hexa — treillis hexagonal | léger et aéré, refroidissement |
| **C** | Fentes aéro — longues fentes inclinées | style racer |
| **D** | Squelette — 3 grandes ouvertures | le plus léger |
| **E** | Demi-hauteur — ne ferme que le bas | laisse le stack respirer |

Tous ont **les mêmes fixations** : lèvres haute et basse qui viennent se prendre
sur les plaques, 4 trous M2. Ils s'échangent sans rien remonter d'autre.

## Pièces TPU

`tpu_cam_mount_top` + `tpu_cam_mount_bottom` (berceau caméra en deux coquilles) ·
`tpu_rear_bay` (poteau antenne VTX à 22° **Ø6,6** + fourreau antenne RX + canal
de câble) · `tpu_cap_holder` (condensateur **couché**) · `tpu_rx_holder` (bac
récepteur) · `tpu_gps_mount` (platine GPS à l'avant) · `tpu_arm_guard` (×4 :
pare-chocs de bras **+ canal pour les 3 fils de phase**) · `tpu_batt_pad`
(patins antidérapants sous la sangle).

## Réglages d'impression

- **TPU 95A** pour tout ce qui commence par `tpu_` et pour les side panels :
  buse 0,4 · couche **0,2 mm** · **3 périmètres** · remplissage **20 %** gyroïde ·
  **pas de support** (tout est dessiné auto-portant ≤ 45°) · 25-30 mm/s.
- Side panels : poser **à plat sur le flanc**, aucun support, et imprimer **×2**
  (le même fichier sert à gauche et à droite).
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
   remonte les side panels : ils cachent la soudure et protègent le fil.
5. Antennes **avant** de visser les flancs : elles s'engagent par le dessous.
6. Sangle : patins `tpu_batt_pad` collés sur la plaque haute, ça évite que la
   LiPo glisse en virage.

## Honnêteté

Ces pièces sont **générées et vérifiées géométriquement** (export STL OK,
cotes contrôlées), mais **jamais imprimées ni volées** : c'est un point de départ
propre, pas un kit validé en vol. Avant de lancer une série, imprime **une**
pièce test (`tpu_cap_holder`, la plus rapide) pour valider `CLR` sur ta machine,
et fais un montage à blanc avec tes composants réels — les cotes de la caméra,
du récepteur et du condensateur varient d'une marque à l'autre.
