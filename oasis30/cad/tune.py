#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OASIS 30 — toutes les cotes du châssis, en un seul endroit.

Repère : X vers la droite, **Y vers l'avant**, Z vers le haut.
Origine au centre de la face **inférieure** de la plaque basse.

D'où viennent les chiffres : voir ../ref/MEASURES.md — chaque cote est soit
publiée par Sub250 / ses revendeurs, soit mesurée sur `ref/photos/dimensions.webp`
(échelle 0,1712 mm/px), soit relevée dans les STL d'origine. Ce qui reste estimé
est marqué `# EST`.
"""
import math

# ─────────────────────────────────────────────── géométrie générale
WB          = 150.0    # entraxe diagonal moteur-moteur (publié)
TRACK_X     = 125.0    # écartement latéral moteur-moteur (dimensions.webp)
TRACK_Y     = math.sqrt(WB**2 - TRACK_X**2)          # = 82.916 → ±41.458
MX, MY      = TRACK_X / 2, TRACK_Y / 2
LEN_TOTAL   = 132.0    # longueur hors-tout nez → queue (dimensions.webp)
PROP_D      = 76.2     # hélices 3" (76,2 mm)

MOTORS = [(+MX, +MY), (-MX, +MY), (-MX, -MY), (+MX, -MY)]

# ─────────────────────────────────────────────── épaisseurs carbone (publiées)
PLATE_B     = 2.5      # plaque basse
PLATE_M     = 2.5      # plaque médiane (« upper bottom plate »)
PLATE_D     = 2.5      # pont étroit / splint, posé sur la médiane
PLATE_T     = 2.0      # roof (plaque haute)
ARM_T       = 3.0      # bras (version O4 Pro ; 2,5 sur la version O3)
CAGE_T      = 2.5      # flancs de la cage caméra

# ─────────────────────────────────────────────── empilage vertical (Z)
Z_BOTTOM    = 0.0
Z_ARM       = Z_BOTTOM + PLATE_B                     # 2.5  — les bras posent dessus
Z_MID       = Z_ARM + ARM_T                          # 5.5  — la médiane les coiffe
Z_DECK      = Z_MID + PLATE_M                        # 8.0  — le pont étroit
STANDOFF_H  = 20.0                                   # entretoises alu M3, posées SUR le pont
Z_TOP       = Z_DECK + PLATE_D + STANDOFF_H          # 30.5 — le roof
H_TOTAL     = Z_TOP + PLATE_T                        # 32.5
# ↑ recoupement : 32,5 mm est exactement la hauteur du flanc Sub250 d'origine
#   (mesurée dans ref/sub250_stl/side_panel.stl) — l'empilage tombe juste.
SIDE_PANEL_H = 32.5                                  # cote relevée dans le STL Sub250

# ─────────────────────────────────────────────── moteurs
MOTOR_PCD   = 9.0      # entraxe M2 des 1404 (carré 9×9)
MOTOR_BORE  = 6.5      # passage d'axe
MOTOR_PAD_D = 20.0     # Ø du patin moteur en bout de bras
M2          = 2.0
M3          = 3.0

# ─────────────────────────────────────────────── bras
ARM_W_ROOT  = 17.0     # largeur à la racine (fourche)
ARM_W_MID   = 9.5      # largeur au milieu de la poutre
ARM_FORK    = 11.0     # entraxe des deux branches de la fourche
ARM_R_IN    = 16.0     # rayon où commence le bras (sous les plaques)

# ─────────────────────────────────────────────── silhouette des plaques
# demi-largeurs (Y, demi-largeur) — relevées sur dimensions.webp
# Les LOBES à y ≈ ±12 sont ce qui donne de la matière autour des vis de bras :
# sans eux la fixation extérieure tombe dans le vide (contrôlée par export.py).
PROFILE_WIDE = [(48, 11.0), (42, 13.5), (34, 17.0), (28, 20.0), (20, 22.0),
                (15, 26.0), (9, 26.0), (4, 22.0),
                (0, 21.5),
                (-4, 22.0), (-9, 26.0), (-15, 26.0), (-20, 21.5),
                (-26, 16.5), (-34, 12.8), (-46, 12.8),
                (-58, 14.8), (-64, 11.0), (-67, 6.5)]
DECK_W      = 30.0     # largeur des plaques étroites (roof + pont)
DECK_Y0     = -66.0    # extrémité arrière
DECK_Y1     = 30.0     # extrémité avant — s'arrête avant le berceau caméra

# ─────────────────────────────────────────────── stack et périphériques
STACK       = 20.0     # FC/ESC AIO : M3 en 20×20
VTX_STACK   = 25.5     # perçage secondaire VTX/O4 : 25,5×25,5
STACK_Y     =  0.0     # stack centré sur le châssis
BAY_W       = 26.0     # fenêtre centrale de la plaque basse
CAM_W       = 21.0     # largeur hors-tout de la caméra O4 Pro
CAM_H       = 19.0     # hauteur du corps caméra                       # EST
CAM_TILT    = 30.0     # inclinaison caméra (degrés)
CAM_Y       = 55.0     # centre de la cage caméra (nez à +65 → 132 mm hors-tout)
CAM_Z       = 18.0     # hauteur de l'axe optique                      # EST
XT30_W      = 8.0      # passage du fil de batterie dans le roof
XT30_L      = 8.0      # longueur de la découpe (courte : le roof arrière est chargé)
XT30_Y      = -30.0    # découpe arrière du roof, entre la batterie et la platine RX
STANDOFF_D  = 5.0      # Ø extérieur des entretoises alu

# ─────────────────────────────────────────────── pièces imprimées
CLR         = 0.25     # jeu d'ajustement universel — le paramètre à toucher
FILLET      = 2.0      # rayon des congés sur le contour des plaques
EDGE_MIN    = 3.0      # marge minimale entre un perçage et le bord
WALL        = 1.6      # épaisseur de paroi standard des pièces TPU

# Écart intérieur de la cage caméra : il doit loger le **berceau**, pas la
# caméra nue — sinon le TPU ne rentre pas. C'est l'erreur classique du montage.
CAGE_GAP    = CAM_W + 2 * WALL + 2 * CLR             # 24,7 mm

# entretoises : 4 hautes (roof) + 2 courtes (cage caméra)
# ATTENTION : à y = -46 la plaque ne fait que 12,8 mm de demi-largeur ;
# une entretoise à x = 13 tomberait DANS LE VIDE (vis qui ne tient pas).
STANDOFFS_TOP  = [(13.0, 26.0), (-13.0, 26.0), (9.0, -34.0), (-9.0, -34.0)]
STANDOFFS_CAM  = [(13.0, 25.0), (-13.0, 25.0)]   # derrière le berceau  # EST

# ─────────────────────────────────────────────── contrôles
def checks():
    """Cotes que `export.py` vérifie sur la géométrie produite."""
    return {
        "entraxe diagonal": (WB, 0.5),
        "écartement latéral": (TRACK_X, 0.5),
        "écartement longitudinal": (TRACK_Y, 0.5),
        "hauteur hors-tout": (H_TOTAL, 0.3),
    }


if __name__ == "__main__":
    print("OASIS 30 — entraxe %.0f mm (%.1f × %.1f), hélices %.1f mm" % (WB, TRACK_X, TRACK_Y, PROP_D))
    print("moteurs :", ", ".join("(%+.2f, %+.2f)" % m for m in MOTORS))
    print("empilage : basse %.1f | bras %.1f | médiane %.1f | pont %.1f | roof %.1f → H %.1f mm"
          % (PLATE_B, ARM_T, PLATE_M, PLATE_D, PLATE_T, H_TOTAL))
    gap = TRACK_Y - PROP_D
    print("dégagement hélices avant/arrière : %.1f mm  (latéral : %.1f mm)"
          % (gap, TRACK_X - PROP_D))
