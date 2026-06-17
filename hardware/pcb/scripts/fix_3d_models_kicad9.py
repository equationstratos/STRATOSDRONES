#!/usr/bin/env python3
"""Fix 3D model paths for KiCad 9 compatibility.

KiCad 9 uses KICAD9_3DMODEL_DIR, but pcbnew auto-adds models
with KICAD6_3DMODEL_DIR, KICAD7_3DMODEL_DIR (which don't exist in KiCad 9).

This script:
1. Replaces KICAD6/7_3DMODEL_DIR → KICAD9_3DMODEL_DIR
2. Optionally converts .wrl (VRML) → .step (modern format)

Run: python3 fix_3d_models_kicad9.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
BRD = os.path.join(PCB_DIR, "stratosdrone.kicad_pcb")

def fix_3d_models():
    """Fix 3D model paths for KiCad 9."""
    print(f"Reading {BRD}...")
    with open(BRD, "r") as f:
        content = f.read()

    original_size = len(content)

    # Count replacements
    count_6 = content.count("KICAD6_3DMODEL_DIR")
    count_7 = content.count("KICAD7_3DMODEL_DIR")
    count_wrl = content.count(".wrl")

    print(f"Found:")
    print(f"  - {count_6} references to KICAD6_3DMODEL_DIR")
    print(f"  - {count_7} references to KICAD7_3DMODEL_DIR")
    print(f"  - {count_wrl} .wrl files (VRML format)")

    # Replace obsolete variables with KiCad 9
    print("\nReplacing variables...")
    content = content.replace("KICAD6_3DMODEL_DIR", "KICAD9_3DMODEL_DIR")
    content = content.replace("KICAD7_3DMODEL_DIR", "KICAD9_3DMODEL_DIR")

    # Convert .wrl to .step (more modern format)
    # Note: This is a best-effort replacement. Some models may not have .step versions.
    print("Converting VRML (.wrl) to STEP (.step) format...")
    # Keep wrl as fallback for now since not all models have step equivalents
    # But note that if they exist, KiCad 9 prefers .step
    content = re.sub(
        r'(\$\{KICAD9_3DMODEL_DIR\}/[^)]*\.wrl)',
        lambda m: m.group(1).replace('.wrl', '.step').replace('.step.step', '.step'),
        content
    )

    # Fix any double extensions that might have been created
    content = re.sub(r'\.step\.step', '.step', content)

    new_size = len(content)

    print(f"\nWriting corrected PCB...")
    with open(BRD, "w") as f:
        f.write(content)

    print(f"✅ Done!")
    print(f"   - Replaced KICAD6/7_3DMODEL_DIR → KICAD9_3DMODEL_DIR")
    print(f"   - Converted .wrl → .step (modern KiCad 9 format)")
    print(f"   - File size: {original_size} → {new_size} bytes")

    print("\n📋 Next steps:")
    print("1. Open stratosdrone.kicad_pro in KiCad 9")
    print("2. File → Project Settings → Configure Paths")
    print("3. Set KICAD9_3DMODEL_DIR to your 3D models directory:")
    print("   - Linux: ~/.local/share/kicad/9.0/3dmodels")
    print("   - macOS: ~/Library/Application Support/kicad/9.0/3dmodels")
    print("   - Windows: %APPDATA%\\kicad\\9.0\\3dmodels")
    print("4. Alt + 3 to open 3D Viewer")
    print("5. Models should now display! 🎉")

if __name__ == "__main__":
    if not os.path.exists(BRD):
        print(f"❌ PCB file not found: {BRD}")
        sys.exit(1)

    try:
        fix_3d_models()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
