# 06 — Schéma : moteurs + LEDs + IO (27 composants)

Dernier bloc du schéma : les 4 étages moteurs, les LEDs d'état et les connecteurs.

> 📄 Fiche **[fiches/blocs.md](fiches/blocs.md)**, section « Bloc 06 — MOTEURS +
> LEDS + IO ».

## 1. Les 4 étages moteurs (i = 1 à 4)

Chaque moteur brushed est piloté par un **NFET low-side** avec diode de roue
libre. Motif **identique** pour M1…M4 (change juste l'indice) :

- **Q1–Q4 = AO3400A** (SOT-23) : 1 = Drain (`Mi_D`), 2 = Source (`GND`),
  3 = Gate (`Mi_GATE`).
- **R22–R25 = 100 Ω** : résistance **série de grille** entre `Mi_G` (venant du P4)
  et `Mi_GATE`.
- **R26–R29 = 100 kΩ** : **pull-down de grille** (`Mi_GATE`→GND) → hélices à
  l'arrêt au boot.
- **D3–D6 = SS34** : diode **flyback**, cathode (pin 1) sur `VBAT`, anode (pin 2)
  sur `Mi_D`.
- **J5–J8 = header 1×2** : pads du moteur, pin 1 `VBAT`, pin 2 `Mi_D`.

Correspondance indice → composants (fiche) :

| Moteur | FET | R série | R pull-down | Flyback | Pads |
|--------|-----|---------|-------------|---------|------|
| M1 | Q1 | R22 | R26 | D3 | J5 |
| M2 | Q2 | R23 | R27 | D4 | J6 |
| M3 | Q3 | R24 | R28 | D5 | J7 |
| M4 | Q4 | R25 | R29 | D6 | J8 |

> Les nets `M1_G`…`M4_G` viennent du P4 (GPIO45–48, ch. 03).

## 2. LEDs d'état WS2812B (LED1, LED2)

- Empreinte : `LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm`.
- **Chaînées** : LED1 pin2 `LED_DIN` (data in, du P4) → LED1 pin4 `LED_D12`
  (data out) → LED2 pin2 `LED_D12` → LED2 pin4 `LED_DOUT` (fin de chaîne).
- Alim des deux : pin1 `VBAT`, pin3 `GND`.
- **C34 = C35 = 100 nF** (VBAT/GND) de découplage.
  > Alimentées en **VBAT** (1S) : le niveau data 3.3 V est marginal-mais-standard
  > pour les whoops 1S (`KNOWN_GAPS.md` §15). OK en pratique.

## 3. Connecteurs extension + debug

- **J9 = EXP** (1×6, pas 1.27 mm) : `3V3`, `GND`, `VBAT`, `I2C_SDA`, `I2C_SCL`,
  `EXP_IO` — connecteur d'extension (deck).
- **J10 = DBG** (1×4) : console UART0 du **P4** : `GND`, `U0TXD`, `U0RXD`, `3V3`.
- **J11 = C6DBG** (1×4) : flash/console du **C6** : `GND`, `C6_U0TXD`, `C6_U0RXD`,
  `C6_BOOT`.

## Schéma terminé — auto-contrôle

Tu as posé les 5 blocs (02→06). Total attendu : **112 composants**. Vérifie vite :

- Nets « sources » d'alim (`VBAT`, `VBUS`, `3V3`, `GND`, `VDD_CORE`, `VDD_MIPI`)
  ont bien un **PWR_FLAG**.
- Les 6 nets à une seule broche sont **normaux** (points de test / à vérifier) :
  `CAM_GPIO`, `CHRG_N`, `GPIO0`, `LED_DOUT`, `STDBY_N`, `TOF_INT`
  (voir l'avertissement en tête de **[fiches/nets.md](fiches/nets.md)**).

➡️ On passe à l'ERC et aux empreintes :
**[07_erc_et_empreintes.md](07_erc_et_empreintes.md)**
