# 04 — Schéma : Wi-Fi ESP32-C6 (1 composant)

Court chapitre : un seul composant, le module Wi-Fi, mais des broches à câbler
avec soin.

> 📄 Fiche **[fiches/blocs.md](fiches/blocs.md)**, section « Bloc 04 — Wi-Fi
> ESP32-C6 » : câblage broche→net de U3.

## Le module (U3)

- Symbole : **`Espressif:ESP32-C6-MINI-1/U`** (touche `A`). Réf `U3`, valeur
  `ESP32-C6-MINI-1`.
- Empreinte : `Espressif:ESP32-C6-MINI-1` (déjà ajoutée au ch. 01).

## Rôle et interface

Le C6 est le **co-processeur Wi-Fi** : le P4 lui parle en **SDIO** (protocole
**esp-hosted**, le P4 est hôte, le C6 esclave). Broches SDIO **fixes** côté C6 :

| Broche C6 | Net | Fonction |
|-----------|-----|----------|
| 25 | `SDIO_CLK` | horloge SDIO (GPIO19) |
| 24 | `SDIO_CMD` | commande (GPIO18) |
| 26 | `SDIO_D0` | data0 (GPIO20) |
| 27 | `SDIO_D1` | data1 (GPIO21) |
| 28 | `SDIO_D2` | data2 (GPIO22) |
| 29 | `SDIO_D3` | data3 (GPIO23) |

Ces nets sont **les mêmes** que côté P4 (ch. 03) → une fois câblés ici, le bus
SDIO est bouclé.

## Alimentation et straps

| Broche C6 | Net |
|-----------|-----|
| 3 | `3V3` |
| 8 | `C6_EN` (enable, piloté par le P4 via GPIO54) |
| 23 | `C6_BOOT` (strap GPIO9 — pull-up R21 au ch. 03) |
| 30 | `C6_U0RXD` (console C6) |
| 31 | `C6_U0TXD` |
| 1, 2, 11, 14, 36–53 | `GND` (toutes les masses / thermique du module) |

> ℹ️ Le module intègre déjà son antenne et ses passifs RF : côté schéma, on ne
> câble que l'alim, l'enable, le boot, la console et le SDIO. Au **PCB** (ch. 09),
> garde la **zone d'antenne** du module dégagée (keepout) et en bord de carte.

## Vérification du bloc

- 1 composant (U3). Les 6 nets SDIO + `C6_EN` + `C6_BOOT` sont désormais reliés
  au P4.

➡️ **[05_schema_capteurs_camera.md](05_schema_capteurs_camera.md)**
