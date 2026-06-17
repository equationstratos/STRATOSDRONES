#!/usr/bin/env python3
"""Generate interactive PCB visualization in HTML."""
import os
import json
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BRD = os.path.join(HERE, "stratosdrone.kicad_pcb")
OUT = os.path.join(HERE, "pcb_viewer.html")

def generate_visualization():
    """Generate HTML/SVG visualization of PCB layout."""
    board = pcbnew.LoadBoard(BRD)

    # Get board dimensions
    bbox = board.ComputeBoundingBox()
    width_mm = pcbnew.ToMM(bbox.GetWidth())
    height_mm = pcbnew.ToMM(bbox.GetHeight())

    # Scale for display (100px = 10mm)
    scale = 10
    svg_width = width_mm * scale
    svg_height = height_mm * scale

    # Collect component data
    components = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        value = fp.GetValue()

        # Get position
        pos = fp.GetPosition()
        x = pcbnew.ToMM(pos.x)
        y = pcbnew.ToMM(pos.y)

        # Get bounding box
        fbox = fp.GetBoundingBox()
        w = pcbnew.ToMM(fbox.GetWidth())
        h = pcbnew.ToMM(fbox.GetHeight())

        # Layer (top/bottom)
        layer = "bottom" if fp.IsFlipped() else "top"

        # Highlight important components
        color = "#999"
        if ref.startswith("U"):  # ICs
            color = "#f44"
        elif ref in ["U8", "U9"]:  # Sensors
            color = "#4f4"
        elif ref.startswith("J"):  # Connectors
            color = "#44f"
        elif ref.startswith("L"):  # Inductors
            color = "#ff4"

        components.append({
            "ref": ref,
            "value": value,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "layer": layer,
            "color": color,
            "rotation": fp.GetOrientationDegrees()
        })

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STRATOSDRONE PCB Layout Viewer</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1e1e1e;
            color: #ccc;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #fff;
            margin-bottom: 20px;
            font-size: 24px;
        }}
        .info {{
            background: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            border-left: 4px solid #4f8;
        }}
        .info p {{ margin: 5px 0; }}
        .viewer-container {{
            background: #0a0a0a;
            border: 2px solid #444;
            border-radius: 8px;
            overflow: auto;
            max-width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 600px;
            position: relative;
        }}
        svg {{
            background: #1a1a1a;
            border: 1px solid #333;
        }}
        .component {{
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .component:hover {{
            opacity: 0.8;
        }}
        .component text {{
            font-size: 8px;
            pointer-events: none;
            fill: #fff;
            text-anchor: middle;
            dominant-baseline: middle;
        }}
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 30px;
            background: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 1px solid #666;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #4f8;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #4f8;
        }}
        .stat-label {{
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ STRATOSDRONE PCB Layout</h1>

        <div class="info">
            <p><strong>Board Dimensions:</strong> {width_mm:.1f} × {height_mm:.1f} mm</p>
            <p><strong>Components:</strong> {len(components)} placed</p>
            <p><strong>Status:</strong> Zones filled ✓ | Signal routing pending</p>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{width_mm:.0f}×{height_mm:.0f}</div>
                <div class="stat-label">mm (Board Size)</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(components)}</div>
                <div class="stat-label">Components</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">4</div>
                <div class="stat-label">Zones (Filled)</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">14</div>
                <div class="stat-label">Gerber Files</div>
            </div>
        </div>

        <div class="viewer-container">
            <svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">
                <!-- PCB outline -->
                <rect x="0" y="0" width="{svg_width}" height="{svg_height}"
                      fill="#1a1a1a" stroke="#444" stroke-width="1"/>

                <!-- Component placements -->
"""

    # Add components to SVG
    for comp in components:
        x = comp["x"] * scale
        y = comp["y"] * scale
        w = comp["w"] * scale
        h = comp["h"] * scale

        # Rectangle for component
        html += f"""                <g class="component" title="{comp['ref']}: {comp['value']}">
                    <rect x="{x - w/2}" y="{y - h/2}" width="{w}" height="{h}"
                          fill="{comp['color']}" stroke="#555" stroke-width="0.5" opacity="0.7"/>
                    <text x="{x}" y="{y}" font-size="7">{comp['ref']}</text>
                </g>
"""

    html += """            </svg>
        </div>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #f44;"></div>
                <span>ICs (U1–U10)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #4f4;"></div>
                <span>Sensors (U8, U9)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #44f;"></div>
                <span>Connectors (J)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ff4;"></div>
                <span>Inductors (L)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #999;"></div>
                <span>Passives (R, C, D)</span>
            </div>
        </div>

        <div style="margin-top: 30px; padding: 20px; background: #2d2d2d; border-radius: 8px; border-left: 4px solid #ff4;">
            <strong>📋 Next Steps:</strong>
            <ol style="margin-left: 20px; margin-top: 10px; line-height: 1.8;">
                <li>Open <code>stratosdrone.kicad_pcb</code> in KiCad 7.0+</li>
                <li>Route signal nets (Tools > Autoroute or manual routing)</li>
                <li>Verify clearances and traces</li>
                <li>Re-export gerbers from KiCad</li>
                <li>Upload to JLCPCB for fabrication</li>
            </ol>
        </div>
    </div>
</body>
</html>"""

    with open(OUT, "w") as f:
        f.write(html)

    print(f"✅ PCB viewer generated: {OUT}")
    print(f"   Components: {len(components)}")
    print(f"   Board: {width_mm:.1f} × {height_mm:.1f} mm")

if __name__ == "__main__":
    generate_visualization()
