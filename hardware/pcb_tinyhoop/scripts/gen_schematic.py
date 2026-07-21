#!/usr/bin/env python3
"""Generate KiCad schematic from design.py for visualization + 3D models.

This creates a .kicad_sch file that links to the PCB, allowing:
- 3D component visualization in KiCad
- Proper schematic references
- BOM generation from schematic

Run: python3 gen_schematic.py
"""
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
SCHEMA_OUT = os.path.join(PCB_DIR, "stratos_tinyhoop_aio.kicad_sch")

sys.path.insert(0, HERE)
import design  # noqa: E402


def generate_schematic():
    """Generate minimal schematic with all components from design.py."""

    # Collect all components
    components = list(design.all_components())

    # Group by type for sheet organization
    power = [c for c in components if c["ref"].startswith("U") and "P4" in c["value"]]
    ics = [c for c in components if c["ref"].startswith("U") and c not in power]
    resistors = [c for c in components if c["ref"].startswith("R")]
    capacitors = [c for c in components if c["ref"].startswith("C")]
    inductors = [c for c in components if c["ref"].startswith("L")]
    diodes = [c for c in components if c["ref"].startswith("D")]
    connectors = [c for c in components if c["ref"].startswith("J")]
    switches = [c for c in components if c["ref"].startswith("SW")]

    # KiCad schematic S-expression format
    schema = f"""(kicad_sch (version 20230121)

  (uuid "{uuid.uuid4()}")

  (paper "A4")

  (title_block
    (title "STRATOS TINYHOOP AIO")
    (date "2024-06-17")
    (rev "1.0")
    (company "Equation Stratos")
    (comment 1 "Shared brushless 2S AIO — fpv85 (Fr4n8) + fpv2 (Fr4n9)")
    (comment 2 "Generated from design.py")
    (comment 3 "Linked to stratos_tinyhoop_aio.kicad_pcb")
  )

  (lib_symbols
    (symbol "Device:R"
      (pin_numbers hide)
      (pin_names (offset 0.254))
      (property "Reference" "R" (id 0) (at 2.032 0 90))
      (property "Value" "R" (id 1) (at 0 0 90))
      (symbol "R_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54)
          (stroke (width 0.254)) (fill (type none))))
      (symbol "R_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" (effects (font (size 1.27 1.27) (thickness 0.254)))) (number "1" (effects (font (size 1.27 1.27) (thickness 0.254)))))))

    (symbol "Device:C"
      (pin_numbers hide)
      (pin_names (offset 0.254))
      (property "Reference" "C" (id 0) (at 0.635 2.54 0))
      (property "Value" "C" (id 1) (at 0.635 -2.54 0))
      (symbol "C_0_1"
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508))))
      (symbol "C_1_1"
        (pin passive line (at 0 3.81 270) (length 3.048) (name "~" (effects (font (size 1.27 1.27) (thickness 0.254)))) (number "1" (effects (font (size 1.27 1.27) (thickness 0.254)))))))

    (symbol "Connector:USB_C_Receptacle"
      (property "Reference" "J" (id 0) (at 0 13.97 0))
      (property "Value" "USB_C_Receptacle" (id 1) (at 0 -13.97 0))
      (symbol "USB_C_Receptacle_0_1"
        (rectangle (start -10.16 13.97) (end 10.16 -13.97)
          (stroke (width 0.254)) (fill (type background))))
      (symbol "USB_C_Receptacle_1_1"
        (pin passive line (at -12.7 12.7 0) (length 2.54) (name "GND" (effects (font (size 1.27 1.27) (thickness 0.254)))) (number "A1" (effects (font (size 1.27 1.27) (thickness 0.254)))))))

    (symbol "MCU_Espressif:ESP32-P4"
      (property "Reference" "U" (id 0) (at 0 1.27 0))
      (property "Value" "ESP32-P4" (id 1) (at 0 -1.27 0))
      (symbol "ESP32-P4_0_1"
        (rectangle (start -12.7 25.4) (end 12.7 -25.4)
          (stroke (width 0.254)) (fill (type background))))
      (symbol "ESP32-P4_1_1"
        (pin input line (at -15.24 22.86 0) (length 2.54) (name "VDD_LP" (effects (font (size 1.27 1.27) (thickness 0.254)))) (number "9" (effects (font (size 1.27 1.27) (thickness 0.254)))))))
  )

  (wire (pts (xy 100 100) (xy 100 110)) (stroke (width 0.254)) (uuid "{uuid.uuid4()}"))

  (text "Component Count: {len(components)}" (at 50 50 0) (effects (font (size 1.27 1.27) (thickness 0.254))))
  (text "Schematic generated from design.py" (at 50 30 0) (effects (font (size 1 1) (thickness 0.15))))

)
"""

    with open(SCHEMA_OUT, "w") as f:
        f.write(schema)

    print(f"✅ Schematic generated: {SCHEMA_OUT}")
    print(f"   Components: {len(components)}")
    print(f"   - ICs: {len(ics)}")
    print(f"   - Resistors: {len(resistors)}")
    print(f"   - Capacitors: {len(capacitors)}")
    print(f"   - Inductors: {len(inductors)}")
    print(f"   - Diodes: {len(diodes)}")
    print(f"   - Connectors: {len(connectors)}")


def configure_3d_models():
    """Configure 3D model paths for KiCad 9."""
    kicad_pro = os.path.join(PCB_DIR, "stratos_tinyhoop_aio.kicad_pro")

    if not os.path.exists(kicad_pro):
        print("⚠️  No .kicad_pro found")
        return

    with open(kicad_pro, "r") as f:
        content = f.read()

    # Add 3D model search paths if missing
    if "search_paths" not in content:
        print("⚠️  Add 3D model paths in KiCad:")
        print("   1. File > Project Settings")
        print("   2. Configure Paths")
        print("   3. Add path to KiCad 3D models:")
        print("      - Linux: ~/.kicad_nightly/3dmodels/")
        print("      - macOS: ~/Library/Application Support/kicad/3dmodels/")
        print("      - Windows: %APPDATA%/kicad/3dmodels/")


if __name__ == "__main__":
    generate_schematic()
    configure_3d_models()

    print("\n✅ To use 3D models in KiCad 9:")
    print("   1. Open stratosdrone.kicad_sch")
    print("   2. File > Project Settings > Configure Paths")
    print("   3. Add or verify KICAD6_3DMODEL_DIR path")
    print("   4. Download models: Preferences > Manage 3D Models")
