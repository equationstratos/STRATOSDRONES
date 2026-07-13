#!/usr/bin/env python3
"""Génère les fiches de référence du guide KiCad depuis design.py.

Source de vérité UNIQUE : ../../scripts/design.py. Ce script n'écrit AUCUNE
valeur/empreinte à la main : il importe `design`, réutilise
`design.all_components()` + `design.BOARD`, regroupe les composants par bloc
fonctionnel (les mêmes sections que le guide, chapitres 02→06) et écrit :

    composants.md   tableau complet (ref, valeur, empreinte, LCSC, face, DNP)
    nets.md         netlist : chaque net -> liste (ref, pad)
    blocs.md        par bloc/sous-bloc : composants + câblage pin->net
    empreintes.md   empreintes uniques + bibliothèque source
    bom.md          BOM (composants posés avec code LCSC) + quantités

Re-lancer après toute édition de design.py :  python3 gen_reference.py

Le script est AUTO-VÉRIFIANT : il s'arrête (assert) si un composant de
design.py n'est pas classé dans exactement un bloc — c'est le garde-fou qui
garantit que le guide couvre 100 % de la carte.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "..", "scripts"))
sys.path.insert(0, SCRIPTS)
import design  # noqa: E402

C = list(design.all_components())
BY_REF = {c["ref"]: c for c in C}


# --------------------------------------------------------------------------
# Découpage en blocs fonctionnels (= chapitres 02→06 du guide).
# Chaque sous-bloc = (titre, [refs]). L'ordre suit celui du câblage conseillé.
# --------------------------------------------------------------------------
def _r(prefix, lo, hi):
    return [f"{prefix}{i}" for i in range(lo, hi + 1)]


BLOCKS = [
    ("02", "ALIMENTATION", "02_schema_alimentation.md", [
        ("Entrée batterie + USB-C + charge TP4056",
         ["J1", "J2", "R1", "R2", "D1", "U4", "R3", "C1", "C2", "D2"]),
        ("Buck 3V3 (SY8089)",
         ["U5", "L1", "C3", "C4", "R4", "R5", "R6"]),
        ("DC-DC cœur ~1.2V (TLV62569)",
         ["U10", "L2", "C5", "C36", "C37", "R30", "R31"]),
        ("Diviseur VBAT -> ADC",
         ["R7", "R8", "C6"]),
        ("Découplage des rails LDO internes du P4",
         ["C7", "C42", "C38", "C39", "C40", "C41"]),
    ]),
    ("03", "MCU ESP32-P4 + FLASH", "03_schema_mcu_p4_flash.md", [
        ("MCU ESP32-P4 (U1) + flash QSPI (U2)",
         ["U1", "U2"]),
        ("Quartz 40 MHz / reset / boot / REXT",
         ["Y1", "C8", "C9", "R9", "C10", "SW1", "SW2", "R10", "R11", "R12"]),
        ("Pull-ups flash QSPI",
         ["R13", "R14", "R15"]),
        ("Pull-ups SDIO (bus vers le C6)",
         _r("R", 16, 20)),
        ("Pull-up boot du C6",
         ["R21"]),
        ("Découplage P4 + bulk",
         ["C11"] + _r("C", 12, 27)),
    ]),
    ("04", "Wi-Fi ESP32-C6", "04_schema_c6_wifi.md", [
        ("Co-processeur Wi-Fi (esp-hosted, esclave SDIO)",
         ["U3"]),
    ]),
    ("05", "CAPTEURS + CAMÉRA", "05_schema_capteurs_camera.md", [
        ("IMU ICM-42688-P (SPI)",
         ["U6", "C28", "C29"]),
        ("Baromètre SPL06-001 (I²C 0x76)",
         ["U7", "C30"]),
        ("ToF VL53L1X (I²C 0x29, dessous)",
         ["U8", "C31"]),
        ("Flux optique PMW3901 (SPI, dessous) + header de repli",
         ["U9", "C32", "J3"]),
        ("Caméra MIPI-CSI (FFC 15 broches)",
         ["J4", "C33"]),
    ]),
    ("06", "MOTEURS + LEDS + IO", "06_schema_moteurs_leds_io.md", [
        ("4 drivers moteurs (NFET low-side + flyback + pads)",
         _r("Q", 1, 4) + _r("R", 22, 29) + _r("D", 3, 6) + _r("J", 5, 8)),
        ("LEDs d'état WS2812B",
         ["LED1", "LED2", "C34", "C35"]),
        ("Extension + debug",
         ["J9", "J10", "J11"]),
    ]),
]


def _check_coverage():
    seen = {}
    for _, _, _, subs in BLOCKS:
        for _, refs in subs:
            for r in refs:
                assert r in BY_REF, f"bloc référence un ref inconnu: {r}"
                assert r not in seen, f"{r} classé dans 2 blocs"
                seen[r] = True
    missing = [c["ref"] for c in C if c["ref"] not in seen]
    assert not missing, f"composants non classés dans un bloc: {missing}"


# --------------------------------------------------------------------------
# Netlist
# --------------------------------------------------------------------------
def build_nets():
    nets = {}
    for c in C:
        for pad, net in c["pins"].items():
            nets.setdefault(net, []).append((c["ref"], pad))
    return nets


# --------------------------------------------------------------------------
# Rendu Markdown
# --------------------------------------------------------------------------
def _side(c):
    return "Dessous (B)" if c.get("side") == "B" else "Dessus (T)"


def _dnp(c):
    return "DNP (non posé)" if not c.get("populate", True) else "posé"


HEADER = ("<!-- Fiche générée par fiches/gen_reference.py depuis "
          "scripts/design.py — NE PAS éditer à la main. -->\n\n")


def write_composants():
    lines = [HEADER, "# Fiche — Liste des composants\n",
             f"\n{len(C)} composants (source : `scripts/design.py`).\n\n",
             "| Ref | Valeur | Empreinte | LCSC | Face | Pose | Rôle |\n",
             "|-----|--------|-----------|------|------|------|------|\n"]
    def key(c):
        r = c["ref"]
        import re
        m = re.match(r"([A-Za-z]+)(\d+)", r)
        return (m.group(1), int(m.group(2)))
    for c in sorted(C, key=key):
        lines.append("| {ref} | {val} | `{fp}` | {lcsc} | {side} | {dnp} | {cm} |\n".format(
            ref=c["ref"], val=c["value"], fp=c["fp"],
            lcsc=c["lcsc"] or "—", side=_side(c), dnp=_dnp(c),
            cm=(c.get("comment") or "").replace("|", "\\|")))
    _write("composants.md", lines)


def write_nets():
    nets = build_nets()
    single = sorted(n for n, v in nets.items() if len(v) == 1)
    lines = [HEADER, "# Fiche — Netlist (noms de nets à respecter)\n",
             f"\n{len(nets)} nets distincts. **Utilise ces noms exacts en "
             "labels globaux** dans le schéma : c'est ce qui garantit que ton "
             "netlist correspond à celui de la carte du repo.\n\n"]
    lines.append("> ⚠️ Nets à une seule broche (à vérifier / points de test, "
                 "normal ici) : " + ", ".join(f"`{n}`" for n in single) + "\n\n")
    lines.append("| Net | Broches (ref.pad) |\n|-----|-------------------|\n")
    for net in sorted(nets):
        pads = ", ".join(f"{r}.{p}" for r, p in
                         sorted(nets[net], key=lambda x: x[0]))
        lines.append(f"| `{net}` | {pads} |\n")
    _write("nets.md", lines)


def write_blocs():
    _check_coverage()
    lines = [HEADER, "# Fiche — Câblage par bloc fonctionnel\n",
             "\nPour chaque bloc : les composants à poser puis, pour chacun, "
             "le câblage **broche → net**. Câble chaque broche à un **label de "
             "net global** portant le nom indiqué (colonne Net). Les broches "
             "d'un même net partagent donc le même label — pas besoin de tirer "
             "un fil d'un bout à l'autre de la feuille.\n"]
    for num, title, chap, subs in BLOCKS:
        nrefs = sum(len(refs) for _, refs in subs)
        lines.append(f"\n## Bloc {num} — {title}  ({nrefs} composants)\n")
        lines.append(f"\nChapitre du guide : `{chap}`\n")
        for subtitle, refs in subs:
            lines.append(f"\n### {subtitle}\n\n")
            for r in refs:
                c = BY_REF[r]
                tag = "" if c.get("populate", True) else "  _(DNP)_"
                side = "  _(dessous)_" if c.get("side") == "B" else ""
                lines.append(f"- **{r}** — {c['value']} · `{c['fp']}`"
                             f"{(' · LCSC ' + c['lcsc']) if c['lcsc'] else ''}"
                             f"{side}{tag}\n")
                pins = c["pins"]
                def pk(k):
                    return (0, int(k)) if str(k).isdigit() else (1, str(k))
                cable = " · ".join(f"{p}→`{pins[p]}`"
                                   for p in sorted(pins, key=pk))
                lines.append(f"  - Câblage : {cable}\n")
    _write("blocs.md", lines)


def write_empreintes():
    fps = {}
    for c in C:
        fps.setdefault(c["fp"], []).append(c["ref"])
    vendored = {
        "strat:ESP32-P4": "Vendored — fichier dans `lib/Espressif.pretty/ESP32-P4.kicad_mod` (nickname KiCad conseillé : `Espressif`)",
        "strat:ESP32-C6-MINI-1": "Vendored — `lib/Espressif.pretty/ESP32-C6-MINI-1.kicad_mod` (nickname `Espressif`)",
        "strat:PMW3901MB-TXQT": "Vendored — `lib/strat.pretty/PMW3901MB-TXQT.kicad_mod` (nickname `strat`)",
    }
    lines = [HEADER, "# Fiche — Empreintes (footprints)\n",
             f"\n{len(fps)} empreintes distinctes. Celles préfixées d'une "
             "bibliothèque KiCad standard (`Resistor_SMD`, `Package_SO`, …) sont "
             "installées avec KiCad. Trois sont **vendored** dans le repo (voir "
             "chapitre `01_projet_et_librairies.md`).\n\n",
             "| Empreinte | Source | Composants |\n"
             "|-----------|--------|------------|\n"]
    for fp in sorted(fps):
        src = vendored.get(fp, "KiCad standard")
        refs = ", ".join(sorted(fps[fp]))
        lines.append(f"| `{fp}` | {src} | {refs} |\n")
    _write("empreintes.md", lines)


def write_bom():
    bom = [c for c in C if c.get("populate", True) and c["lcsc"]]
    # regroupe par (valeur, empreinte, lcsc)
    groups = {}
    for c in bom:
        k = (c["value"], c["fp"], c["lcsc"])
        groups.setdefault(k, []).append(c["ref"])
    lines = [HEADER, "# Fiche — BOM (nomenclature)\n",
             f"\n{len(bom)} composants posés avec code LCSC, regroupés en "
             f"{len(groups)} lignes d'achat. (Les composants DNP — non posés — "
             "sont exclus, comme dans `jlcpcb/bom.csv`.)\n\n",
             "| Qté | Valeur | Empreinte | LCSC | Références |\n"
             "|-----|--------|-----------|------|------------|\n"]
    for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda x: -len(x[1])):
        lines.append(f"| {len(refs)} | {val} | `{fp}` | {lcsc} | "
                     f"{', '.join(sorted(refs))} |\n")
    _write("bom.md", lines)


def _write(name, lines):
    path = os.path.join(HERE, name)
    with open(path, "w") as f:
        f.write("".join(lines))
    print(f"  écrit  {name}")


def main():
    _check_coverage()
    nets = build_nets()
    bom = [c for c in C if c.get("populate", True) and c["lcsc"]]
    write_composants()
    write_nets()
    write_blocs()
    write_empreintes()
    write_bom()
    print("\nTotaux (doivent correspondre à `python3 scripts/design.py`) :")
    print(f"  composants       : {len(C)}")
    print(f"  nets distincts   : {len(nets)}")
    print(f"  lignes BOM LCSC  : {len(bom)}")


if __name__ == "__main__":
    main()
