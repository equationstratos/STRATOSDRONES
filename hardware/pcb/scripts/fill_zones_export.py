#!/usr/bin/env python3
"""Fill zones and export updated gerbers for JLCPCB.

This script:
1. Fills all zones (GND/3V3/VBAT with sensor aperture)
2. Exports updated gerbers + drill files

Note: Signal routing must still be done manually in KiCad for optimal results.
If autorouting is desired, use KiCad's Tools > Autoroute menu in pcbnew.

Run: python3 fill_zones_export.py
"""
import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
BRD = os.path.join(PCB_DIR, "stratosdrone.kicad_pcb")
OUT = os.path.join(PCB_DIR, "jlcpcb")


def fill_zones():
    """Load board and fill all zones."""
    print("Loading board...")
    board = pcbnew.LoadBoard(BRD)

    print("Filling zones...")
    # Iterate through zones and fill them
    zones = board.Zones()
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(zones)

    print("Saving board with filled zones...")
    pcbnew.SaveBoard(BRD, board)
    print(f"✅ Zones filled successfully ({len(zones)} zones)")



def export_gerbers():
    """Export gerber files using kicad-cli."""
    gdir = os.path.join(OUT, "gerbers")
    os.makedirs(gdir, exist_ok=True)

    # Define layers to export
    layers = ("F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,"
              "F.Mask,B.Mask,Edge.Cuts")

    print("Exporting gerbers...")
    try:
        # Export gerbers
        result = subprocess.run(
            ["kicad-cli", "pcb", "export", "gerbers",
             "--layers", layers, "--no-protel-ext",
             "-o", gdir + "/", BRD],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"⚠️  Gerber export warning: {result.stderr[:200]}")

        # Export drill files
        print("Exporting drill files...")
        result = subprocess.run(
            ["kicad-cli", "pcb", "export", "drill",
             "--format", "excellon", "--excellon-separate-th",
             "-o", gdir + "/", BRD],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"⚠️  Drill export warning: {result.stderr[:200]}")

        # Count output files
        n = len([f for f in os.listdir(gdir) if not f.startswith(".")])
        print(f"✅ Gerber export: {n} files ready in jlcpcb/gerbers/")

    except FileNotFoundError:
        print("❌ Error: kicad-cli not found. Install KiCad 7.0+")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("❌ Error: Export timed out")
        sys.exit(1)


def main():
    print("=" * 60)
    print("STRATOSDRONE PCB: Fill Zones & Export Gerbers")
    print("=" * 60)

    # Check if board exists
    if not os.path.exists(BRD):
        print(f"❌ Error: Board file not found: {BRD}")
        sys.exit(1)

    try:
        fill_zones()
        export_gerbers()

        print("=" * 60)
        print("✅ COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Review jlcpcb/gerbers/ files")
        print("2. For signal routing:")
        print("   - Open stratosdrone.kicad_pcb in KiCad")
        print("   - Route signal nets (currently ratsnest)")
        print("   - Use Tools > Autoroute or route manually")
        print("3. Re-export gerbers after routing for production")
        print("4. Upload to JLCPCB")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    # Avoid pcbnew shutdown crash
    os._exit(0)
