# Fichiers 3-D DJI — origine et usage

Les trois `.step` de ce dossier sont les fichiers **du constructeur**, repris
tels quels et jamais redessinés :

| Fichier | Pièce | Cotes lues dans le STEP |
|---|---|---|
| `DJI_O4_PRO_CAM.step` | caméra O4 Pro | 25,4 × 23,8 × 20,0 mm · tourillons Ø 2,1 en (0 ; ±10 ; 0) · objectif vers −X |
| `DJI_O4_AIR_UNIT_PRO.step` | air unit O4 Pro | 33,4 carré × 13,0 mm · fixation 25,5 × 25,5 · nappe en −Y, USB-C en −X |
| `DJI_O4_Pro_Antenna_v1.step` | antenne O4 Pro | fourreau Ø 3,5 mm · 85 mm utiles au-dessus du connecteur |

Ils ne servent qu'à **placer** les composants dans le châssis et à vérifier les
dégagements : rien n'en est dérivé pour l'impression. Le châssis, lui, est le
travail de ce dépôt.

[`../../cad/prep_dji_o4.py`](../../cad/prep_dji_o4.py) en tire les maillages du
visualisateur. Seul le maillage grossier de `cad/stl/viz/` est versionné ; le
maillage fin se régénère avec `--ref`, ces STEP en étant la source.
