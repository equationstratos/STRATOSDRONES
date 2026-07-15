#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STRATOSDRONE PCB — self-contained Three.js 3-D populated-board viewer.

Reads the board (``stratosdrone.kicad_pcb``) + the design database
(``scripts/design.py``) and SYNTHESISES a clean 3-D body for every one of the
115 components from Three.js primitives — so the board renders FULLY POPULATED
even though KiCad has no 3-D model for 6 of the parts and none of the board's
``${KICAD9_3DMODEL_DIR}`` .step references resolve on this machine.

Why this exists: no ``kicad-cli`` / ``pcbnew`` / stock 3-D models are available,
so the usual "export STEP/glTF" path is impossible. Building each body from a
footprint→archetype table sidesteps the missing models entirely.

Offline: Three.js r160 is inlined (base64) from ``sim/viz/vendor``; reference
designators are drawn as canvas-textured Sprites (the only fully-offline text
path). Output: ``pcb3d_viewer.html`` (one file, open by double-click).

Run:  python3 hardware/pcb/viz/gen_pcb3d.py
"""
import base64
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.dirname(HERE)                        # hardware/pcb
REPO = os.path.dirname(os.path.dirname(PCB))       # repo root
VENDOR = os.path.join(REPO, "sim", "viz", "vendor")
BRD = os.path.join(PCB, "stratosdrone.kicad_pcb")
OUT = os.path.join(HERE, "pcb3d_viewer.html")

sys.path.insert(0, os.path.join(PCB, "scripts"))
import design  # noqa: E402   (component database; no pcbnew)
import add_logo  # noqa: E402  (logo vector geometry; inject() only runs under __main__)

# --------------------------------------------------------------------------
# Subsystem colours + human-readable roles.
# Copied from scripts/gen_component_map.py (which we CANNOT import — it does
# `import pcbnew`). U10 (P4 core DC-DC) added to Power.
# --------------------------------------------------------------------------
SUBSYS = {
    "MCU / Wi-Fi":     (["U1", "U2", "U3", "Y1"], "#3b6fb6"),
    "Power / charge":  (["U4", "U5", "U10", "L1", "L2", "D1", "D2", "J1", "J2"], "#c0392b"),
    "Sensors":         (["U6", "U7", "U8", "U9", "J3"], "#27ae60"),
    "Camera":          (["J4"], "#8e44ad"),
    "Motors":          (["Q1", "Q2", "Q3", "Q4", "J5", "J6", "J7", "J8"], "#e67e22"),
    "LEDs / IO":       (["LED1", "LED2", "SW1", "SW2", "J9", "J10", "J11"], "#16a085"),
}
PASSIVE_COL = "#8a929c"
DESC = {
    "U1": "ESP32-P4 (vol + caméra + H.264)", "U2": "Flash QSPI 16 Mo",
    "U3": "ESP32-C6 Wi-Fi", "Y1": "Quartz 40 MHz",
    "U4": "Chargeur TP4056 1S", "U5": "Buck 3V3 SY8089", "U10": "DC-DC cœur P4 (TLV62569)",
    "L1": "Inductance buck", "L2": "Inductance cœur P4", "D1": "ESD USB",
    "D2": "Schottky banc (DNP)", "J1": "Batterie JST-PH", "J2": "USB-C",
    "U6": "IMU ICM-42688-P", "U7": "Baromètre SPL06", "U8": "ToF VL53L1X (dessous)",
    "U9": "Flux optique PMW3901 (dessous)", "J3": "Header module flux (dessous, DNP)",
    "J4": "Caméra FFC 15 pts", "Q1": "MOSFET moteur 1", "Q2": "MOSFET moteur 2",
    "Q3": "MOSFET moteur 3", "Q4": "MOSFET moteur 4", "J5": "Plots moteur 1",
    "J6": "Plots moteur 2", "J7": "Plots moteur 3", "J8": "Plots moteur 4",
    "LED1": "LED d'état 1", "LED2": "LED d'état 2", "SW1": "Reset", "SW2": "Boot",
    "J9": "Extension", "J10": "Console UART P4", "J11": "Console UART C6",
}


def subsys_of(ref):
    for name, (refs, col) in SUBSYS.items():
        if ref in refs:
            return name, col
    return "Passifs (R/C/L…)", PASSIVE_COL


# --------------------------------------------------------------------------
# KiCad s-expression text parser (no pcbnew).
# --------------------------------------------------------------------------
def _block_end(text, start):
    """Index of the ) that closes the ( at `start`, quote-aware."""
    depth = 0
    k = start
    instr = False
    while k < len(text):
        c = text[k]
        if instr:
            if c == '"' and text[k - 1] != "\\":
                instr = False
        elif c == '"':
            instr = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return k
        k += 1
    return k


def _footprint_blocks(text):
    out = []
    i = 0
    while True:
        j = text.find("(footprint ", i)
        if j < 0:
            break
        e = _block_end(text, j)
        out.append(text[j:e + 1])
        i = e + 1
    return out


_AT = re.compile(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)")
_SE = re.compile(r'\(start\s+(-?[\d.]+)\s+(-?[\d.]+)\)\s+\(end\s+(-?[\d.]+)\s+(-?[\d.]+)\)')


def _body_size(block):
    """Body W×H (mm) from the F/B.Fab rectangle, else courtyard, else None.

    fp_line is a MULTI-LINE s-expr (start/end on one line, layer on the next),
    so split on '(fp_line' and inspect each fragment as a unit (the layer of
    that line lives inside the same fragment, before the next '(fp_line')."""
    frags = block.split("(fp_line")[1:]
    for want in (".Fab", ".CrtYd"):
        xs, ys = [], []
        for frag in frags:
            head = frag[:220]                       # one fp_line's own text
            if want not in head:
                continue
            m = _SE.search(head)
            if m:
                x1, y1, x2, y2 = map(float, m.groups())
                xs += [x1, x2]
                ys += [y1, y2]
        if xs:
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            if w > 0.2 and h > 0.2:
                return round(w, 3), round(h, 3)
    return None


def parse_footprints(text):
    fps = []
    for blk in _footprint_blocks(text):
        m = re.match(r'\(footprint\s+"([^"]+)"', blk)
        if not m:
            continue
        fp = m.group(1)
        side = "B" if re.match(r'\(footprint\s+"[^"]+"\s+\(layer\s+"B\.Cu"', blk) else "T"
        at = _AT.search(blk)                       # first (at ..) = the placement
        if not at:
            continue
        x, y = float(at.group(1)), float(at.group(2))
        rot = float(at.group(3)) if at.group(3) else 0.0
        ref = (re.search(r'\(fp_text\s+reference\s+"([^"]+)"', blk)
               or re.search(r'\(property\s+"Reference"\s+"([^"]+)"', blk))
        val = (re.search(r'\(fp_text\s+value\s+"([^"]+)"', blk)
               or re.search(r'\(property\s+"Value"\s+"([^"]+)"', blk))
        size = _body_size(blk)
        fps.append(dict(fp=fp, ref=ref.group(1) if ref else "?",
                        val=val.group(1) if val else "", x=x, y=y, rot=rot,
                        side=side, w=size[0] if size else None,
                        h=size[1] if size else None))
    return fps


_SEG = re.compile(
    r'\(segment\s+\(start\s+(-?[\d.]+)\s+(-?[\d.]+)\)\s+\(end\s+(-?[\d.]+)\s+(-?[\d.]+)\)'
    r'\s+\(width\s+(-?[\d.]+)\)\s+\(layer\s+"([^"]+)"\)')
_VIA = re.compile(r'\(via\s+\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\)\s+\(size\s+(-?[\d.]+)\)')
_GRTXT = re.compile(
    r'\(gr_text\s+"([^"]*)"\s+\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)'
    r'[^\n]*?\(layer\s+"(F\.SilkS|B\.SilkS)"')
_GRLINE = re.compile(
    r'\(gr_line\s+\(start\s+(-?[\d.]+)\s+(-?[\d.]+)\)\s+\(end\s+(-?[\d.]+)\s+(-?[\d.]+)\)'
    r'[^\n]*?\(layer\s+"(F\.SilkS|B\.SilkS)"')


def parse_tracks(text):
    segs = [dict(x1=float(a), y1=float(b), x2=float(c), y2=float(d),
                 w=float(w), layer=L) for a, b, c, d, w, L in _SEG.findall(text)]
    vias = [dict(x=float(a), y=float(b), d=float(s)) for a, b, s in _VIA.findall(text)]
    return segs, vias


def parse_silk(text):
    txts = [dict(t=t, x=float(x), y=float(y), rot=float(r) if r else 0.0, layer=L)
            for t, x, y, r, L in _GRTXT.findall(text)]
    lines = [dict(x1=float(a), y1=float(b), x2=float(c), y2=float(d), layer=L)
             for a, b, c, d, L in _GRLINE.findall(text)]
    return txts, lines


def logo_polys():
    """The S-propeller logo as board-mm polygons (from add_logo.py geometry)."""
    cx, cy, tall = 19.0, 22.5, 9.5
    s = tall / 152.0

    def M(x, y):
        return [round(cx - (x - 120.0) * s, 3), round(cy + (y - 120.0) * s, 3)]

    blades = [[M(x, y) for x, y in add_logo.flatten(add_logo.UPPER)],
              [M(x, y) for x, y in add_logo.flatten(add_logo.LOWER)]]
    return dict(blades=blades, hub=M(120, 120),
                hub_r=round(add_logo.HUB_R * s, 3), hub_w=round(add_logo.HUB_W * s, 3),
                dot_r=round(add_logo.DOT_R * s, 3),
                word=dict(t="STRATOS DRONES", x=cx, y=cy + 46.0))


# --------------------------------------------------------------------------
# Footprint → 3-D archetype (shape key, height mm, realistic colour, pins).
# --------------------------------------------------------------------------
def classify(fp, ref, w, h):
    """Return dict(arch, ht, col, pins, rows) for a footprint."""
    def pkg(name, ht, col, pins=0, rows=1, arch="box"):
        return dict(arch=arch, ht=ht, col=col, pins=pins, rows=rows)

    f = fp.split(":")[-1]   # strip lib prefix

    # passives (chip R/C/L)
    m = re.search(r'(?:R|C|L)_(\d{4})', f)
    if m and ("R_" in f or "C_" in f or "L_" in f):
        size = m.group(1)
        ht = {"0402": 0.45, "0603": 0.6, "0805": 0.75, "1005": 0.45}.get(size, 0.6)
        if f.startswith("L_") or "0805" in f and ref.startswith("L"):
            ht = 1.2
        if f.startswith("R_"):
            return pkg(f, ht, "#1c1c1e", arch="chip")            # black body
        if f.startswith("C_"):
            return pkg(f, ht + 0.1, "#c9a86a", arch="chip")      # tan MLCC
        return pkg(f, ht, "#2b2b30", arch="chip")
    if "L_Cenker" in f or ("L_" in f and "CKCS" in f):
        return pkg(f, 1.5, "#2b2b30", arch="chip")
    if f.startswith("L_"):
        return pkg(f, 1.2, "#2b2b30", arch="chip")

    # ICs / modules
    if "ESP32-C6-MINI" in f:
        return pkg(f, 2.4, "#c8ccd0", arch="module")            # RF shield can
    if "ESP32-P4" in f:
        return pkg(f, 1.0, "#131316", arch="qfn")
    if "Crystal" in f:
        return pkg(f, 0.85, "#c8ccd0", arch="can")              # metal can
    if any(k in f for k in ("SOIC", "SOP", "SO-8", "SO_8")):
        return pkg(f, 1.15, "#141416", arch="soic")
    if any(k in f for k in ("QFN", "DHVQFN", "LGA", "VL53", "PMW3901")):
        return pkg(f, 0.85, "#141416", arch="qfn")
    if "SOT-23" in f or "SOT23" in f:
        return pkg(f, 1.0, "#141416", arch="sot")

    # connectors
    if "USB_C" in f:
        return pkg(f, 3.2, "#b9bdc2", arch="usbc")
    if "JST_PH" in f or "JST-PH" in f or "PH_S2B" in f:
        return pkg(f, 4.5, "#e7e2d6", arch="conn")              # white nylon
    if "FH12" in f or "FFC" in f or "FPC" in f:
        return pkg(f, 1.2, "#6b5a3a", arch="ffc")               # brown actuator
    if "PinHeader" in f:
        pins = 2
        mm = re.search(r'(\d+)x(\d+)', f)
        rows, per = (int(mm.group(1)), int(mm.group(2))) if mm else (1, 2)
        pins = rows * per
        return pkg(f, 6.0 if "Vertical" in f else 2.5, "#101012",
                   pins=pins, rows=rows, arch="header")

    # discretes / misc
    if "WS2812" in f or "PLCC4" in f:
        return pkg(f, 0.9, "#eef0f2", arch="led")
    if "Button" in f or "SW_SPST" in f:
        return pkg(f, 3.4, "#1c1c1e", arch="button")
    if "D_SMA" in f or "SOD" in f:
        return pkg(f, 1.1, "#141416", arch="diode")
    if "MountingHole" in f:
        return pkg(f, 0.0, "#caa14a", arch="hole")

    return pkg(f, 1.0, "#3a3f46", arch="box")                    # fallback


DEF_SIZE = {   # fallback body W×H (mm) when no Fab rectangle was found
    "chip": (1.0, 0.5), "soic": (5.0, 3.9), "qfn": (3.0, 3.0), "sot": (2.9, 1.3),
    "module": (13.2, 16.6), "can": (3.2, 2.5), "usbc": (9.0, 7.5), "conn": (6.0, 4.5),
    "ffc": (18.0, 5.0), "header": (5.0, 2.5), "led": (2.0, 2.0), "button": (4.5, 3.5),
    "diode": (4.3, 2.6), "hole": (4.0, 4.0), "box": (3.0, 3.0),
}


def build_data():
    text = open(BRD, encoding="utf-8", errors="replace").read()
    fps = parse_footprints(text)
    segs, vias = parse_tracks(text)
    silk_t, silk_l = parse_silk(text)

    dsn = {c["ref"]: c for c in design.all_components()}
    parts = []
    for fpr in fps:
        ref = fpr["ref"]
        d = dsn.get(ref, {})
        cls = classify(fpr["fp"], ref, fpr["w"], fpr["h"])
        w, h = fpr["w"], fpr["h"]
        if not w or not h:
            w, h = DEF_SIZE.get(cls["arch"], (3.0, 3.0))
        sub, subcol = subsys_of(ref)
        parts.append(dict(
            ref=ref, fp=cls["arch"], fpname=fpr["fp"],
            x=round(fpr["x"], 3), y=round(fpr["y"], 3), rot=fpr["rot"],
            side=fpr["side"],   # PHYSICAL layer from the .kicad_pcb (fab truth)
            w=round(w, 3), h=round(h, 3), ht=cls["ht"], col=cls["col"],
            pins=cls["pins"], rows=cls["rows"],
            val=d.get("value", fpr["val"]), comment=d.get("comment", ""),
            populate=d.get("populate", True), sub=sub, subcol=subcol,
            desc=DESC.get(ref, "")))
    b = design.BOARD
    board = dict(w=b["w"], h=b["h"], r=b["corner_r"], th=1.6,
                 holes=[[6, 6], [b["mount_pitch_x"] + 6, 6],
                        [6, b["mount_pitch_y"] + 6],
                        [b["mount_pitch_x"] + 6, b["mount_pitch_y"] + 6]],
                 hole_d=b["mount_d"])
    return dict(board=board, parts=parts, segs=segs, vias=vias,
                silk=silk_t, silk_lines=silk_l, logo=logo_polys())


# --------------------------------------------------------------------------
# Self-contained HTML emission (Three.js r160 inlined from sim/viz/vendor)
# --------------------------------------------------------------------------
def _data_url(path):
    with open(path, "rb") as f:
        return "data:text/javascript;base64," + base64.b64encode(f.read()).decode("ascii")


def importmap():
    v = lambda *p: _data_url(os.path.join(VENDOR, *p))
    return json.dumps({"imports": {
        "three": v("three.module.js"),
        "three/addons/controls/OrbitControls.js": v("addons", "controls", "OrbitControls.js"),
        "three/addons/environments/RoomEnvironment.js":
            v("addons", "environments", "RoomEnvironment.js"),
        "three/addons/geometries/RoundedBoxGeometry.js":
            v("addons", "geometries", "RoundedBoxGeometry.js"),
    }}, separators=(",", ":"))


TEMPLATE = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>STRATOSDRONE — PCB 3D</title>
<style>
  :root{--bg:#0b0e14;--pan:#141926e6;--ink:#e8edf4;--dim:#8a94a6;--line:#232b3a;--acc:#2f6fed}
  *{box-sizing:border-box} html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);
    font:13px/1.45 -apple-system,Segoe UI,Roboto,sans-serif}
  #view{position:fixed;inset:0} canvas{display:block}
  #panel{position:fixed;top:12px;left:12px;width:262px;max-height:calc(100vh - 24px);overflow:auto;
    background:var(--pan);backdrop-filter:blur(8px);border:1px solid var(--line);border-radius:12px;padding:14px}
  h1{font-size:15px;margin:0 0 2px} .sub{color:var(--dim);font-size:11px;margin:0 0 12px}
  .grp{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--dim);margin:12px 0 6px}
  .row{display:flex;gap:6px;flex-wrap:wrap} button{flex:1;min-width:64px;cursor:pointer;color:var(--ink);
    background:#1b2230;border:1px solid var(--line);border-radius:8px;padding:7px 8px;font-size:12px}
  button.on{background:var(--acc);border-color:var(--acc)} button:hover{border-color:#3a465e}
  label.tog{display:flex;align-items:center;gap:8px;padding:4px 2px;cursor:pointer}
  label.tog input{accent-color:var(--acc)} .sw{width:12px;height:12px;border-radius:3px;display:inline-block}
  .leg{display:flex;align-items:center;gap:7px;padding:2px 0;font-size:12px;color:#c3ccda}
  #tip{position:fixed;pointer-events:none;z-index:9;background:#0e1420f2;border:1px solid var(--line);
    border-radius:8px;padding:7px 9px;font-size:12px;max-width:240px;display:none}
  #tip b{color:#fff} #tip .r{color:var(--acc);font-weight:700} #tip .d{color:var(--dim)}
  .info{color:var(--dim);font-size:11px;margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
  a{color:var(--acc)}
</style></head><body>
<div id="view"></div>
<div id="tip"></div>
<div id="panel">
  <h1>STRATOSDRONE — <span style="color:var(--acc)">PCB 3D</span></h1>
  <p class="sub">carte peuplée · tous les composants · hors-ligne</p>
  <div class="grp">Vue</div>
  <div class="row"><button id="vTop">Dessus</button><button id="vIso" class="on">Iso</button>
    <button id="vBot">Dessous</button></div>
  <div class="grp">Couleur</div>
  <div class="row"><button id="cReal" class="on">Réaliste</button>
    <button id="cSub">Par sous-système</button></div>
  <div class="grp">Affichage</div>
  <div id="togs"></div>
  <div class="grp">Sous-systèmes</div>
  <div id="legend"></div>
  <div class="info" id="info"></div>
</div>
<script type="importmap">
__IMPORTMAP__
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const DATA = __DATA__;
const BOARD = DATA.board, PARTS = DATA.parts;
const DEG = Math.PI/180, CX = BOARD.w/2, CY = BOARD.h/2, TT = BOARD.th/2;
const tx = x => x - CX, ty = y => CY - y;          // kicad (y-down) -> three (y-up), mm

// ---------- renderer / scene / camera ----------
const view = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
view.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0b0e14);
const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 2000); camera.up.set(0,0,1);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.add(new THREE.HemisphereLight(0xbfd3ff, 0x202430, 0.5));
const key = new THREE.DirectionalLight(0xffffff, 2.1); key.position.set(30,40,80); scene.add(key);
const rim = new THREE.DirectionalLight(0x88aaff, 0.7); rim.position.set(-40,-30,30); scene.add(rim);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.08;
controls.minDistance = 14; controls.maxDistance = 260;
const grid = new THREE.GridHelper(160, 32, 0x243043, 0x161c27);
grid.rotation.x = Math.PI/2; grid.position.z = -8; scene.add(grid);

// ---------- board slab + silkscreen/copper textures ----------
function roundRectShape(w,h,r){
  const s = new THREE.Shape(), x=-w/2, y=-h/2;
  s.moveTo(x+r,y); s.lineTo(x+w-r,y); s.quadraticCurveTo(x+w,y,x+w,y+r);
  s.lineTo(x+w,y+h-r); s.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
  s.lineTo(x+r,y+h); s.quadraticCurveTo(x,y+h,x,y+h-r);
  s.lineTo(x,y+r); s.quadraticCurveTo(x,y,x+r,y); return s;
}
const world = new THREE.Group(); scene.add(world);   // holds board+parts; flips for the underside view
const boardG = new THREE.Group(); world.add(boardG);
{ // green FR4 edge slab (rounded r6 corners)
  const shp = roundRectShape(BOARD.w, BOARD.h, BOARD.r);
  const geo = new THREE.ExtrudeGeometry(shp, {depth:BOARD.th, bevelEnabled:false, curveSegments:24});
  geo.translate(0,0,-BOARD.th/2);
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({color:0x0a5a30,roughness:0.55,metalness:0.1}));
  boardG.add(m);
}
function faceGeo(){   // rounded-rect face matching the slab, with 0..1 UVs for the texture
  const g = new THREE.ShapeGeometry(roundRectShape(BOARD.w, BOARD.h, BOARD.r), 24);
  const pos = g.attributes.position, uv = [];
  for (let i=0;i<pos.count;i++) uv.push((pos.getX(i)+BOARD.w/2)/BOARD.w, (pos.getY(i)+BOARD.h/2)/BOARD.h);
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv,2));
  return g;
}
const PX = 9;   // px per mm for the silk/copper canvas
const texCache = {};
function faceTex(side, withTraces, withSilk){
  const key = side + (+withTraces) + (+withSilk);
  if (texCache[key]) return texCache[key];
  const W = Math.round(BOARD.w*PX), H = Math.round(BOARD.h*PX);
  const cv = document.createElement('canvas'); cv.width=W; cv.height=H;
  const g = cv.getContext('2d');
  g.fillStyle = '#0a5a30'; g.fillRect(0,0,W,H);
  if (withTraces){
    g.lineCap='round';
    for (const s of DATA.segs){
      const face = (side==='T'&&s.layer==='F.Cu')||(side==='B'&&s.layer==='B.Cu');
      const inner = s.layer==='In1.Cu'||s.layer==='In2.Cu';
      if(!face && !inner) continue;
      g.strokeStyle = face ? 'rgba(206,150,66,0.9)' : 'rgba(120,150,110,0.22)';
      g.lineWidth = Math.max(1.1, s.w*PX);
      g.beginPath(); g.moveTo(s.x1*PX,s.y1*PX); g.lineTo(s.x2*PX,s.y2*PX); g.stroke();
    }
    g.fillStyle='rgba(214,178,96,0.95)';
    for (const v of DATA.vias){ g.beginPath(); g.arc(v.x*PX,v.y*PX,Math.max(1.2,v.d*PX/2),0,7); g.fill(); }
  }
  if (withSilk){
    g.fillStyle='#eef2f2'; g.strokeStyle='#eef2f2'; g.textAlign='center'; g.textBaseline='middle';
    g.lineWidth=Math.max(1,0.14*PX);
    for (const l of DATA.silk_lines){ if((side==='T')!==(l.layer==='F.SilkS'))continue;
      g.beginPath(); g.moveTo(l.x1*PX,l.y1*PX); g.lineTo(l.x2*PX,l.y2*PX); g.stroke(); }
    for (const t of DATA.silk){ if((side==='T')!==(t.layer==='F.SilkS'))continue;
      g.save(); g.translate(t.x*PX,t.y*PX); g.rotate((t.rot||0)*DEG);
      if (side==='B') g.scale(-1,1);                 // B.SilkS is stored mirrored -> read after board-flip
      g.font=`bold ${1.35*PX}px sans-serif`; g.fillText(t.t,0,0); g.restore(); }
    if (side==='B' && DATA.logo) drawLogo(g);
  }
  const tex = new THREE.CanvasTexture(cv); tex.anisotropy=8; tex.colorSpace=THREE.SRGBColorSpace;
  return (texCache[key] = tex);
}
function drawLogo(g){          // the S-propeller mark (the wordmark is already in DATA.silk)
  const L=DATA.logo; g.fillStyle='#eef2f2';
  for (const bl of L.blades){ g.beginPath(); g.moveTo(bl[0][0]*PX,bl[0][1]*PX);
    for (const p of bl) g.lineTo(p[0]*PX,p[1]*PX); g.closePath(); g.fill(); }
  g.lineWidth=L.hub_w*PX; g.strokeStyle='#eef2f2';
  g.beginPath(); g.arc(L.hub[0]*PX,L.hub[1]*PX,L.hub_r*PX,0,7); g.stroke();
  g.beginPath(); g.arc(L.hub[0]*PX,L.hub[1]*PX,L.dot_r*PX,0,7); g.fill();
}
const facePlanes = {};
function makeFace(side){
  // NB: NO plane flip — the face keeps the board (x,y) mapping so its copper
  // aligns with the parts (which are all placed at tx(x),ty(y)). The bottom is
  // seen from below via DoubleSide; its silk glyphs are pre-mirrored in faceTex
  // so text still reads left-to-right from underneath.
  const m = new THREE.MeshStandardMaterial({map:faceTex(side,true,true), roughness:0.5,
    metalness:0.05, side: side==='T' ? THREE.FrontSide : THREE.DoubleSide});
  const pl = new THREE.Mesh(faceGeo(), m);
  pl.position.z = side==='T' ? TT+0.02 : -TT-0.02;
  boardG.add(pl); facePlanes[side] = {mesh:pl};
}
makeFace('T'); makeFace('B');
// mount-hole rings
for (const [hx,hy] of BOARD.holes){
  const ring = new THREE.Mesh(new THREE.CylinderGeometry(BOARD.hole_d/2*1.7, BOARD.hole_d/2*1.7, BOARD.th+0.2, 20, 1, true),
    new THREE.MeshStandardMaterial({color:0xcaa14a,metalness:0.9,roughness:0.35,side:THREE.DoubleSide}));
  ring.rotation.x = Math.PI/2; ring.position.set(tx(hx), ty(hy), 0); boardG.add(ring);
}

// ---------- component archetype builders ----------
const MAT = {}; function mat(c,m,r){ const k=c+'|'+m+'|'+r;
  return MAT[k] || (MAT[k]=new THREE.MeshStandardMaterial({color:new THREE.Color(c),metalness:m,roughness:r})); }
const SILVER = ()=>mat('#c4c9cf',0.9,0.3), GOLD=()=>mat('#caa14a',0.85,0.35), BLK=(c)=>mat(c||'#141416',0.15,0.55);
function rbox(w,h,d,m,r){ const g=new RoundedBoxGeometry(w,h,d,2,Math.min(r||0.08,w/2,h/2,d/2)); return new THREE.Mesh(g,m); }
function box(w,h,d,m){ return new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m); }

function buildPart(p, dir){
  const G = new THREE.Group(); const w=p.w, h=p.h, ht=Math.max(p.ht,0.05);
  const bodyMeshes = [];
  const put = (mesh, z)=>{ mesh.position.z = dir*(z); G.add(mesh); return mesh; };
  const A = p.fp;
  if (A==='chip'){
    const long = Math.max(w,h), horiz = w>=h;
    const b = put(rbox(w,h,ht, mat(p.col,0.1,0.6), 0.06), ht/2); b.userData.body=1; bodyMeshes.push(b);
    const cap = long*0.24;
    for (const s of [-1,1]){ const c = box(horiz?cap:w, horiz?h:cap, ht*0.9, SILVER());
      c.position.set(horiz?s*(w/2-cap/2):0, horiz?0:s*(h/2-cap/2), dir*ht/2); G.add(c); }
  } else if (A==='soic'||A==='qfn'||A==='box'||A==='diode'){
    const b = put(rbox(w,h,ht, BLK(p.col), 0.05), ht/2); b.userData.body=1; bodyMeshes.push(b);
    if (A==='diode'){ const st=box(w*0.16,h,ht*1.02,SILVER()); st.position.set(w*0.34,0,dir*ht/2); G.add(st); }
    if (A==='qfn'||A==='soic'){ const d=new THREE.Mesh(new THREE.CylinderGeometry(Math.min(w,h)*0.07,Math.min(w,h)*0.07,ht*0.2,10),mat('#3a3f46',0.2,0.6));
      d.rotation.x=Math.PI/2; d.position.set(-w/2+w*0.15,-h/2+h*0.15,dir*ht*1.05); G.add(d); }
    if (A==='soic'){ for(const s of [-1,1]) for(let i=0;i<4;i++){ const pin=box(w*0.14,h*0.16,ht*0.3,GOLD());
      pin.position.set(s*(w/2+w*0.06), -h*0.3+i*(h*0.2), dir*ht*0.2); G.add(pin);} }
  } else if (A==='sot'){
    const b = put(rbox(w,h,ht, BLK(p.col),0.04), ht/2); b.userData.body=1; bodyMeshes.push(b);
    for (const s of [-1,1]) for (let i=0;i<2;i++){ const pin=box(w*0.16,h*0.2,ht*0.3,GOLD());
      pin.position.set(s*(w/2+w*0.08),(i?1:-1)*h*0.28,dir*ht*0.2); G.add(pin); }
  } else if (A==='module'){
    const b = put(rbox(w,h,ht, mat(p.col,0.75,0.35),0.12), ht/2); b.userData.body=1; bodyMeshes.push(b);
    const lid=box(w*0.9,h*0.9,ht*0.12, mat('#9aa0a6',0.6,0.4)); lid.position.z=dir*ht*0.96; G.add(lid);
  } else if (A==='can'){
    const b = put(rbox(w,h,ht, SILVER(),0.15), ht/2); b.userData.body=1; bodyMeshes.push(b);
  } else if (A==='usbc'){
    const b = put(rbox(w,h,ht, mat(p.col,0.85,0.28),0.2), ht/2); b.userData.body=1; bodyMeshes.push(b);
    const slot=box(w*0.55,h*0.42,ht*0.7, mat('#1a1d22',0.3,0.6)); slot.position.set(-w*0.18,0,dir*ht/2); G.add(slot);
  } else if (A==='ffc'){
    const b = put(rbox(w,h,ht, mat(p.col,0.2,0.7),0.08), ht/2); b.userData.body=1; bodyMeshes.push(b);
    const flap=box(w,h*0.34,ht*0.5, mat('#3b3120',0.2,0.7)); flap.position.set(0,h*0.28,dir*ht*0.8); G.add(flap);
  } else if (A==='conn'){
    const b = put(rbox(w,h,ht, mat(p.col,0.05,0.75),0.1), ht/2); b.userData.body=1; bodyMeshes.push(b);
  } else if (A==='header'){
    const base=put(rbox(w,h,ht*0.35, BLK('#101012'),0.05), ht*0.175); base.userData.body=1; bodyMeshes.push(base);
    const per=Math.max(1,Math.round(p.pins/Math.max(1,p.rows))); const rows=p.rows||1;
    for(let r=0;r<rows;r++) for(let i=0;i<per;i++){ const pin=new THREE.Mesh(new THREE.CylinderGeometry(0.28,0.28,ht,8),GOLD());
      pin.rotation.x=Math.PI/2; pin.position.set(-w/2+(i+0.5)*w/per,(rows>1?(r?1:-1)*h*0.22:0),dir*ht/2); G.add(pin);}
  } else if (A==='led'){
    const b=put(rbox(w,h,ht, mat(p.col,0.05,0.5),0.06), ht/2); b.userData.body=1; bodyMeshes.push(b);
    const dome=new THREE.Mesh(new THREE.SphereGeometry(Math.min(w,h)*0.32,14,10),
      new THREE.MeshStandardMaterial({color:0xffffff,emissive:0x88ccff,emissiveIntensity:0.6,roughness:0.3}));
    dome.position.z=dir*ht; G.add(dome);
  } else if (A==='button'){
    const base=put(rbox(w,h,ht*0.4, BLK(p.col),0.05), ht*0.2); base.userData.body=1; bodyMeshes.push(base);
    const btn=new THREE.Mesh(new THREE.CylinderGeometry(Math.min(w,h)*0.3,Math.min(w,h)*0.3,ht*0.6,16),mat('#26292f',0.2,0.5));
    btn.rotation.x=Math.PI/2; btn.position.z=dir*ht*0.7; G.add(btn);
  } else if (A==='hole'){
    const ann=new THREE.Mesh(new THREE.TorusGeometry(w*0.28,0.35,8,20),GOLD()); ann.position.z=0; G.add(ann);
    ann.userData.body=1; bodyMeshes.push(ann);
  } else {
    const b=put(rbox(w,h,ht, BLK(p.col),0.06), ht/2); b.userData.body=1; bodyMeshes.push(b);
  }
  G.userData.part = p; G.userData.bodies = bodyMeshes;
  return G;
}

// ---------- place parts ----------
const topG = new THREE.Group(), botG = new THREE.Group(); world.add(topG, botG);
const allBodies = [];
for (const p of PARTS){
  const dir = p.side==='T' ? 1 : -1;
  const G = buildPart(p, dir);
  G.position.set(tx(p.x), ty(p.y), p.side==='T' ? TT : -TT);
  G.rotation.z = -p.rot*DEG;
  (p.side==='T'?topG:botG).add(G);
  for (const b of G.userData.bodies){ b.material=b.material.clone();   // own material -> recolourable
    b.userData.part=p; b.userData.realCol=b.material.color.getHex(); allBodies.push(b); }
  // reference-designator sprite
  const lab = makeLabel(p.ref);
  lab.position.set(tx(p.x), ty(p.y), (p.side==='T'?TT:-TT) + dir*(Math.max(p.ht,0.5)+0.9));
  lab.userData.isLabel = 1; (p.side==='T'?topG:botG).add(lab);
}
function makeLabel(txt){
  const cv=document.createElement('canvas'); cv.width=128; cv.height=48;
  const g=cv.getContext('2d'); g.fillStyle='rgba(12,18,28,0.82)';
  g.beginPath(); g.roundRect(2,10,124,28,7); g.fill();
  g.fillStyle='#e8edf4'; g.font='bold 22px sans-serif'; g.textAlign='center'; g.textBaseline='middle';
  g.fillText(txt,64,25);
  const tex=new THREE.CanvasTexture(cv); tex.colorSpace=THREE.SRGBColorSpace;
  const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:tex,depthTest:true,transparent:true}));
  sp.scale.set(3.2,1.2,1); return sp;
}

// ---------- interaction: hover tooltip ----------
const ray=new THREE.Raycaster(), mouse=new THREE.Vector2(); const tip=document.getElementById('tip');
let hovered=null;
renderer.domElement.addEventListener('pointermove', e=>{
  const r=renderer.domElement.getBoundingClientRect();
  mouse.x=((e.clientX-r.left)/r.width)*2-1; mouse.y=-((e.clientY-r.top)/r.height)*2+1;
  ray.setFromCamera(mouse,camera);
  const vis=allBodies.filter(b=>b.parent&&b.parent.parent&&b.parent.parent.visible);
  const hit=ray.intersectObjects(vis,false)[0];
  if (hit){ const p=hit.object.userData.part;
    tip.style.display='block'; tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY+12)+'px';
    tip.innerHTML=`<span class="r">${p.ref}</span> <b>${p.val||''}</b><br>`+
      (p.desc?`${p.desc}<br>`:'')+`<span class="d">${p.sub} · ${p.side==='T'?'dessus':'dessous'} · ${p.fpname}</span>`;
  } else tip.style.display='none';
});

// ---------- colour modes ----------
let colMode='real';
function applyColMode(){
  for (const b of allBodies){ const p=b.userData.part;
    if (colMode==='sub') b.material.color.set(p.subcol);
    else b.material.color.setHex(b.userData.realCol);
  }
}

// ---------- UI ----------
const TOGS=[
  ['top','Composants dessus',()=>topG,true],['bot','Composants dessous',()=>botG,true],
  ['lab','Étiquettes réf',null,true],['trace','Pistes cuivre',null,true],
  ['silk','Sérigraphie + logo',null,true],['grid','Grille',()=>grid,true],
];
const togsEl=document.getElementById('togs'); const state={};
for (const [k,label,,def] of TOGS){ state[k]=def;
  const l=document.createElement('label'); l.className='tog';
  l.innerHTML=`<input type="checkbox" ${def?'checked':''}><span>${label}</span>`;
  l.querySelector('input').addEventListener('change',e=>{ state[k]=e.target.checked; applyState(); });
  togsEl.appendChild(l);
}
function applyState(){
  topG.visible=state.top; botG.visible=state.bot; grid.visible=state.grid;
  for (const g of [topG,botG]) g.children.forEach(c=>{ if(c.userData.isLabel)
    c.visible = (g===topG?state.top:state.bot)&&state.lab; });
  for (const side of ['T','B']){ const f=facePlanes[side];
    f.mesh.material.map = faceTex(side, state.trace, state.silk); f.mesh.material.needsUpdate=true; }
}

document.getElementById('cReal').addEventListener('click',()=>setCol('real'));
document.getElementById('cSub').addEventListener('click',()=>setCol('sub'));
function setCol(m){ colMode=m; applyColMode();
  document.getElementById('cReal').classList.toggle('on',m==='real');
  document.getElementById('cSub').classList.toggle('on',m==='sub'); }

function frame(dist, el, az){ const d=dist, e=(el||45)*DEG, a=(az||0)*DEG;
  camera.position.set(d*Math.cos(e)*Math.sin(a), -d*Math.cos(e)*Math.cos(a), d*Math.sin(e));
  controls.target.set(0,0,0); controls.update(); }
document.getElementById('vTop').addEventListener('click',()=>{setView('vTop');world.rotation.x=0;frame(120,89,0);});
document.getElementById('vIso').addEventListener('click',()=>{setView('vIso');world.rotation.x=0;frame(120,42,18);});
document.getElementById('vBot').addEventListener('click',()=>{setView('vBot');world.rotation.x=Math.PI;frame(120,52,18);});
function setView(id){ for(const v of ['vTop','vIso','vBot']) document.getElementById(v).classList.toggle('on',v===id); }

// legend
const legEl=document.getElementById('legend'); const SUB=__SUBLEG__;
for (const [name,col] of SUB){ const d=document.createElement('div'); d.className='leg';
  d.innerHTML=`<span class="sw" style="background:${col}"></span>${name}`; legEl.appendChild(d); }
const nT=PARTS.filter(p=>p.side==='T').length, nB=PARTS.length-nT;
document.getElementById('info').innerHTML =
  `${PARTS.length} composants · ${nT} dessus / ${nB} dessous<br>${DATA.segs.length} pistes · ${DATA.vias.length} vias`+
  `<br><span style="color:#6b7789">corps synthétisés — contourne les modèles 3D KiCad manquants</span>`;

// ---------- loop ----------
let looping=false, ioVisible=true, hostControlled=false;
const active=()=>ioVisible;
function startLoop(){ if(!looping){ looping=true; requestAnimationFrame(loop); } }
function loop(){ if(!active()){ looping=false; return; } requestAnimationFrame(loop);
  controls.update(); renderer.render(scene,camera); }
function resize(){ const w=view.clientWidth,h=view.clientHeight; renderer.setSize(w,h);
  camera.aspect=w/h; camera.updateProjectionMatrix(); }
addEventListener('resize',resize); resize();
applyState(); applyColMode(); frame(120,42,18); startLoop();

window.__vizRendering = ()=>looping;
window.__pcbInfo = ()=>({parts:PARTS.length, top:nT, bottom:nB, segs:DATA.segs.length, vias:DATA.vias.length});
window.__cam = frame;
addEventListener('message',e=>{ const m=e.data; if(m&&m.type==='viz'){ hostControlled=true; ioVisible=!!m.visible; if(active())startLoop(); }});
new IntersectionObserver(es=>{ if(hostControlled)return; ioVisible=es[0].isIntersecting; if(active())startLoop(); },{threshold:0.01}).observe(view);
try{ parent.postMessage({type:'ready'},'*'); }catch(e){}
</script></body></html>
"""


def main():
    data = build_data()
    subleg = [[name, col] for name, (_, col) in SUBSYS.items()] + [["Passifs (R/C/L…)", PASSIVE_COL]]
    html = (TEMPLATE
            .replace("__IMPORTMAP__", importmap())
            .replace("__DATA__", json.dumps(data, separators=(",", ":")))
            .replace("__SUBLEG__", json.dumps(subleg, separators=(",", ":"))))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    p = data["parts"]
    nt = sum(1 for x in p if x["side"] == "T")
    print(f"== STRATOSDRONE PCB 3D viewer ==")
    print(f"  parts {len(p)} (top {nt}, bottom {len(p)-nt})  segs {len(data['segs'])}  vias {len(data['vias'])}")
    print(f"  wrote {OUT} ({os.path.getsize(OUT)} B)")


if __name__ == "__main__":
    main()
