# 09 — PCB : placement des composants

Le placement conditionne tout le routage. On suit la logique « Tello » : capteurs
au nez, RF puis CPU au centre, alim à l'arrière, moteurs aux coins.

> 🖼️ Repère visuel : ouvre la **carte annotée des composants** du repo,
> `../preview/component_map.png` (générée par `make map`). Elle montre où va
> chaque référence.

## Repères de placement (coordonnées clés)

`y = 0` au nez, `y = 74` à l'arrière. Ancrages principaux (de `gen_pcb.py`) :

| Zone | Composants | Repère |
|------|-----------|--------|
| Nez (y≈0–10) | **J4** caméra FFC | bord haut |
| Capteurs dessous | **U8** ToF, **U9** flux | colonne centrale, **face B** |
| RF (y≈18) | **U3** ESP32-C6 | ~ (19.5, 18.6), **antenne vers le bord** |
| CPU (y≈39) | **U1** ESP32-P4 | ~ (18.8, 38.6), au centre |
| Support CPU | Y1, flash U2, découplage | autour de U1 |
| Alim (y≈50–70) | U5, U10, U4, selfs, gros caps | vers l'arrière |
| Arrière (y≈74) | **J2** USB-C, **J1** batterie | bord bas |
| 4 coins | **Q1–Q4** + pads **J5–J8** | en retrait des trous M2 |

## Méthode

1. **Ancre les gros d'abord** : U1 (P4) au centre, U3 (C6) au-dessus avec sa
   **zone d'antenne dégagée** vers le bord de carte (keepout RF), J4 au nez,
   J2/J1 à l'arrière. Sélectionne un composant, touche `M` pour déplacer, tape
   éventuellement les coordonnées via **Propriétés** (double-clic → Position).
2. **Découplage au plus près** : chaque 100 nF (C12–C25, C28–C35…) doit toucher
   la/les broche(s) d'alim de sa puce. Les caps de charge du quartz (C8/C9)
   collés à Y1 et au P4 (boucle oscillateur la plus courte).
3. **Regroupe par sous-bloc** : garde ensemble buck (U5+L1+C3+C4+R4/R5),
   DC-DC cœur (U10+L2+C5+C36/C37+R30/R31), étage moteur i (Qi+Ri+Di+Ji).

## Faces (dessus / dessous)

Passe ces composants sur la **face arrière (B.Cu)** — sélection + touche `F`
(Flip) :

- **U8** (ToF), **U9** (flux optique) : ils doivent **regarder le sol**.
- **C31, C32** : découplage de ces deux capteurs, sur la même face.
- La carte du repo déporte aussi beaucoup de **condensateurs de découplage** en
  face arrière, directement **sous** leur puce, pour gagner de la place
  (compactage 45×85 → 38×74). Tu peux faire pareil au fur et à mesure du routage.

## La fenêtre optique (à préparer)

Les deux capteurs dessous seront placés dans la **colonne centrale**, dans la
zone **X ≈ 12–26 mm, Y ≈ 28–50 mm**. C'est là que le plan VBAT du dessous aura
une **ouverture** (ch. 10). Positionne U8 et U9 dans cette fenêtre (par ex. U8
vers (18, 36), U9 vers (18, 44)) pour qu'ils aient un champ dégagé.

## Contrôles de placement

- Active l'affichage des **courtyards** : aucun chevauchement > 0.3 mm.
- **Tous les pads à l'intérieur** du contour 38×74 (le générateur échoue sinon).
- Les composants **contournent** les 4 trous M2 et la zone d'antenne du C6.
- Densité forte autour du P4 : c'est attendu (`KNOWN_GAPS.md` « Board Density »).
  Micro-ajuste en routant.

➡️ **[10_pcb_zones.md](10_pcb_zones.md)**
