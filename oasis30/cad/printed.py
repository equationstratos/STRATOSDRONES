#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OASIS 30 — les pièces imprimées qui **manquent** au kit Sub250.

Sub250 livre déjà (voir ../ref/sub250_stl/, repris tels quels, jamais redessinés) :
flancs latéraux, 4 patins de pied, platine d'antennes RX, support d'antenne de
queue. Ce module dessine le reste de ce qu'il faut pour un build complet :

    cam_cradle_bottom / cam_cradle_top   berceau caméra DJI O4 Pro, incliné
    arm_guard          ×4                clip de bras + canal pour les 3 phases
    batt_pad                             patin antidérapant sous la sangle
    xt30_grommet                         passe-fil de la découpe du roof
    gps_mount                            platine GPS/compas
    rear_bumper                          protection de la pointe arrière

Même chaîne que le carbone : B-rep OpenCASCADE → `.step` **et** `.stl`.
Matière : TPU 95A (sauf `gps_mount`, imprimable en PLA/PETG).
"""
import math

import tune as T
from oasisfly30 import box, cyl, cut, fuse, rpad, prism, drill, occ_ref


def _occ():
    return occ_ref()


# ══════════════════════════════════════════════════ berceau caméra O4 Pro
CAM_BODY_W = T.CAM_W          # 21 mm entre les flancs de cage
CAM_BODY_H = T.CAM_H          # 19 mm de haut
CAM_BODY_D = 22.0             # profondeur du corps caméra              # EST


def _cam_pocket(z0):
    """Le volume occupé par la caméra, incliné de CAM_TILT vers le haut."""
    w = CAM_BODY_W + 2 * T.CLR
    h = CAM_BODY_H + 2 * T.CLR
    pocket = box(-w / 2, -CAM_BODY_D / 2, z0, w, CAM_BODY_D, h)
    _occ().rotate([pocket], 0, 0, z0 + h / 2, 1, 0, 0, math.radians(-T.CAM_TILT))
    return pocket


CRADLE_W = T.CAM_W + 2 * T.WALL          # 24,2 — doit rester ≤ T.CAGE_GAP


def _side_screws(body, z, dz):
    """Perce les 2 vis M2 latérales qui traversent les flancs de cage."""
    for sx in (1, -1):
        c = _occ().addCylinder(sx * (CRADLE_W / 2 + 2), 0, z, -sx * (CRADLE_W + 4), 0, 0,
                               T.M2 / 2)
        body = cut(body, [(3, c)])
    return body


def cam_cradle_bottom():
    """Coquille basse : porte la caméra inclinée à 30°, vissée par les flancs."""
    shell = rpad(0, 0, 0, CRADLE_W, CAM_BODY_D + 2 * T.WALL, 13.0, 3.0)
    foot = rpad(0, -3, 0, CRADLE_W, CAM_BODY_D + 10.0, 2.4, 2.0)   # semelle d'appui
    body = fuse(shell + foot)
    body = cut(body, [_cam_pocket(3.0)])
    body = cut(body, [box(-CRADLE_W, -CAM_BODY_D, 13.0 - 0.001,
                          2 * CRADLE_W, 2 * CAM_BODY_D, 20)])       # arase le dessus
    body = _side_screws(body, 7.0, 0)
    return body


def cam_cradle_top():
    """Coquille haute : referme sur la caméra, ouverture pour l'objectif."""
    shell = rpad(0, 0, 0, CRADLE_W, CAM_BODY_D + 2 * T.WALL, 12.0, 3.0)
    body = cut(shell, [_cam_pocket(-8.0)])
    # fenêtre d'objectif à l'avant + évent arrière
    body = cut(body, [box(-8, CAM_BODY_D / 2 - 1, 0.5, 16, 6, 10)])
    body = cut(body, [box(-6, -CAM_BODY_D / 2 - 3, 3.0, 12, 5, 6)])
    body = _side_screws(body, 5.0, 0)
    return body


# ══════════════════════════════════════════════════ protège-bras + guide-fils
def arm_guard():
    """Clip en C sur le bras + canal pour les 3 fils de phase.

    Se pose **après** avoir passé les fils : les hélices ne peuvent plus les
    trancher, et le canal est côté intérieur (vers le châssis).
    """
    L = 30.0
    wi = T.ARM_W_MID + 2 * T.CLR                     # largeur intérieure
    hi = T.ARM_T + 2 * T.CLR
    outer = rpad(0, 0, 0, wi + 2 * T.WALL, L, hi + 2 * T.WALL + 4.2, 2.0)
    body = cut(outer, [box(-wi / 2, -L, T.WALL, wi, 2 * L, hi)])       # passage du bras
    # canal de câble Ø4,2 au-dessus, dans l'axe du bras
    c = _occ().addCylinder(0, -L / 2 - 1, T.WALL + hi + 2.6, 0, L + 2, 0, 2.1)
    body = cut(body, [(3, c)])
    # fente d'encliquetage par le dessous
    body = cut(body, [box(-2.0, -L, -1, 4.0, 2 * L, T.WALL + 1)])
    return body


# ══════════════════════════════════════════════════ patin de batterie
def batt_pad():
    """Patin antidérapant collé sur le roof, nervuré, ajouré pour la sangle."""
    L, W, H = 44.0, 24.0, 2.6
    body = rpad(0, 0, 0, W, L, H, 4.0)
    tools = []
    for y in (12, -12):                              # passages de sangle
        tools.append(rpad(0, y, -1, W + 2, 5.0, H + 2, 2.0)[0])
    body = cut(body, tools)
    ribs = []
    for y in range(-17, 18, 4):                      # nervures antidérapantes
        ribs.append(rpad(0, y, H - 0.001, W - 5, 1.8, 0.8, 0.9)[0])
    return fuse(body + ribs)


# ══════════════════════════════════════════════════ passe-fil XT30
def xt30_grommet():
    """S'encliquette dans la découpe du roof et protège le fil de batterie."""
    w, l, t = T.XT30_W + 2 * T.CLR, 13.0, T.PLATE_T
    collar = rpad(0, 0, 0, w + 2 * T.WALL, l + 2 * T.WALL, t + 2 * T.WALL, 1.8)
    body = cut(collar, [rpad(0, 0, -1, w - 1.5, l - 1.5, t + 2 * T.WALL + 2, 1.2)[0]])
    # gorge qui vient pincer l'épaisseur du roof
    body = cut(body, [rpad(0, 0, T.WALL, w, l, t, 1.4)[0]])
    return body


# ══════════════════════════════════════════════════ platine GPS
def gps_mount():
    """Platine GPS/compas, surélevée pour l'éloigner du VTX."""
    base = rpad(0, 0, 0, 24.0, 24.0, 2.0, 3.0)
    posts = []
    for sx in (1, -1):
        for sy in (1, -1):
            posts.append(cyl(sx * 8.0, sy * 8.0, 2.0, 6.0, 2.6))
    body = fuse(base + posts)
    body = drill(body, [(sx * 8.0, sy * 8.0) for sx in (1, -1) for sy in (1, -1)],
                 T.M2 / 2, -1, 12)
    body = drill(body, [(sx * 10.0, 0) for sx in (1, -1)], T.M3 / 2, -1, 4)
    return body


# ══════════════════════════════════════════════════ bumper arrière
def rear_bumper():
    """Capuchon TPU sur la pointe arrière — encaisse les atterrissages ratés."""
    hw = 8.0
    H = 7.5                       # assez bas pour ne pas toucher la plaque médiane
    outer = prism([(hw, 0), (hw - 3, -9), (-hw + 3, -9), (-hw, 0)], 0, H)
    inner = prism([(hw - T.WALL, 1), (hw - 3 - T.WALL, -9 + T.WALL),
                   (-hw + 3 + T.WALL, -9 + T.WALL), (-hw + T.WALL, 1)],
                  T.WALL, H)
    body = cut(outer, inner)
    slot_h = T.PLATE_B + 2 * T.CLR
    body = cut(body, [box(-hw, -12, 2.0, 2 * hw, 14, slot_h)])
    return body


# ══════════════════════════════════════════════════ registre
PRINTED = [
    ("cam_cradle_bottom", cam_cradle_bottom, 1, "TPU 95A", "Berceau caméra O4 Pro — coquille basse"),
    ("cam_cradle_top",    cam_cradle_top,    1, "TPU 95A", "Berceau caméra O4 Pro — coquille haute"),
    ("arm_guard",         arm_guard,         4, "TPU 95A", "Clip de bras + canal 3 phases"),
    ("batt_pad",          batt_pad,          1, "TPU 95A", "Patin antidérapant sous la sangle"),
    ("xt30_grommet",      xt30_grommet,      1, "TPU 95A", "Passe-fil de la découpe du roof"),
    ("gps_mount",         gps_mount,         1, "PLA/PETG", "Platine GPS/compas surélevée"),
    ("rear_bumper",       rear_bumper,       1, "TPU 95A", "Capuchon de pointe arrière"),
]
