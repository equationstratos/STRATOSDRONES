# STRATOSDRONE PCB — vérification des points VERIFY (session automatisée)

Ce document rend compte de la **vérification maximale** des points ouverts
(`KNOWN_GAPS.md` §5, §6, §11, §14) menée pour rapprocher la carte d'un état
« prêt à commander ». Chaque point : ce qui a été vérifié, la **source
autoritaire**, la décision, et — honnêtement — le **résidu** qui ne peut être
clos que sur la vraie machine / le vrai composant.

> ⚠️ Contrainte d'environnement : ce travail a tourné dans un sandbox distant.
> Les pages distributeurs (LCSC/JLCPCB) et certaines datasheets sont bloquées par
> le proxy sortant ; les faits ci-dessous viennent donc de recherches web
> (résumés de datasheets/docs officielles) et de vérifications **locales** dans
> KiCad 7 (empreintes sur disque) et `pcbnew`. Les points marqués « à confirmer »
> doivent l'être sur le catalogue JLC en direct et/ou la carte physique.

---

## §11 — Quartz : **BUG FATAL corrigé** (mauvaise fréquence)

**Constat.** Le part LCSC utilisé, **C9002 = YXC X322512MSB4SI**, est un cristal
**12 MHz / 20 pF** (SMD3225-4P) — **pas** 40 MHz. Le champ « valeur » de `design.py`
affichait « 40 MHz », mais **JLCPCB monte le composant que le code LCSC résout**,
donc la carte serait partie avec un **12 MHz**. Or l'**ESP32-P4 exige un cristal
40 MHz** sur XTAL_P/XTAL_N (main xtal). Résultat : horloge fausse, la puce ne
démarre pas → carte morte.

**Preuves.**
- La convention de nommage YXC encode la fréquence juste après « X3225 » :
  X3225**8** = 8 MHz, X3225**12** = **12 MHz** (notre part), X3225**24** = 24 MHz,
  X3225**25** = 25 MHz — cohérent sur toute la série
  ([LCSC X32258MSB4SI 8 MHz](https://www.lcsc.com/product-detail/Crystals_YXC-X32258MSB4SI_C2682774.html),
  [X322524MSB4SI 24 MHz](https://www.lcsc.com/product-detail/C15643.html)).
- Deux fiches indépendantes donnent C9002 = **12 MHz, 20 pF, SMD3225-4P**
  ([JLCPCB C9002](https://jlcpcb.com/partdetail/Yxc-X322512MSB4SI/C9002),
  [LCSC C9002](https://www.lcsc.com/product-detail/C9002.html)).
- Exigence 40 MHz : *ESP32-P4 Hardware Design Guidelines* (circuit du main xtal).

**Correction appliquée** (`design.py`, Y1) : LCSC **C9002 → C2831465**
(**JWT YF4040M00033T8188097**, **40 MHz**, ±20 ppm, SMD3225-4P)
([JLCPCB C2831465](https://jlcpcb.com/partdetail/JWT-YF4040M00033T8188097/C2831465)).
Empreinte inchangée (même land 3225-4Pin). BOM/CPL régénérés (`jlcpcb/bom.csv`
montre désormais `Y1 … C2831465`).

**Résidu à confirmer avant commande.**
- **CL du cristal commandé** : régler `C8 = C9 = 2·(CL − Cstray)` (Cstray ≈ 2–3 pF).
  Ex. CL 8 pF → ~10–11 pF ; CL 10 pF → ~15 pF. Confirmer la CL de C2831465 sur la
  fiche JLC en direct puis ajuster C8/C9 (actuellement 10 pF, valeur générique).
- Vérifier la **disponibilité/stock** de C2831465 chez JLC au moment de commander
  (sinon prendre un autre 40 MHz SMD3225-4P, ex. CF4040M00012/C5765977).

---

## §5 — Straps de boot ESP32-P4 : **confirmé + pull-up GPIO36 ajouté**

**Vérifié** contre la doc officielle Espressif *Boot Mode Selection (ESP32-P4)*
([esptool docs](https://docs.espressif.com/projects/esptool/en/latest/esp32p4/advanced-topics/boot-mode-selection.html))
et la synthèse des straps
([espboards.dev](https://www.espboards.dev/blog/esp32-strapping-pins/)) :

- **GPIO35** sélectionne le mode : **bas = download (bootloader série)**, sinon
  **boot flash**. Il a un **pull-up interne faible** → au repos, boot depuis la
  flash. ✅ Le montage existant est correct : **SW2** (GPIO35→GND, bouton BOOT)
  + **R10 = 10 k** pull-up 3V3→GPIO35.
- ⚠️ **GPIO36 doit être HAUT** pour entrer **de façon fiable** en download, et la
  combinaison GPIO36 = 0 & GPIO35 = 0 est **invalide**. Or GPIO36 (broche 68) était
  **flottant** (défaut = flottant). Sans pull-up, maintenir BOOT peut ne pas
  entrer en download de manière fiable.

**Correction appliquée** : ajout de **R32 = 10 k** pull-up **3V3 → GPIO36**
(`design.py` ; broche 68 du P4 = net `GPIO36_STRAP`). Ajoutée au board committé
sans casser le routage (posée, à router à la finition). Aucun court pad-à-pad
(vérifié en `pcbnew`).
- GPIO37/GPIO38 (autres straps) servent ici de **console UART0** — usage normal.
- GPIO34 laissé **flottant** (son défaut) — conforme.

**Résidu** : aucun bloquant. R32 reste **à router** (2 liaisons) lors de la
finition (elle est dans le ratsnest).

---

## §6 — Caméra MIPI-CSI (FFC 15 broches) : **brochage confirmé conforme OV5647**

**Contexte firmware.** La cible caméra est explicitement l'**OV5647** — le driver
`espressif/esp_cam_sensor` et `firmware/main/video_task.c` (« MIPI-CSI camera
(OV5647 via esp_video) ») le confirment. L'OV5647 est le capteur de la
**Raspberry Pi Camera v1.3**, dont le FFC 15 broches est un standard bien documenté.

**Vérification** du brochage J4 (`design.py`) contre le FFC 15 broches
OV5647/RPi v1.3 ([Arducam 5MP OV5647](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/5MP-OV5647/),
[RPi camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html)) :

| Broche | J4 (design.py) | Standard OV5647/RPi v1.3 | OK |
|:--:|:--|:--|:--:|
| 1 | GND | GND | ✅ |
| 2 | CSI_D0N | Data0 − | ✅ |
| 3 | CSI_D0P | Data0 + | ✅ |
| 4 | GND | GND | ✅ |
| 5 | CSI_D1N | Data1 − | ✅ |
| 6 | CSI_D1P | Data1 + | ✅ |
| 7 | GND | GND | ✅ |
| 8 | CSI_CKN | Clock − | ✅ |
| 9 | CSI_CKP | Clock + | ✅ |
| 10 | GND | GND | ✅ |
| 11 | CAM_PWDN | contrôle capteur (reset/pwdn) | ✅ |
| 12 | CAM_GPIO | contrôle capteur (GPIO/clk-en) | ✅ |
| 13 | I2C_SCL | SCL | ✅ |
| 14 | I2C_SDA | SDA | ✅ |
| 15 | 3V3 | +3.3 V | ✅ |

→ Le brochage FFC **correspond** au standard OV5647 : ordre des lanes, position
des GND, alims et I²C conformes. Le point est **résolu au niveau connecteur**.

**Résidu (faible risque)** : la **polarité P/N** et l'**ordre des lanes** côté
**pads du P4** ne sont pas re-vérifiés contre le schéma de l'**ESP32-P4-EVK**
(bloqué par le proxy). Le mapping retenu (FFC D0± → P4 CSI_D0±, etc.) est le
mapping direct standard ; une inversion P/N éventuelle est en général corrigeable
**côté firmware** (config des lanes MIPI D-PHY). À confirmer contre le schéma
caméra de l'EVK P4 avant grande série ; pour un premier proto, le risque est
faible et rattrapable en logiciel.

---

## §14 — Empreinte USB-C : **confirmée conforme**

**Vérifié localement** (KiCad 7 installé) : `design.py` (J2) utilise l'empreinte
**officielle KiCad** `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` — c'est
la land du **part HRO TYPE-C-31-M-12** lui-même (LCSC C165948). Les pads de
l'empreinte (`A1,A4,A5,A6,A7,A8,A9,A12,B1,B4,B5,B6,B7,B8,B9,S1`) couvrent tous
ceux câblés par J2 ; les broches SBU (A8/B8) sont non connectées, ce qui est
correct pour un réceptacle **power + USB2 sink**. Pas de variante à contacts
miroir à craindre : l'empreinte suit le brochage du part.

**Résidu** : au moment de commander, vérifier que la **référence LCSC exacte**
commandée (C165948) est bien la variante 16 broches de ce boîtier (les catalogues
évoluent). Aucun changement de design requis.

---

## Récapitulatif

| Point | État | Action |
|-------|------|--------|
| §11 quartz | 🔴→🟢 **bug fatal corrigé** | C9002 (12 MHz) → C2831465 (40 MHz) ; régler C8/C9 selon CL |
| §5 boot straps | 🟢 confirmé + durci | R32 pull-up GPIO36 ajouté ; à router |
| §6 caméra CSI | 🟢 conforme OV5647 | résidu faible : polarité P/N côté P4 (rattrapable firmware) |
| §14 USB-C | 🟢 conforme | aucune action design |

Voir **[`ORDER_CHECKLIST.md`](ORDER_CHECKLIST.md)** pour la checklist finale
bloquante avant commande (dont le **routage** à terminer, qui reste le vrai
verrou — cf. `KNOWN_GAPS.md` §1).
