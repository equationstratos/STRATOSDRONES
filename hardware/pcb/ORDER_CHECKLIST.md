# STRATOSDRONE PCB — checklist AVANT de commander chez JLCPCB

À cocher **dans l'ordre**. Tant qu'une case « bloquant » n'est pas cochée, **ne
commande pas**. Détails : `VERIFY_RESOLVED.md`, `KNOWN_GAPS.md`,
`guide_kicad/13_mcp_et_finition.md`.

## ✅ Déjà fait (session automatisée)

- [x] **Quartz** : part LCSC corrigé **C9002 (12 MHz, fatal) → C2831465 (40 MHz)**
      dans `design.py` + `jlcpcb/bom.csv`. *(VERIFY_RESOLVED §11)*
- [x] **Strap boot** : **R32** (pull-up 10 k sur GPIO36) ajoutée au design et au
      board. *(VERIFY_RESOLVED §5)*
- [x] **Caméra** : brochage FFC vérifié **conforme OV5647** (cible firmware).
      *(VERIFY_RESOLVED §6)*
- [x] **USB-C** : empreinte = land officielle du part HRO commandé. *(§14)*
- [x] BOM/CPL régénérés, zones remplies, gerbers **préliminaires** exportés.

## 🔴 Bloquant — à finir sur ta machine (KiCad 9)

- [ ] **Router les ~108 liaisons restantes** (routeur interactif « shove » +
      autoroutage Freerouting). Chevelu (`F8`) **vide**. *(ch. 11 & 13)*
- [ ] **Router R32** (2 liaisons : GPIO36 ↔ 3V3) — elle est posée mais non routée.
- [ ] **Paires différentielles** (USB `USB_D±`, CSI `CSI_D0/D1/CK ±`) routées
      appairées, sur le stackup impédance JLC04161H-7628. *(ch. 11)*
- [ ] **Remplir les zones** (`B`) après routage.
- [ ] **DRC = 0 erreur** (KiCad **Inspecter → DRC**, ou via le MCP). Les
      « unconnected » doivent être à **0**.
- [ ] **Charges quartz C8/C9** = `2·(CL − Cstray)` pour la **CL réelle** de
      C2831465 (confirmer la CL sur JLC ; Cstray ≈ 2–3 pF). *(VERIFY_RESOLVED §11)*
- [ ] **Ré-exporter les gerbers depuis KiCad** (carte routée + zones remplies) —
      **pas** depuis `export_fab.py` (qui exporte le préliminaire). *(ch. 12)*

## 🟠 À confirmer (physique / catalogue)

- [ ] **Rotations CPL** des composants sensibles vérifiées vs `cpl.csv` :
      **U8 VL53L1X**, **J2 USB-C**, **U1 P4 (QFN)**, **U6 IMU** — une rotation JLC
      erronée = pose de travers.
- [ ] **Stock LCSC** au moment de commander : Y1 **C2831465** (40 MHz) et les
      parts critiques (P4 C22387510, C6 C3013606, IMU C2840095) **en stock** ;
      sinon substituer et re-vérifier.
- [ ] **Caméra** : polarité P/N CSI côté P4 — à valider au bench (rattrapable
      firmware) avant d'en dépendre. *(VERIFY_RESOLVED §6)*
- [ ] `U9` (PMW3901) **ou** `J3` (module CJMCU-3901) — poser **l'un** des deux,
      pas les deux. *(KNOWN_GAPS §9)*
- [ ] `D2` (SS34 bench-power) **non posée** si une batterie est installée.
      *(KNOWN_GAPS §7)*

## ⚙️ Options de commande JLCPCB

- [ ] PCB **4 couches**, 1.6 mm, stackup **JLC04161H-7628** (impédance USB/CSI),
      finition **ENIG**.
- [ ] Assemblage **PCBA double face** ; upload `jlcpcb/bom.csv` + `jlcpcb/cpl.csv`.
- [ ] `make check` (consistance board == design == firmware) **vert**.

---

**En clair** : les correctifs design (dont le **bug fatal du quartz**) et la
vérification sont faits ; il te reste **le routage final + DRC = 0 + les
confirmations physiques**. C'est cette dernière ligne droite, sur ta machine, qui
rend la carte **réellement** prête à commander.
