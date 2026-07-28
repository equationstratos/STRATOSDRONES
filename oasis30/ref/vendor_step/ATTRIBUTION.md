# Fichiers 3-D du commerce — origine et usage

Les `.step` de ce dossier sont les fichiers **des constructeurs**, repris
tels quels et jamais redessinés :

| Fichier | Pièce | Cotes lues dans le STEP |
|---|---|---|
| `DJI_O4_PRO_CAM.step` | caméra O4 Pro | 25,4 × 23,8 × 20,0 mm · tourillons Ø 2,1 en (0 ; ±10 ; 0) · objectif vers −X |
| `DJI_O4_AIR_UNIT_PRO.step` | air unit O4 Pro | 33,4 carré × 13,0 mm · fixation 25,5 × 25,5 · nappe en −Y, USB-C en −X |
| `DJI_O4_Pro_Antenna_v1.step` | antenne O4 Pro | fourreau Ø 3,5 mm · 85 mm utiles au-dessus du connecteur |
| `XING2_1404.step` | moteur XING2 1404 | Ø 19,9 × 18,6 mm · plan de pose z = −4,25 · haut de cloche z = 9,54 · fils vers −Y |

Ils ne servent qu'à **placer** les composants dans le châssis et à vérifier les
dégagements : rien n'en est dérivé pour l'impression. Le châssis, lui, est le
travail de ce dépôt.

Attention en les relisant : `getBoundingBox` d'OpenCASCADE est **majorante**
sur les faces courbes — il annonce Ø 28,3 pour la cloche du 1404, qui fait
Ø 19,9. Les cotes ci-dessus sont lues sur les **nœuds du maillage**.

[`../../cad/prep_vendor.py`](../../cad/prep_vendor.py) en tire les maillages du
visualisateur. Seul le maillage grossier de `cad/stl/viz/` est versionné ; le
maillage fin se régénère avec `--ref`, ces STEP en étant la source.
