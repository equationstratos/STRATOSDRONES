# Simulateur d'assemblage — TinyHoop MK1

Ouvre [`build.html`](build.html) par double-clic (aucun serveur, aucun build) :
tu prends les pièces une par une et tu les **emboîtes** virtuellement jusqu'au
drone complet.

Ce sont **les vraies pièces du visualisateur 3-D**
([`../viz/drone_viewer.html`](../viz/)) — mêmes maillages (plaques JeNo issues du
STEP, DJI O4, TPU imprimés, moteurs Readytosky 1104, pack DOGCOM), et **mêmes
coordonnées d'assemblage** : un montage terminé est identique au visualisateur,
pièce pour pièce.

## Comment ça marche

- **24 étapes** dans l'ordre réel du montage (plaque basse → moteurs →
  entretoises → FC → air unit → cage + caméra → plaque haute → baie arrière →
  RX → antennes → condo → GPS → bumpers → hélices → batterie).
- Les pièces non posées attendent **autour** du drone ; leur emplacement final
  est montré par un **fantôme bleu translucide**.
- **Glisse une pièce à la souris** : si tu la lâches assez près de son logement,
  elle **s'emboîte** d'elle-même (avec une petite animation).
- Ou utilise les commandes : `Entrée` / **Emboîter** pose l'étape courante,
  **Suivante** passe à la pièce d'après, **Tout assembler** joue le montage
  complet, **Recommencer** remet tout dans le bac.
- `R` fait tourner la pièce en main, `Échap` la repose dans le bac.
- La barre de progression et la gamme de montage à gauche suivent l'avancement ;
  à 24/24 le message **« Drone assemblé »** confirme la structure complète.

## Régénérer

```bash
python3 TinyHoopMK1/build/gen_build.py     # réécrit build.html
```

Le générateur importe les mêmes STL que `viz/gen_viewer.py` et les inline en
base64, d'où un fichier autonome (~15 Mo) qui marche en `file://`.

## Notes

- Les entretoises (châssis, carte, cage caméra) sont **procédurales et lisses**,
  comme dans le visualisateur — pas les anciens maillages facettés.
- Les positions viennent de `viz/gen_viewer.py` (`MODEL.elec`, `MOTORS`,
  `standoffs`) : si tu déplaces une pièce là-bas, reflète-la ici.
- Le guide texte du montage réel (PCB, impression, bring-up) reste
  [`../../docs/build_guide.md`](../../docs/build_guide.md) — ce simulateur en est
  la version 3-D interactive, pas un remplacement.
