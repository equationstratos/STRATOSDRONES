#!/usr/bin/env python3
"""Generate a self-contained interactive 3-D viewer for the STRATOSDRONE.

The drone's *functional* geometry lives in ``sim/models/stratosdrone/model.sdf``
(the rigid body Gazebo simulates).  This script parses that SDF for the hard
constraints — motor positions, prop radius, wheelbase, mass — and bakes them
into a single ``drone_viewer.html`` powered by Three.js.

The viewer shows the drone two ways, switchable live:
  • **Stylisé (Tello)** — a sleek, modern, DJI-Tello-class body built
    procedurally in Three.js (rounded shell, vented canopy, camera nose, swept
    arms, two-blade props, circular prop guards) with PBR materials + image-
    based lighting.  Anchored to the *real* motor/prop geometry from the SDF.
  • **Sim (SDF brut)** — the raw collision/visual primitives Gazebo uses, for
    cross-checking that the pretty model still matches the simulated one.

Both modes share the same controls (per-group show/hide, exploded view,
spinning props, view presets) and the printed-frame STL drag-and-drop overlay.

Three.js (r160) is inlined as base64 ``data:`` URLs, so the HTML opens by
double-click, fully offline — no CDN, no web server, no ``file://`` CORS issue.

Run:  python3 sim/viz/gen_viewer.py            # -> sim/viz/drone_viewer.html
      python3 sim/viz/gen_viewer.py --open     # also print a file:// URL
"""
import argparse
import base64
import json
import math
import os
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SDF = os.path.join(REPO, "sim", "models", "stratosdrone", "model.sdf")
OUT = os.path.join(HERE, "drone_viewer.html")
VENDOR = os.path.join(HERE, "vendor")


# --------------------------------------------------------------------------
# SDF parsing
# --------------------------------------------------------------------------
def _floats(text, n=None):
    vals = [float(x) for x in (text or "").split()]
    if n is not None:
        vals = (vals + [0.0] * n)[:n]
    return vals


def category(name):
    """Group a visual by name prefix, for the show/hide layer toggles.
    ``duct_*`` maps to ``guards`` so the SDF ducts and the styled prop guards
    share one toggle."""
    if name.startswith("arm"):
        return "arms"
    if name.startswith("motor"):
        return "motors"
    if name.startswith("prop"):
        return "props"
    if name.startswith("duct"):
        return "guards"
    return "shell"          # body, canopy, camera, battery


def parse_sdf(path):
    """Return (parts, meta).  parts: list of visual dicts ready for Three.js."""
    root = ET.parse(path).getroot()
    link = root.find(".//link")
    parts = []

    for vis in link.findall("visual"):
        name = vis.get("name", "?")
        pose = _floats(vis.findtext("pose", "0 0 0 0 0 0"), 6)
        geom = vis.find("geometry")
        box = geom.find("box") if geom is not None else None
        cyl = geom.find("cylinder") if geom is not None else None

        diffuse = [0.6, 0.6, 0.62, 1.0]
        mat = vis.find("material")
        if mat is not None and mat.findtext("diffuse"):
            diffuse = _floats(mat.findtext("diffuse"), 4)

        tr = vis.findtext("transparency")
        opacity = (1.0 - float(tr)) if tr not in (None, "") else diffuse[3]

        part = {
            "name": name,
            "group": category(name),
            "pose": pose,
            "color": [round(c, 4) for c in diffuse[:3]],
            "opacity": round(opacity, 3),
        }
        if box is not None:
            part["type"] = "box"
            part["size"] = _floats(box.findtext("size"), 3)
        elif cyl is not None:
            part["type"] = "cylinder"
            part["radius"] = float(cyl.findtext("radius"))
            part["length"] = float(cyl.findtext("length"))
        else:
            continue
        parts.append(part)

    hull = None
    col = link.find("collision")
    if col is not None:
        cbox = col.find(".//box")
        if cbox is not None:
            hull = {
                "pose": _floats(col.findtext("pose", "0 0 0 0 0 0"), 6),
                "size": _floats(cbox.findtext("size"), 3),
            }

    mass = float(link.findtext(".//inertial/mass", "0") or 0)
    meta = {"mass": mass, "hull": hull, "dims": derive_dims(parts, mass)}
    return parts, meta


def derive_dims(parts, mass):
    """Headline numbers computed from the geometry so they track the model."""
    motors = [p for p in parts if p["group"] == "motors"]
    props = [p for p in parts if p["group"] == "props"]

    wheelbase = 0.0
    if len(motors) >= 2:
        xs = [m["pose"][0] for m in motors]
        ys = [m["pose"][1] for m in motors]
        wheelbase = math.hypot(max(xs) - min(xs), max(ys) - min(ys))

    prop_d = 2 * max((p.get("radius", 0) for p in props), default=0)

    tip = 0.0
    for p in props:
        x, y = p["pose"][0], p["pose"][1]
        tip = max(tip, 2 * (math.hypot(x, y) + p.get("radius", 0)) / math.sqrt(2))

    lo = [1e9, 1e9, 1e9]
    hi = [-1e9, -1e9, -1e9]
    for p in parts:
        c = p["pose"][:3]
        if p["type"] == "box":
            h = [s / 2 for s in p["size"]]
        else:
            r, L = p.get("radius", 0), p.get("length", 0)
            h = [r, r, L / 2]
        for i in range(3):
            lo[i] = min(lo[i], c[i] - h[i])
            hi[i] = max(hi[i], c[i] + h[i])
    bbox = [hi[i] - lo[i] for i in range(3)]

    mm = lambda v: round(v * 1000, 1)
    return {
        "wheelbase_mm": mm(wheelbase),
        "prop_d_mm": mm(prop_d),
        "tip_mm": mm(tip),
        "len_mm": mm(bbox[0]),
        "wid_mm": mm(bbox[1]),
        "hgt_mm": mm(bbox[2]),
        "mass_g": round(mass * 1000, 1),
    }


# --------------------------------------------------------------------------
# HTML emission
# --------------------------------------------------------------------------
def _data_url(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return "data:text/javascript;base64," + b64


def build_importmap():
    """Import-map of inlined data: URLs -> one self-contained, offline file.
    Every addon imports only the bare ``three`` specifier, resolved here too."""
    v = lambda *p: _data_url(os.path.join(VENDOR, *p))
    imports = {
        "three": v("three.module.js"),
        "three/addons/controls/OrbitControls.js": v("addons", "controls", "OrbitControls.js"),
        "three/addons/loaders/STLLoader.js": v("addons", "loaders", "STLLoader.js"),
        "three/addons/geometries/RoundedBoxGeometry.js": v("addons", "geometries", "RoundedBoxGeometry.js"),
        "three/addons/environments/RoomEnvironment.js": v("addons", "environments", "RoomEnvironment.js"),
    }
    return json.dumps({"imports": imports}, separators=(",", ":"))


def build_html(parts, meta):
    payload = json.dumps({"parts": parts, "meta": meta}, separators=(",", ":"))
    # the printed V2 shells, embedded SEPARATELY (lower body + capot) so the
    # viewer can show the real parts, explode them apart and spin props on top.
    def _b64(path):
        if not os.path.exists(path):
            return ""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    stldir = os.path.join(REPO, "hardware", "frame", "tello_style", "stl")
    body_b64  = _b64(os.path.join(stldir, "body_bottom_v2.stl"))
    capot_b64 = _b64(os.path.join(stldir, "body_top_v2.stl"))
    prop_b64  = _b64(os.path.join(HERE, "prop.stl"))     # real DJI-Tello propeller
    pcb_b64   = _b64(os.path.join(HERE, "pcb.stl"))       # mainboard dummy
    batt_b64  = _b64(os.path.join(HERE, "battery.stl"))   # 1S pack dummy
    guard_b64 = _b64(os.path.join(HERE, "guard.stl"))     # real Tello prop guard
    return (TEMPLATE
            .replace("/*__DATA__*/", payload)
            .replace("__IMPORTMAP__", build_importmap())
            .replace("__BODY_STL_B64__", body_b64)
            .replace("__CAPOT_STL_B64__", capot_b64)
            .replace("__PROP_STL_B64__", prop_b64)
            .replace("__PCB_STL_B64__", pcb_b64)
            .replace("__BATT_STL_B64__", batt_b64)
            .replace("__GUARD_STL_B64__", guard_b64))


TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>STRATOSDRONES — visualisateur 3D</title>
<style>
  :root{--bg:#0b0e14;--panel:#12161d;--line:#262d38;--ink:#e6edf3;--mut:#8b949e;
        --acc:#2f6fed;--acc2:#63a4ff;}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;font:13px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
            background:var(--bg);color:var(--ink);overflow:hidden}
  #app{display:flex;height:100%}
  #side{width:304px;flex:none;background:var(--panel);border-right:1px solid var(--line);
        display:flex;flex-direction:column;overflow-y:auto}
  #view{flex:1;position:relative}
  canvas{display:block}
  header{padding:14px 16px;border-bottom:1px solid var(--line)}
  header h1{margin:0;font-size:15px;letter-spacing:.3px}
  header h1 b{color:var(--acc)}
  header p{margin:3px 0 0;color:var(--mut);font-size:11px}
  .sec{padding:12px 16px;border-bottom:1px solid var(--line)}
  .sec h2{margin:0 0 9px;font-size:11px;text-transform:uppercase;letter-spacing:.6px;
          color:var(--mut);font-weight:600}
  .row{display:flex;align-items:center;gap:8px;margin:5px 0}
  label.tog{display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none;margin:5px 0}
  label.tog input{accent-color:var(--acc)}
  .sw{width:11px;height:11px;border-radius:3px;flex:none}
  .btns{display:grid;grid-template-columns:1fr 1fr;gap:6px}
  button{background:#1b212b;color:var(--ink);border:1px solid var(--line);border-radius:6px;
         padding:7px 8px;font-size:12px;cursor:pointer;transition:.12s}
  button:hover{background:#262d38;border-color:#3a4250}
  button.on{background:var(--acc);border-color:var(--acc);color:#fff}
  input[type=range]{width:100%;accent-color:var(--acc)}
  .val{color:var(--acc);font-variant-numeric:tabular-nums}
  table{width:100%;border-collapse:collapse;font-size:12px}
  td{padding:3px 0;color:var(--mut)}
  td.v{text-align:right;color:var(--ink);font-variant-numeric:tabular-nums}
  .spec td.v{color:var(--acc2)}
  #drop{border:1.5px dashed var(--line);border-radius:8px;padding:14px;text-align:center;
        color:var(--mut);font-size:11px;cursor:pointer;transition:.15s}
  #drop.hot{border-color:var(--acc);color:var(--ink);background:#1b212b}
  #hud{position:absolute;left:12px;bottom:12px;background:rgba(11,14,20,.82);
       border:1px solid var(--line);border-radius:8px;padding:9px 12px;font-size:11px;
       color:var(--mut);backdrop-filter:blur(4px);pointer-events:none}
  #hud b{color:var(--acc)}
  #tip{position:absolute;right:12px;top:12px;background:rgba(11,14,20,.82);
       border:1px solid var(--line);border-radius:8px;padding:8px 11px;font-size:11px;
       color:var(--mut);max-width:212px}
  #tip b{color:var(--ink)}
  .mini{font-size:10px;color:var(--mut);margin-top:6px}
  code{color:var(--acc2)}
  /* embed (configurator live preview): hide all chrome, just the drone */
  body.embed #side, body.embed #tip, body.embed #hud{display:none}
  /* playground: swap the control panel for a script console */
  #pg{width:340px;flex:none;background:var(--panel);border-right:1px solid var(--line);
      display:none;flex-direction:column;overflow-y:auto}
  body.playground #side, body.playground #tip{display:none}
  body.playground #pg{display:flex}
  #pgCode{width:100%;height:186px;resize:vertical;background:#0b0e14;color:var(--ink);
      border:1px solid var(--line);border-radius:6px;padding:8px;
      font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre;overflow:auto}
  .pg-log{height:118px;overflow:auto;font:11px/1.55 ui-monospace,Menlo,monospace;color:var(--mut);
      background:#0b0e14;border:1px solid var(--line);border-radius:6px;padding:8px}
  .pg-log .ok{color:var(--acc2)} .pg-log .err{color:#ff6b6b} .pg-log .cmd{color:var(--ink)}
  .pg-log div{white-space:pre-wrap}
  /* mobile: stack the panel above the canvas instead of side-by-side */
  @media (max-width:700px){
    #app{flex-direction:column}
    #side,#pg{width:100%;max-height:46%;border-right:0;border-bottom:1px solid var(--line)}
    #view{min-height:54%}
    #tip{display:none}
    #hud{font-size:10px;padding:6px 9px}
    #pgCode{height:120px}
    .pg-log{height:80px}
    header{padding:10px 14px}
  }
</style>
</head>
<body>
<div id="app">
  <div id="side">
    <header>
      <h1><b>STRATOS</b>DRONES — 3D</h1>
      <p>Fr4n7-001 · Tello EDU class · 118 mm · 3"</p>
    </header>

    <div class="sec">
      <h2>Modèle</h2>
      <div class="btns">
        <button id="mFrame" class="on">Frame imprimé</button>
        <button id="mStyled">Stylisé (Tello)</button>
        <button id="mSdf">Sim (SDF brut)</button>
      </div>
    </div>

    <div class="sec">
      <h2>Vues</h2>
      <div class="btns">
        <button data-view="iso">Isométrique</button>
        <button data-view="top">Dessus</button>
        <button data-view="front">Face</button>
        <button data-view="side">Côté</button>
      </div>
    </div>

    <div class="sec">
      <h2>Composants</h2>
      <div id="groups"></div>
    </div>

    <div class="sec">
      <h2>Affichage</h2>
      <div class="row"><span style="flex:1">Vue éclatée</span>
        <span class="val" id="explodeV">0%</span></div>
      <input type="range" id="explode" min="0" max="100" value="0"/>
      <div class="row" style="margin-top:10px"><span style="flex:1">Rotation hélices</span>
        <span class="val" id="spinV">arrêt</span></div>
      <input type="range" id="spin" min="0" max="100" value="0"/>
      <div class="btns" style="margin-top:10px">
        <button id="bWire">Fil de fer</button>
        <button id="bGrid" class="on">Grille</button>
        <button id="bAxes">Axes</button>
        <button id="bHull">Coque collision</button>
      </div>
    </div>

    <div class="sec">
      <h2>Dimensions (mesurées)</h2>
      <table id="dims"></table>
    </div>

    <div class="sec">
      <h2>STRATOSDRONES vs Tello EDU</h2>
      <table class="spec">
        <tr><td>Entraxe</td><td class="v">118 mm</td></tr>
        <tr><td>Hélices</td><td class="v">3" (76 mm)</td></tr>
        <tr><td>Moteurs</td><td class="v">8520 brushed</td></tr>
        <tr><td>MCU vol</td><td class="v">ESP32-P4</td></tr>
        <tr><td>Radio</td><td class="v">ESP32-C6 · WiFi6</td></tr>
        <tr><td>Caméra</td><td class="v">OV5647 5MP CSI</td></tr>
      </table>
    </div>

    <div class="sec">
      <h2>Frame imprimé (STL)</h2>
      <div id="drop">Glissez un <b>.stl</b> ici<br/>
        <span class="mini">hardware/frame/**/stl/*.stl</span></div>
      <div id="stlList" class="mini"></div>
      <div class="row" style="margin-top:8px">
        <span style="flex:1">Opacité STL</span><span class="val" id="stlOpV">100%</span></div>
      <input type="range" id="stlOp" min="10" max="100" value="100"/>
    </div>
  </div>

  <div id="pg">
    <header>
      <h1><b>STRATOS</b>DRONES — Playground</h1>
      <p>Fr4n7-001 · pilotez le drone avec un script (SDK Tello)</p>
    </header>
    <div class="sec">
      <h2>Script</h2>
      <textarea id="pgCode" spellcheck="false">command
takeoff
forward 100
cw 90
forward 100
cw 90
forward 100
cw 90
forward 100
cw 90
land</textarea>
      <div class="btns" style="margin-top:8px">
        <button id="pgRun" class="on">▶ Exécuter</button>
        <button id="pgReset">■ Réinitialiser</button>
      </div>
    </div>
    <div class="sec">
      <h2>Scripts du dépôt</h2>
      <div class="btns">
        <button id="pgP1">01 · Hover</button>
        <button id="pgP2">02 · Carré</button>
        <button id="pgP3">03 · Swarm ×3</button>
        <button id="pgP4">★ Freestyle</button>
      </div>
      <div class="mini">01-03 : miroirs fidèles de <code>sdk/python/examples/*.py</code> —
        <a href="https://github.com/equationstratos/STRATOSDRONE/tree/claude/cool-ride-w1bpia/sdk/python/examples"
           target="_blank" rel="noopener" style="color:var(--acc2)">voir les originaux Python</a>.
        ★ Freestyle : démo bonus (curves + flips), pas dans le dépôt.</div>
    </div>
    <div class="sec">
      <h2>Pilotage clavier</h2>
      <button id="pgKbd" style="width:100%">🎮 Pilotage clavier : OFF</button>
      <div class="mini"><b>T</b> décoller · <b>↑</b> avancer · <b>↓</b> reculer ·
        <b>←</b> gauche · <b>→</b> droite · <b>Z</b> monter · <b>W</b> descendre ·
        <b>Q</b> pivoter à gauche · <b>D</b> pivoter à droite ·
        <b>F</b> flip · <b>L</b> atterrir.
        Actif quand aucun script ne tourne — pilote toute la formation.</div>
    </div>
    <div class="sec">
      <h2>État du vol</h2>
      <table>
        <tr><td>Drones</td><td class="v" id="pgN">1</td></tr>
        <tr><td>Batterie (min)</td><td class="v" id="pgBat">100 %</td></tr>
        <tr><td>Altitude (max)</td><td class="v" id="pgAlt">0 cm</td></tr>
        <tr><td>Cap drone 1</td><td class="v" id="pgYaw">0°</td></tr>
        <tr><td>Commande</td><td class="v" id="pgCmd">—</td></tr>
      </table>
    </div>
    <div class="sec">
      <h2>Journal</h2>
      <div id="pgLog" class="pg-log"></div>
    </div>
    <div class="sec">
      <h2>Commandes</h2>
      <div class="mini">command · <b>drones &lt;1-6&gt;</b> · takeoff · land ·
        forward/back/left/right/up/down &lt;20-500&gt; · cw/ccw &lt;1-360&gt; ·
        go x y z speed · <b>curve x1 y1 z1 x2 y2 z2 speed</b> (10-60) ·
        flip l/r/f/b · speed &lt;10-100&gt; · <b>sleep &lt;s&gt;</b>.<br/>
        En essaim, les arguments acceptent des expressions de l'index
        <code>i</code> (0,1,2…, sans espaces)&nbsp;:
        <code>go 60+40*i (i-1)*80 0 60</code> — comme
        <code>swarm.parallel(lambda i, t: …)</code>.<br/>
        Style Python accepté&nbsp;: <code>move_forward(100); rotate_clockwise(90); flip('f');</code></div>
    </div>
  </div>

  <div id="view">
    <div id="tip"><b>Souris :</b> glisser = orbite · molette = zoom ·
      clic-droit = pan. Repère <b>FLU</b> (X avant, Y gauche, Z haut).</div>
    <div id="hud"></div>
  </div>
</div>

<!-- Three.js (r160) inlined as base64 data: URLs by gen_viewer.py -> single
     offline file, opens by double-click (no CDN / server / file:// CORS). -->
<script type="importmap">
__IMPORTMAP__
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const DATA = /*__DATA__*/;
const PARTS = DATA.parts, META = DATA.meta;

const GROUPKEYS = ['shell','elec','arms','motors','props','guards'];
const GROUPS = {
  shell:  {label:'Corps / canopy / caméra', color:'#cfd3d9'},
  elec:   {label:'PCB / batterie',          color:'#2f8f4f'},
  arms:   {label:'Bras',                    color:'#3a3f47'},
  motors: {label:'Moteurs',                 color:'#8b929c'},
  props:  {label:'Hélices',                 color:'#2f6fed'},
  guards: {label:'Protège-hélices',         color:'#6b7280'},
};

// real anchors from the SDF (so the styled body sits on the true geometry)
const MOTORS = PARTS.filter(p=>p.group==='motors')
  .map(p=>({x:p.pose[0], y:p.pose[1], name:p.name}));
const PROP_R = Math.max(...PARTS.filter(p=>p.group==='props').map(p=>p.radius||0), 0.0381);

// ---- renderer / scene (Z-up to match the SDF FLU frame) --------------------
const view = document.getElementById('view');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0e14);

const camera = new THREE.PerspectiveCamera(42, 1, 0.001, 100);
camera.up.set(0, 0, 1);

const renderer = new THREE.WebGLRenderer({antialias:true});
// cap the backbuffer: full retina x2 is invisible on this dark scene but
// doubles GPU load — a real cost when several viewers share one page
renderer.setPixelRatio(Math.min(devicePixelRatio,
  matchMedia('(max-width:700px)').matches ? 1.25 : 1.5));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
view.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.08;

// image-based lighting for soft, modern reflections
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

scene.add(new THREE.HemisphereLight(0xbfd3ff, 0x202024, 0.55));
const key = new THREE.DirectionalLight(0xffffff, 2.0);
key.position.set(0.12, 0.16, 0.30); scene.add(key);
const rim = new THREE.DirectionalLight(0x88aaff, 0.7);
rim.position.set(-0.2, -0.18, 0.10); scene.add(rim);

const grid = new THREE.GridHelper(0.3, 30, 0x262d38, 0x171c24);
grid.rotation.x = Math.PI / 2; scene.add(grid);
const axes = new THREE.AxesHelper(0.06); axes.visible = false; scene.add(axes);

// soft contact shadow blob under the drone
const shadow = new THREE.Mesh(new THREE.CircleGeometry(0.085, 48),
  new THREE.MeshBasicMaterial({color:0x000000, transparent:true, opacity:0.28}));
shadow.position.z = -0.0235; scene.add(shadow);

// ---- two model roots (styled / sdf) ---------------------------------------
const ROOTS = {styled:new THREE.Group(), sdf:new THREE.Group()};
scene.add(ROOTS.styled, ROOTS.sdf);
function makeGroups(root){const g={};for(const k of GROUPKEYS){g[k]=new THREE.Group();root.add(g[k]);}return g;}
const G = {styled:makeGroups(ROOTS.styled), sdf:makeGroups(ROOTS.sdf)};
const propMeshes = {styled:[], sdf:[], frame:[]};
let mode = 'frame';
// the embedded printed-frame STL is parsed further down into this group
const frameRoot = new THREE.Group(); scene.add(frameRoot); frameRoot.visible = false;

function reg(group, mesh){ mesh.userData.home = mesh.position.clone(); group.add(mesh); return mesh; }

// ===========================================================================
//  SDF primitive model (raw simulation geometry — validation mode)
// ===========================================================================
function sdfMatrix(pose){
  const [x,y,z,r,p,yw] = pose;
  const m = new THREE.Matrix4().makeRotationZ(yw)
    .multiply(new THREE.Matrix4().makeRotationY(p))
    .multiply(new THREE.Matrix4().makeRotationX(r));
  m.setPosition(x, y, z); return m;
}
for (const part of PARTS){
  let geo;
  if (part.type === 'box'){
    geo = new THREE.BoxGeometry(part.size[0], part.size[1], part.size[2]);
  } else {
    geo = new THREE.CylinderGeometry(part.radius, part.radius, part.length, 40);
    geo.rotateX(Math.PI/2);
  }
  const mat = new THREE.MeshStandardMaterial({
    color:new THREE.Color(part.color[0],part.color[1],part.color[2]),
    transparent: part.opacity<1, opacity: part.opacity,
    metalness:0.25, roughness:0.55, side:THREE.DoubleSide});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.applyMatrix4(sdfMatrix(part.pose));
  reg(G.sdf[part.group], mesh);
  if (part.group === 'props'){
    const blade = new THREE.Mesh(
      new THREE.BoxGeometry(part.radius*1.9, part.radius*0.16, 0.0016),
      new THREE.MeshStandardMaterial({color:mat.color, metalness:.2, roughness:.6}));
    blade.applyMatrix4(sdfMatrix(part.pose));
    blade.userData.dir = (part.name.endsWith('fr')||part.name.endsWith('bl'))?1:-1;
    reg(G.sdf.props, blade); propMeshes.sdf.push(blade);
  }
}

// ===========================================================================
//  Styled Tello-class model (procedural, PBR) — anchored to the SDF geometry
// ===========================================================================
const M = {
  bodyDark:  new THREE.MeshStandardMaterial({color:0x2b303a, metalness:.45, roughness:.42}),
  bodyLight: new THREE.MeshStandardMaterial({color:0xcdd2da, metalness:.25, roughness:.5}),
  canopy:    new THREE.MeshStandardMaterial({color:0x12151c, metalness:.5, roughness:.18}),
  accent:    new THREE.MeshStandardMaterial({color:0x2f6fed, metalness:.3, roughness:.35}),
  guard:     new THREE.MeshStandardMaterial({color:0x5b626d, metalness:.5, roughness:.4}),
  motor:     new THREE.MeshStandardMaterial({color:0x474d57, metalness:.85, roughness:.3}),
  hub:       new THREE.MeshStandardMaterial({color:0x383d45, metalness:.8, roughness:.32}),
  lens:      new THREE.MeshStandardMaterial({color:0x05070b, metalness:.2, roughness:.08}),
  led:       new THREE.MeshStandardMaterial({color:0x2f6fed, emissive:0x2f6fed, emissiveIntensity:1.4,
               metalness:0, roughness:.5}),
  propO:     new THREE.MeshStandardMaterial({color:0x2f6fed, metalness:.2, roughness:.4, side:THREE.DoubleSide}),
  propD:     new THREE.MeshStandardMaterial({color:0x20242c, metalness:.3, roughness:.45, side:THREE.DoubleSide}),
};

function rbox(w,d,h,r,mat){ return new THREE.Mesh(new RoundedBoxGeometry(w,d,h,4,Math.min(r,Math.min(w,d,h)/2-1e-4)), mat); }
function zcyl(rt,rb,h,mat,seg=36){ const g=new THREE.CylinderGeometry(rt,rb,h,seg); g.rotateX(Math.PI/2); return new THREE.Mesh(g,mat); }
function at(mesh,x,y,z,rz){ mesh.position.set(x,y,z); if(rz)mesh.rotation.z=rz; return mesh; }

// DJI-Tello-style blade: slim swept root, wide belly, rounded slightly-swept
// tip, concave trailing edge — a scimitar. `cw` mirrors it for CCW props.
function bladeMesh(r, mat, cw){
  const f = cw ? 1 : -1;
  const s = new THREE.Shape();
  s.moveTo(0.006, f*-0.0024);                                                  // root, leading edge
  s.bezierCurveTo(r*0.34, f*-0.0050, r*0.58, f*-0.0098, r*0.78, f*-0.0092);     // sweep out to wide belly
  s.bezierCurveTo(r*0.92, f*-0.0084, r*1.005, f*-0.0034, r*0.995, f*0.0012);    // rounded tip
  s.bezierCurveTo(r*0.965, f*0.0052, r*0.84, f*0.0068, r*0.64, f*0.0052);       // back of the tip
  s.bezierCurveTo(r*0.42, f*0.0034, r*0.22, f*0.0026, 0.006, f*0.0022);         // concave trailing edge -> root
  s.closePath();
  const g = new THREE.ExtrudeGeometry(s,{depth:0.0011, bevelEnabled:true,
    bevelThickness:0.00038, bevelSize:0.00038, bevelSegments:1, curveSegments:20});
  g.translate(0,0,-0.00055);
  const m = new THREE.Mesh(g, mat); m.rotation.x = f*0.30;   // blade pitch (matches spin sense)
  return m;
}
// real DJI-Tello propeller mesh (embedded STL: Ø77.9 mm, axis Z, hub centred).
let PROP_GEO = null;
(function(){
  const b64 = "__PROP_STL_B64__";
  if (!b64) return;
  const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  PROP_GEO = new STLLoader().parse(bin.buffer); PROP_GEO.computeVertexNormals();
})();
const PROP_S = 0.001 * (PROP_R / 0.038);     // STL mm -> m, scaled to the prop radius
function buildProp(cx,cy,cz, orange, cw){
  const grp = new THREE.Group(); grp.position.set(cx,cy,cz);
  if (PROP_GEO){
    const mat = (orange ? M.propO : M.propD).clone(); mat.side = THREE.DoubleSide;
    const m = new THREE.Mesh(PROP_GEO, mat);
    m.scale.set(PROP_S, cw ? PROP_S : -PROP_S, PROP_S);    // mirror Y for CCW props
    grp.add(m);
  } else {                                                 // procedural fallback
    grp.add(zcyl(0.0034,0.0050,0.0072, M.hub));
    const mat = orange ? M.propO : M.propD;
    for (let i=0;i<2;i++){ const b = bladeMesh(PROP_R, mat, cw); b.rotation.z = i*Math.PI; grp.add(b); }
  }
  return grp;
}
// a thin cylindrical strut between two 3-D points (for the guard posts)
function strutBetween(a, b, thick, mat){
  const len = a.distanceTo(b);
  const m = new THREE.Mesh(new THREE.CylinderGeometry(thick, thick, len, 8), mat);
  m.position.copy(a).add(b).multiplyScalar(0.5);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), b.clone().sub(a).normalize());
  return m;
}
// Prop guard placed AT THE PROPELLER PLANE (cz = prop height), held by three
// slim posts rising from the motor — a light, real prop-guard, not a ring down
// at the motor. The group sits at (cx,cy,cz) so it explodes radially too.
function buildGuard(cx,cy,cz){
  const grp = new THREE.Group(); grp.position.set(cx,cy,cz);
  const R = PROP_R + 0.003;                       // just outside the prop tips
  grp.add(new THREE.Mesh(new THREE.TorusGeometry(R, 0.0013, 12, 72), M.guard));
  const rIn = 0.0085, zIn = 0.013 - cz;           // motor-can top, local frame
  for (let k=0;k<3;k++){
    const a = k*2*Math.PI/3 + Math.PI/6;
    const p0 = new THREE.Vector3(Math.cos(a)*rIn, Math.sin(a)*rIn, zIn);
    const p1 = new THREE.Vector3(Math.cos(a)*R,   Math.sin(a)*R,   0);
    grp.add(strutBetween(p0, p1, 0.0011, M.guard));
  }
  return grp;
}

// sleek tapered fuselage planform (top view, FLU): pointed nose at +X, wide
// shoulders, rounded wide tail — a teardrop/wedge for an aggressive silhouette.
function hullShape(){
  const s = new THREE.Shape();
  s.moveTo(0.054, 0);                                   // nose tip
  s.bezierCurveTo(0.051,0.016, 0.030,0.031, 0.004,0.034);
  s.bezierCurveTo(-0.020,0.037, -0.039,0.031, -0.047,0.013);
  s.quadraticCurveTo(-0.052,0, -0.047,-0.013);          // round tail
  s.bezierCurveTo(-0.039,-0.031, -0.020,-0.037, 0.004,-0.034);
  s.bezierCurveTo(0.030,-0.031, 0.051,-0.016, 0.054,0);
  return s;
}
function extrudedFlat(shape, depth, bevel, mat){
  const g = new THREE.ExtrudeGeometry(shape, {depth, bevelEnabled:true,
    bevelThickness:bevel, bevelSize:bevel, bevelSegments:3, curveSegments:28});
  g.translate(0,0,-depth/2);
  return new THREE.Mesh(g, mat);
}
// a swept arm that tapers from a wide root to a slim motor end, rounded tip
function taperedArm(len, wRoot, wTip, h, mat){
  const s = new THREE.Shape();
  s.moveTo(0,-wRoot/2);
  s.lineTo(len,-wTip/2);
  s.quadraticCurveTo(len+wTip*0.55,0, len,wTip/2);
  s.lineTo(0,wRoot/2);
  s.closePath();
  const g = new THREE.ExtrudeGeometry(s,{depth:h, bevelEnabled:true,
    bevelThickness:0.0014, bevelSize:0.0014, bevelSegments:2, curveSegments:8});
  g.translate(0,0,-h/2);
  return new THREE.Mesh(g, mat);
}

function buildStyled(){
  const Gs = G.styled;
  const PROPZ = 0.0215;                 // propeller plane (guards sit here too)

  // ---- slim, low tapered hull (finer + lighter than the previous block) ----
  const hull = extrudedFlat(hullShape(), 0.013, 0.0035, M.bodyDark);
  hull.scale.set(1, 0.9, 1); hull.position.z = 0.004; reg(Gs.shell, hull);

  // ---- low faired canopy following the fuselage lines (clean, not a bubble) ----
  const canopy = extrudedFlat(hullShape(), 0.006, 0.003, M.canopy);
  canopy.scale.set(0.66, 0.55, 1); canopy.position.set(-0.004,0,0.0145);
  reg(Gs.shell, canopy);
  const stripe = rbox(0.046,0.004,0.0024,0.0012, M.accent);
  at(stripe,-0.004,0,0.0185); reg(Gs.shell, stripe);

  // ---- pronounced but slim camera nose (housing + lens + accent ring) ----
  const noseH = zcyl(0.006,0.0078,0.012, M.bodyLight).rotateY(Math.PI/2);
  noseH.position.set(0.05,0,0.004); reg(Gs.shell, noseH);
  const lensRing = zcyl(0.0052,0.0052,0.0035, M.accent).rotateY(Math.PI/2);
  lensRing.position.set(0.0555,0,0.004); reg(Gs.shell, lensRing);
  const lens = new THREE.Mesh(new THREE.SphereGeometry(0.0044,26,18), M.lens);
  lens.position.set(0.0565,0,0.004); reg(Gs.shell, lens);

  // ---- tail status LED + slim battery underside ----
  const led = rbox(0.014,0.0035,0.0024,0.0012, M.led);
  at(led,-0.046,0,0.006); reg(Gs.shell, led);
  const batt = rbox(0.028,0.026,0.011,0.003, M.bodyDark);
  at(batt,-0.022,0,-0.008); reg(Gs.shell, batt);

  // ---- slim landing feet ----
  for (const sx of [1,-1]) for (const sy of [1,-1]){
    const foot = zcyl(0.0026,0.0036,0.007, M.bodyDark);
    foot.position.set(sx*0.026, sy*0.022, -0.0105); reg(Gs.shell, foot);
  }

  // ---- per-motor: DOUBLE twin-strut arm (like the v2 frame), nacelle, motor,
  //      prop, prop-plane guard ----
  for (const mo of MOTORS){
    const ang = Math.atan2(mo.y, mo.x);
    const md = Math.hypot(mo.x, mo.y);
    const rRoot = 0.016;
    const bx = Math.cos(ang)*rRoot, by = Math.sin(ang)*rRoot;   // root near the body corner
    const px = -Math.sin(ang),      py = Math.cos(ang);          // perpendicular
    const off = 0.010;                                          // strut splay at the body
    for (const s of [-1, 1]){
      const rx = bx + s*off*px, ry = by + s*off*py;
      const a2 = Math.atan2(mo.y - ry, mo.x - rx);
      const len = Math.hypot(mo.x - rx, mo.y - ry);
      const strut = taperedArm(len + 0.004, 0.0072, 0.0052, 0.0052, M.bodyDark);
      strut.position.set(rx, ry, 0.001); strut.rotation.z = a2;
      reg(Gs.arms, strut);
    }

    const nac = zcyl(0.0078,0.0088,0.013, M.bodyDark);
    nac.position.set(mo.x, mo.y, 0.0055); reg(Gs.motors, nac);
    const can = zcyl(0.0055,0.0055,0.012, M.motor);
    can.position.set(mo.x, mo.y, 0.012); reg(Gs.motors, can);
    const shaft = zcyl(0.0013,0.0013,0.006, M.hub);
    shaft.position.set(mo.x, mo.y, 0.019); reg(Gs.motors, shaft);

    const orange = mo.name.endsWith('fr') || mo.name.endsWith('fl');
    const prop = buildProp(mo.x, mo.y, PROPZ, orange, (mo.x>0)===(mo.y<0));
    reg(Gs.props, prop); propMeshes.styled.push(prop);

    const guard = buildGuard(mo.x, mo.y, PROPZ);
    reg(Gs.guards, guard);
  }
}
buildStyled();

// ---- collision hull wireframe (shared) ------------------------------------
let hullMesh = null;
if (META.hull){
  const h = META.hull;
  hullMesh = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(h.size[0],h.size[1],h.size[2])),
    new THREE.LineBasicMaterial({color:0x3fb950}));
  hullMesh.applyMatrix4(sdfMatrix(h.pose));
  hullMesh.visible = false; scene.add(hullMesh);
}

// ---- mode + group visibility ----------------------------------------------
const groupVis = {shell:true,elec:true,arms:true,motors:true,props:true,guards:true};
function applyMode(){ ROOTS.styled.visible = mode==='styled'; ROOTS.sdf.visible = mode==='sdf';
  frameRoot.visible = mode==='frame'; }
function applyGroupVis(){
  for (const r of ['styled','sdf']) for (const k of GROUPKEYS) G[r][k].visible = groupVis[k];
  if (frameRoot.userData.shell)   frameRoot.userData.shell.visible   = groupVis.shell;
  if (frameRoot.userData.propsG)  frameRoot.userData.propsG.visible  = groupVis.props;
  if (frameRoot.userData.motorsG) frameRoot.userData.motorsG.visible = groupVis.motors;
  if (frameRoot.userData.elecG)   frameRoot.userData.elecG.visible   = groupVis.elec;
  if (frameRoot.userData.guardsG) frameRoot.userData.guardsG.visible = groupVis.guards;
}
applyMode(); applyGroupVis();

// ---- explode ---------------------------------------------------------------
const EXPLODE = {shell:[0,0], elec:[0,0], arms:[0.022,0], motors:[0.045,0.006],
                 props:[0.045,0.06], guards:[0.045,0.03]};
let explodeT = 0;
function applyExplode(t){
  explodeT = t;
  for (const r of ['styled','sdf']) for (const k of GROUPKEYS){
    const [kr,kz] = EXPLODE[k] || [0,0];
    for (const m of G[r][k].children){
      const h = m.userData.home; if(!h) continue;
      const rad = Math.hypot(h.x, h.y) || 1;
      m.position.set(h.x*(1 + t*kr/rad*8), h.y*(1 + t*kr/rad*8), h.z + t*kz);
    }
  }
  // printed frame: body sinks a touch, capot lifts off, motors pull out, props
  // lift highest (e[0] = gentle fractional radial spread, e[1] = z lift in m).
  frameRoot.traverse(o=>{
    const h=o.userData.home, e=o.userData.exp; if(!h||!e) return;
    o.position.set(h.x*(1 + t*e[0]), h.y*(1 + t*e[0]), h.z + t*e[1]);
  });
}

// ---- STL drag & drop (printed-frame overlay) ------------------------------
const stlGroup = new THREE.Group(); scene.add(stlGroup);
const stlLoader = new STLLoader(); let stlOpacity = 1;

// ---- embedded printed frame: lower body + capot (SEPARATE) + spinning props,
//      so the frame mode explodes apart and the "Hélices" toggle/spin work too.
const frameShell = new THREE.Group(), frameProps = new THREE.Group();
const frameMotors = new THREE.Group(), frameElec = new THREE.Group(), frameGuards = new THREE.Group();
frameRoot.add(frameShell, frameProps, frameMotors, frameElec, frameGuards);
frameRoot.userData.shell = frameShell; frameRoot.userData.propsG = frameProps;
frameRoot.userData.motorsG = frameMotors; frameRoot.userData.elecG = frameElec;
frameRoot.userData.guardsG = frameGuards;
let GUARD_GEO = null;
(function(){
  function geoFromB64(b64){
    if (!b64) return null;
    const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const g = stlLoader.parse(bin.buffer); g.computeVertexNormals(); return g;
  }
  function meshFromB64(b64, color, metal, rough){
    const g = geoFromB64(b64); if (!g) return null;
    const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({color, metalness:metal, roughness:rough}));
    m.scale.setScalar(0.001);        // OpenSCAD mm -> m
    m.rotation.z = Math.PI/2;        // frame -Y nose -> viewer +X (FLU forward)
    return m;
  }
  const body  = meshFromB64("__BODY_STL_B64__",  0x9298a3, .4,  .5);
  const capot = meshFromB64("__CAPOT_STL_B64__", 0x2f6fed, .35, .45);
  if (body){  body.userData.home={x:0,y:0,z:0};      body.userData.exp=[0,-0.004]; frameShell.add(body); }
  if (capot){ capot.position.z=0.013;                                    // rim joint (13 mm)
              capot.userData.home={x:0,y:0,z:0.013};  capot.userData.exp=[0, 0.020]; frameShell.add(capot); }
  frameRoot.userData.bodyMesh = body; frameRoot.userData.capotMesh = capot;  // for live recolour
  // --- front camera lens, same implantation as the SCAD site renders:
  //     barrel Ø8×3 flush with the nose wall, inner lens Ø4.6 (SCAD y=-36..-39
  //     -> viewer +X after the z+90° STL rotation, ×0.001 scale) ---
  const camBarrel = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.003, 32),
    new THREE.MeshStandardMaterial({color:0x101216, metalness:.3, roughness:.35}));
  camBarrel.rotation.z = Math.PI/2;               // cylinder Y axis -> X (forward)
  camBarrel.position.set(0.0375, 0, 0.0065);
  const camLens = new THREE.Mesh(new THREE.CylinderGeometry(0.0023, 0.0023, 0.0008, 32),
    new THREE.MeshStandardMaterial({color:0x3a4a63, metalness:.2, roughness:.08}));
  camLens.rotation.z = Math.PI/2;
  camLens.position.set(0.0388, 0, 0.0065);
  for (const m of [camBarrel, camLens]){
    m.userData.home = {x:m.position.x, y:m.position.y, z:m.position.z};
    m.userData.exp  = [0, -0.004];                // explodes with the body
    frameShell.add(m);
  }
  // --- mainboard (on the bosses, z=4.2 mm) + 1S pack (on the board, z=5.8 mm) ---
  const pcb = meshFromB64("__PCB_STL_B64__", 0x1f7a3d, .1, .7);
  if (pcb){ pcb.position.z=0.0042; pcb.userData.home={x:0,y:0,z:0.0042}; pcb.userData.exp=[0,-0.018]; frameElec.add(pcb); }
  const batt = meshFromB64("__BATT_STL_B64__", 0x2247c4, .2, .5);
  if (batt){ batt.position.z=0.0058+0.00475; batt.userData.home={x:0,y:0,z:0.0058+0.00475}; batt.userData.exp=[0,0.010]; frameElec.add(batt); }
  GUARD_GEO = geoFromB64("__GUARD_STL_B64__");
  for (const mo of MOTORS){
    const cw = (mo.x>0)===(mo.y<0);
    // --- prop guard (Tello-style): guard.stl is RIGID here (recentred on the C-clip's
    //     true bore — a circle fit on the clip's bottom rim, its cleanest circular
    //     section — no shear/distortion, so the ring stays a true undistorted circle).
    //     Placement dialled in by hand (live-slider panel, since removed): clip raised
    //     4 mm off the nacelle's foot and nudged 9 mm out along the motor radius, clear
    //     of both the arm beam and the motor can; +20% scale so the bore wraps the
    //     nacelle + arm-root junction snugly. ---
    if (GUARD_GEO){
      const a = Math.atan2(mo.y, mo.x);
      const g = new THREE.Mesh(GUARD_GEO, new THREE.MeshStandardMaterial({color:0x2b2e33, metalness:.25, roughness:.7}));
      g.scale.set(0.0012, 0.0012, 0.00069);
      g.rotation.z = a;
      const grp = new THREE.Group(); grp.add(g);
      grp.position.set(mo.x + 0.009*Math.cos(a), mo.y + 0.009*Math.sin(a), 0.004);
      grp.userData.home={x:grp.position.x, y:grp.position.y, z:0.004}; grp.userData.exp=[0.05, 0.026];
      frameGuards.add(grp);
    }
    // --- 8520 motor pressed into the pod (visible can + bell where prop clips) ---
    const can = zcyl(0.00425,0.00425,0.020, M.motor);    // 8.5 mm Ø, 20 mm
    can.position.set(0, 0, 0.010);                        // local to the motor group
    const bell = zcyl(0.0044,0.0040,0.005, M.bodyDark);   // top bell
    bell.position.set(0, 0, 0.0195);
    const mgrp = new THREE.Group(); mgrp.add(can, bell);
    mgrp.position.set(mo.x, mo.y, 0);
    mgrp.userData.home={x:mo.x, y:mo.y, z:0}; mgrp.userData.exp=[0.04, 0.006];
    frameMotors.add(mgrp);
    // --- real Tello prop on top (orange front, dark rear for orientation) ---
    const orange = mo.name.endsWith('fr') || mo.name.endsWith('fl');
    const prop = buildProp(mo.x, mo.y, 0.0205, orange, cw);
    prop.userData.home={x:mo.x, y:mo.y, z:0.0205}; prop.userData.exp=[0.04, 0.030];
    prop.userData.dir = cw ? 1 : -1;
    prop.userData.front = orange;                 // front (fr/fl) vs rear, for live recolour
    frameProps.add(prop); propMeshes.frame.push(prop);
  }
})();
function addSTL(name, buf){
  const geo = stlLoader.parse(buf); geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({color:0x58a6ff,
    transparent:true, opacity:stlOpacity, metalness:.1, roughness:.7, side:THREE.DoubleSide}));
  mesh.scale.setScalar(0.001);                 // OpenSCAD STLs are in mm
  stlGroup.add(mesh);
  document.getElementById('stlList').innerHTML += `<div>+ ${name}</div>`;
}
const drop = document.getElementById('drop');
function readFiles(files){ for (const f of files){ if(!f.name.toLowerCase().endsWith('.stl'))continue;
  const rd = new FileReader(); rd.onload = e => addSTL(f.name, e.target.result); rd.readAsArrayBuffer(f); } }
['dragenter','dragover'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add('hot');}));
['dragleave','drop'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove('hot');}));
drop.addEventListener('drop', e=>readFiles(e.dataTransfer.files));
drop.addEventListener('click', ()=>{const i=document.createElement('input');i.type='file';i.accept='.stl';
  i.multiple=true; i.onchange=()=>readFiles(i.files); i.click();});
document.getElementById('stlOp').addEventListener('input', e=>{ stlOpacity=e.target.value/100;
  document.getElementById('stlOpV').textContent=e.target.value+'%';
  stlGroup.traverse(o=>{ if(o.material) o.material.opacity=stlOpacity; }); });

// ---- UI: component toggles -------------------------------------------------
const gEl = document.getElementById('groups');
for (const k of GROUPKEYS){
  const lab = document.createElement('label'); lab.className='tog';
  lab.innerHTML = `<input type="checkbox" checked data-g="${k}">
    <span class="sw" style="background:${GROUPS[k].color}"></span>${GROUPS[k].label}`;
  gEl.appendChild(lab);
}
gEl.addEventListener('change', e=>{ const k=e.target.dataset.g; if(!k)return;
  groupVis[k]=e.target.checked; applyGroupVis(); });

// ---- UI: model mode --------------------------------------------------------
const mStyled=document.getElementById('mStyled'), mSdf=document.getElementById('mSdf'),
      mFrame=document.getElementById('mFrame');
function setMode(x){ mode=x; mStyled.classList.toggle('on',x==='styled');
  mSdf.classList.toggle('on',x==='sdf'); mFrame.classList.toggle('on',x==='frame'); applyMode(); }
mStyled.onclick=()=>setMode('styled'); mSdf.onclick=()=>setMode('sdf'); mFrame.onclick=()=>setMode('frame');

// ---- UI: display toggles + sliders ----------------------------------------
let wire=false, spinRate=0;
const bWire=document.getElementById('bWire'), bGrid=document.getElementById('bGrid'),
      bAxes=document.getElementById('bAxes'), bHull=document.getElementById('bHull');
bWire.onclick=()=>{wire=!wire; bWire.classList.toggle('on',wire);
  for (const root of [ROOTS.styled, ROOTS.sdf, frameRoot]) root.traverse(o=>{ if(o.material&&o.material.wireframe!==undefined) o.material.wireframe=wire; });};
bGrid.onclick=()=>{grid.visible=!grid.visible; bGrid.classList.toggle('on',grid.visible);};
bAxes.onclick=()=>{axes.visible=!axes.visible; bAxes.classList.toggle('on',axes.visible);};
bHull.onclick=()=>{ if(hullMesh){hullMesh.visible=!hullMesh.visible; bHull.classList.toggle('on',hullMesh.visible);} };
document.getElementById('explode').addEventListener('input', e=>{ applyExplode(e.target.value/100);
  document.getElementById('explodeV').textContent=e.target.value+'%';});
document.getElementById('spin').addEventListener('input', e=>{ spinRate=e.target.value/100*48;
  document.getElementById('spinV').textContent=e.target.value==0?'arrêt':e.target.value+'%';});

// ---- dimensions table + HUD -----------------------------------------------
const d = META.dims;
document.getElementById('dims').innerHTML = `
  <tr><td>Entraxe (diag. moteurs)</td><td class="v">${d.wheelbase_mm} mm</td></tr>
  <tr><td>Ø hélice</td><td class="v">${d.prop_d_mm} mm</td></tr>
  <tr><td>Envergure tip-to-tip</td><td class="v">${d.tip_mm} mm</td></tr>
  <tr><td>Longueur (X)</td><td class="v">${d.len_mm} mm</td></tr>
  <tr><td>Largeur (Y)</td><td class="v">${d.wid_mm} mm</td></tr>
  <tr><td>Hauteur (Z)</td><td class="v">${d.hgt_mm} mm</td></tr>
  <tr><td>Masse (sim)</td><td class="v">${d.mass_g} g</td></tr>`;
document.getElementById('hud').innerHTML =
  `entraxe <b>${d.wheelbase_mm}mm</b> · Ø hélice <b>${d.prop_d_mm}mm</b> ·
   tip-to-tip <b>${d.tip_mm}mm</b> · <b>${d.mass_g}g</b>`;

// ---- camera presets --------------------------------------------------------
const R = 0.2;
const VIEWS = {iso:[R*0.85,-R*0.85,R*0.55], top:[0.0001,0,R*1.15],
               front:[R*1.25,0,0.02], side:[0,-R*1.25,0.02]};
function setView(v){ const p=VIEWS[v]||VIEWS.iso; camera.position.set(p[0],p[1],p[2]);
  controls.target.set(0,0,0.004); controls.update(); }
document.querySelectorAll('[data-view]').forEach(b=> b.onclick=()=>setView(b.dataset.view));
setView('iso');

// ---- resize + render loop --------------------------------------------------
function resize(){ const w=view.clientWidth,h=view.clientHeight;
  renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();

// ===========================================================================
//  URL params & host messaging — embed (configurator preview) / playground
// ===========================================================================
const PARAMS = new URLSearchParams(location.search);
const EMBED  = PARAMS.has('embed');
const PLAY   = PARAMS.has('playground');

// bounded zoom: tight for inspection, wide for the flight playground
if (PLAY)       { controls.minDistance = 0.3;  controls.maxDistance = 14;  }
else if (EMBED) { controls.minDistance = 0.12; controls.maxDistance = 0.9; }
else            { controls.minDistance = 0.05; controls.maxDistance = 0.6; }

// embed: frame the WHOLE drone whatever the iframe's aspect ratio — fit the
// bounding sphere against the smaller of the vertical/horizontal FOV.
function fitEmbed(){
  if (!EMBED) return;
  const sph = new THREE.Box3().setFromObject(frameRoot)
                .getBoundingSphere(new THREE.Sphere());
  const vFov = camera.fov * Math.PI / 180;
  const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
  const dist = sph.radius / Math.sin(Math.min(vFov, hFov) / 2) * 1.18;
  const dir = new THREE.Vector3(0.85, -0.85, 0.55).normalize();
  camera.position.copy(sph.center).addScaledVector(dir, dist);
  controls.target.copy(sph.center);
  controls.update();
}
addEventListener('resize', fitEmbed);   // runs after the base resize handler

// ---- live per-part recolour of the printed-frame model --------------------
function setPartColor(part, hex){
  if (!hex) return;
  const c = new THREE.Color(hex);
  const u = frameRoot.userData;
  if (part === 'body'  && u.bodyMesh)  u.bodyMesh.material.color.copy(c);
  if (part === 'capot' && u.capotMesh) u.capotMesh.material.color.copy(c);
  if (part === 'pf' || part === 'pr'){
    const wantFront = (part === 'pf');
    for (const pr of propMeshes.frame){
      if (!!pr.userData.front !== wantFront) continue;
      pr.traverse(o => { if (o.isMesh) o.material.color.copy(c); });
    }
  }
}
function applyColors(o){
  if (!o) return;
  setPartColor('body',  o.body);
  setPartColor('capot', o.capot);
  setPartColor('pf',    o.propFront != null ? o.propFront : o.pf);
  setPartColor('pr',    o.propRear  != null ? o.propRear  : o.pr);
}
applyColors({ body:PARAMS.get('body'), capot:PARAMS.get('capot'),
              pf:PARAMS.get('pf'), pr:PARAMS.get('pr') });
addEventListener('message', e => {
  const m = e.data;
  if (m && m.type === 'colors'){ applyColors(m); window.__lastColors = m; }
});

if (EMBED || PLAY){
  document.body.classList.add(EMBED ? 'embed' : 'playground');
  mode = 'frame'; applyMode();
  resize();          // the side panel just changed -> recompute canvas + aspect
  fitEmbed();
}
// tell the host we're ready so the configurator can (re)send its colours
try { if (parent && parent !== window) parent.postMessage({type:'ready'}, '*'); } catch(_){}

// ===========================================================================
//  Playground — a tiny in-browser flight sim: a Tello-SDK script drives the
//  drone over the grid. Verbs & ranges mirror fc_core/src/fc_sdk.c; the
//  kinematics imitate fc_core/src/fc_params.c (speed 1 m/s, yaw ~96 dps,
//  takeoff 0.8 m, land 0.45 m/s). Pure client-side — no Python, no network.
// ===========================================================================
const PG = (function(){
  if (!PLAY) return null;
  const DEG = Math.PI/180, SPEED0 = 1.0, YAW_RATE = 96*DEG;
  const CLIMB = 0.42, DESC = 0.45, TAKEOFF_Z = 0.8;
  const SPACING = 0.8, MAXD = 6;      // formation pitch (spawn_swarm.sh: 0.8 m in Y)
  const $ = id => document.getElementById(id);
  const logEl = $('pgLog');
  function log(msg, cls){ const d=document.createElement('div');
    if(cls) d.className=cls; d.textContent=msg; logEl.appendChild(d);
    logEl.scrollTop = logEl.scrollHeight; }

  // ---- the fleet: drones[0] wraps frameRoot; extras are deep clones -------
  // (clone children individually: frameRoot.userData holds mesh refs that
  //  Object3D.clone() would try to JSON-copy). Materials are shared by
  //  reference, so the configurator recolour applies to every drone.
  const st = { armed:false, running:false, queue:[], cur:null, timer:0 };
  const drones = [];
  function collectProps(root){ const out=[];
    root.traverse(o=>{ if (o.userData && o.userData.dir!==undefined && o.userData.front!==undefined) out.push(o); });
    return out; }
  function mkClone(){
    const g = new THREE.Group();
    for (const ch of frameRoot.children) g.add(ch.clone(true));
    scene.add(g); return g; }
  function homeY(k, n){ return (k - (n-1)/2) * SPACING; }
  function spawn(n){
    n = Math.max(1, Math.min(MAXD, Math.round(n)));
    while (drones.length > n){ const d = drones.pop(); if (d.root !== frameRoot) scene.remove(d.root); }
    if (!drones.length) drones.push({root:frameRoot, props:collectProps(frameRoot)});
    while (drones.length < n){ const r = mkClone(); drones.push({root:r, props:collectProps(r)}); }
    drones.forEach((d, k) => {
      d.yaw=0; d.flying=false; d.bat=100; d.speed=SPEED0; d.job=null; d.flip=null;
      d.root.position.set(0, homeY(k, n), 0); d.root.rotation.set(0, 0, 0);
    });
    readout();
  }
  function readout(){
    const n = drones.length, flying = drones.filter(d=>d.flying).length;
    $('pgN').textContent = n + (flying ? ' · ' + flying + ' en vol' : ' au sol');
    $('pgBat').textContent = Math.max(0,Math.round(Math.min.apply(null, drones.map(d=>d.bat)))) + ' %';
    $('pgAlt').textContent = Math.round(Math.max.apply(null, drones.map(d=>d.root.position.z))*100) + ' cm';
    let deg = Math.round((drones[0]?drones[0].yaw:0)/DEG) % 360; if (deg<0) deg+=360;
    $('pgYaw').textContent = deg + '°';
    $('pgCmd').textContent = st.cur ? st.cur.raw : (st.running ? '—' : 'prêt');
  }

  // ---- tiny safe arithmetic in the drone index i (numbers + - * / parens) --
  // mirrors swarm.parallel(lambda i, t: ...) staggering, e.g. go 60+40*i (i-1)*80 0 60
  function evalExpr(src, i){
    const s = String(src); let p = 0;
    function fail(){ throw new Error('expr'); }
    function prim(){
      if (s[p]==='('){ p++; const v=sum(); if (s[p]!==')') fail(); p++; return v; }
      if (s[p]==='-'){ p++; return -prim(); }
      if (s[p]==='+'){ p++; return prim(); }
      if (s[p]==='i'){ p++; return i; }
      const m = /^\d+(\.\d+)?/.exec(s.slice(p)); if (!m) fail();
      p += m[0].length; return parseFloat(m[0]);
    }
    function prod(){ let v=prim(); for(;;){ if (s[p]==='*'){p++; v*=prim();}
      else if (s[p]==='/'){p++; v/=prim();} else return v; } }
    function sum(){ let v=prod(); for(;;){ if (s[p]==='+'){p++; v+=prod();}
      else if (s[p]==='-'){p++; v-=prod();} else return v; } }
    const v = sum(); if (p !== s.length) fail(); return v;
  }

  const MOVES = {forward:1,back:1,left:1,right:1,up:1,down:1};
  const ALIAS = { takeoff:'takeoff', land:'land', move_forward:'forward', move_back:'back',
    move_left:'left', move_right:'right', move_up:'up', move_down:'down',
    rotate_clockwise:'cw', rotate_counter_clockwise:'ccw', flip:'flip',
    set_speed:'speed', go_xyz_speed:'go', curve_xyz_speed:'curve',
    sleep:'sleep', time_sleep:'sleep' };
  function normalize(line){
    let s = line.replace(/#.*$/,'').replace(/;+\s*$/,'').trim(); if (!s) return '';
    const m = s.match(/^([A-Za-z_.]+)\s*\((.*)\)\s*$/);
    if (m){ const verb = ALIAS[m[1].replace('.','_')] || m[1];
      const args = m[2].split(',').map(a=>a.trim().replace(/^['"]|['"]$/g,'')).filter(a=>a.length);
      return (verb + ' ' + args.join(' ')).trim(); }
    const t = s.split(/\s+/); if (ALIAS[t[0]]) t[0]=ALIAS[t[0]]; return t.join(' ');
  }
  // numeric args stay as EXPRESSION STRINGS, evaluated per drone at dispatch
  function parse(line){
    const s = normalize(line); if (!s) return null;
    const t = s.split(/\s+/), op = t[0].toLowerCase();
    if (['command','takeoff','land','stop','emergency','streamon','streamoff'].includes(op))
      return {op, raw:s};
    if (MOVES[op] || op==='cw' || op==='ccw' || op==='speed' || op==='sleep' || op==='drones'){
      if (t.length < 2) return {error:'error (argument manquant)', raw:s};
      return {op, e:[t[1]], raw:s};
    }
    if (op==='flip'){ const dir=(t[1]||'').replace(/^['"]|['"]$/g,'');
      if (!/^[lrfb]$/.test(dir)) return {error:'error (l/r/f/b)', raw:s}; return {op, dir, raw:s}; }
    if (op==='go'){ if (t.length < 5) return {error:'error (go x y z speed)', raw:s};
      return {op, e:[t[1],t[2],t[3],t[4]], raw:s}; }
    if (op==='curve'){ if (t.length < 8) return {error:'error (curve x1 y1 z1 x2 y2 z2 speed)', raw:s};
      return {op, e:[t[1],t[2],t[3],t[4],t[5],t[6],t[7]], raw:s}; }
    if (op==='rc') return {op:'noop', raw:s};
    if (op.endsWith('?')) return {op:'query', q:op, raw:s};
    return {error:'unknown command', raw:s};
  }
  function evalArgs(c, i){
    try { return (c.e||[]).map(x=>evalExpr(x, i)); }
    catch(_){ return null; }
  }
  function abort(msg){ log(msg,'err'); st.queue=[]; st.cur=null; st.running=false; readout(); }
  const RANGE = {move:[20,500], rot:[1,360], speed:[10,100], sleep:[0.1,10], drones:[1,MAXD], go:[-500,500], gospd:[10,100]};
  function next(){
    if (!st.queue.length){ st.cur=null; st.running=false; readout(); return; }
    const c = st.queue.shift(); st.cur = c;
    if (c.op!=='command' && !st.armed) return abort(c.raw+' → error (envoyez "command" d\'abord)');
    const needFly = MOVES[c.op] || ['cw','ccw','go','curve','flip','land'].includes(c.op);
    if (needFly && drones.some(d=>!d.flying)) return abort(c.raw+' → error (drone au sol)');
    log(c.raw,'cmd');
    if (c.op==='command'){ st.armed=true; return done('ok'); }
    if (c.op==='drones'){ const v=evalArgs(c,0);
      if (!v || !(v[0]>=RANGE.drones[0] && v[0]<=RANGE.drones[1])) return abort('→ error (drones 1-'+MAXD+')');
      spawn(v[0]); return done('ok'); }
    if (c.op==='sleep'){ const v=evalArgs(c,0);
      if (!v || !(v[0]>=RANGE.sleep[0] && v[0]<=RANGE.sleep[1])) return abort('→ error (sleep 0.1-10 s)');
      st.timer=v[0]; readout(); return; }
    if (c.op==='speed'){ const v=evalArgs(c,0);
      if (!v || !(v[0]>=10 && v[0]<=100)) return abort('→ error (speed 10-100)');
      drones.forEach(d=>d.speed=v[0]/100); return done('ok'); }
    if (c.op==='query'){
      const v = c.q==='battery?' ? Math.round(Math.min.apply(null, drones.map(d=>d.bat)))
            : c.q==='height?' ? Math.round(drones[0].root.position.z*100)
            : c.q==='sdk?' ? 20 : 'ok';
      return done(String(v)); }
    if (c.op==='noop' || c.op==='stop' || c.op==='streamon' || c.op==='streamoff' || c.op==='emergency')
      return done('ok');
    // per-drone motion jobs (parallel; command completes when ALL finish)
    for (let k=0;k<drones.length;k++){
      const d = drones[k], p = d.root.position;
      const fx = Math.cos(d.yaw), fy = Math.sin(d.yaw);
      const job = {op:c.op};
      if (c.op==='takeoff') job.tz = TAKEOFF_Z;
      else if (c.op==='land') job.tz = 0;
      else if (c.op==='flip'){
        if (p.z < 0.6) return abort('→ error (trop bas pour un flip)');
        job.flip={axis:(c.dir==='f'||c.dir==='b')?'x':'y',
                  sign:(c.dir==='f'||c.dir==='l')?-1:1, t:0, dur:0.6};
      } else {
        const v = evalArgs(c, k); if (!v) return abort('→ error (expression)');
        if (MOVES[c.op]){
          if (!(v[0]>=RANGE.move[0] && v[0]<=RANGE.move[1])) return abort('→ error (20-500 cm)');
          const dst = v[0]/100;
          if (c.op==='forward'){ job.tx=p.x+fx*dst; job.ty=p.y+fy*dst; job.tz2=p.z; }
          else if (c.op==='back'){ job.tx=p.x-fx*dst; job.ty=p.y-fy*dst; job.tz2=p.z; }
          else if (c.op==='left'){ job.tx=p.x-fy*dst; job.ty=p.y+fx*dst; job.tz2=p.z; }
          else if (c.op==='right'){ job.tx=p.x+fy*dst; job.ty=p.y-fx*dst; job.tz2=p.z; }
          else if (c.op==='up'){ job.tx=p.x; job.ty=p.y; job.tz2=p.z+dst; }
          else { job.tx=p.x; job.ty=p.y; job.tz2=Math.max(0.05,p.z-dst); }
          job.spd=d.speed;
        } else if (c.op==='go'){
          if (v.slice(0,3).some(x=>!(x>=RANGE.go[0]&&x<=RANGE.go[1])) ||
              !(v[3]>=RANGE.gospd[0]&&v[3]<=RANGE.gospd[1])) return abort('→ error (range)');
          job.tx=p.x+fx*(v[0]/100)-fy*(v[1]/100);
          job.ty=p.y+fy*(v[0]/100)+fx*(v[1]/100);
          job.tz2=Math.max(0.05,p.z+v[2]/100); job.spd=v[3]/100;
        } else if (c.op==='curve'){
          // quadratic Bézier through the mid waypoint — fc_sdk: coords ±500, speed 10-60
          if (v.slice(0,6).some(x=>!(x>=RANGE.go[0]&&x<=RANGE.go[1])) ||
              !(v[6]>=10&&v[6]<=60)) return abort('→ error (curve: ±500 cm, speed 10-60)');
          const bod=(x,y,z)=>({x:p.x+fx*(x/100)-fy*(y/100),
                               y:p.y+fy*(x/100)+fx*(y/100),
                               z:Math.max(0.05,p.z+z/100)});
          job.b0={x:p.x,y:p.y,z:p.z}; job.b1=bod(v[0],v[1],v[2]); job.b2=bod(v[3],v[4],v[5]);
          let len=0, px=job.b0.x, py=job.b0.y, pz=job.b0.z;
          for (let q=1;q<=20;q++){ const s=q/20, a=(1-s)*(1-s), m=2*(1-s)*s, bq=s*s;
            const qx=a*job.b0.x+m*job.b1.x+bq*job.b2.x, qy=a*job.b0.y+m*job.b1.y+bq*job.b2.y,
                  qz=a*job.b0.z+m*job.b1.z+bq*job.b2.z;
            len+=Math.hypot(qx-px,qy-py,qz-pz); px=qx; py=qy; pz=qz; }
          job.T=Math.max(0.2, len/(v[6]/100)); job.t=0;
        } else if (c.op==='cw' || c.op==='ccw'){
          if (!(v[0]>=RANGE.rot[0] && v[0]<=RANGE.rot[1])) return abort('→ error (1-360°)');
          job.dyaw=(c.op==='cw'?-1:1)*v[0]*DEG; job.yaw0=d.yaw; job.acc=0;
        }
      }
      d.job = job;
    }
    readout();
  }
  function done(reply){ if (reply) log('→ '+reply,'ok');
    st.cur=null; next(); }
  function stepDrone(d, dt){
    const j = d.job; if (!j) return true;
    const p = d.root.position;
    if (j.flip){ const f=j.flip; f.t+=dt;
      const a=Math.min(1,f.t/f.dur)*2*Math.PI*f.sign;
      if (f.axis==='x') d.root.rotation.x=a; else d.root.rotation.y=a;
      if (f.t>=f.dur){ d.root.rotation.x=0; d.root.rotation.y=0; d.job=null; return true; }
      return false; }
    if (j.op==='takeoff'){ p.z=Math.min(j.tz,p.z+CLIMB*dt);
      if (p.z>=j.tz-1e-4){ d.flying=true; d.job=null; return true; } return false; }
    if (j.op==='land'){ p.z=Math.max(0,p.z-DESC*dt);
      if (p.z<=1e-4){ p.z=0; d.flying=false; d.job=null; return true; } return false; }
    if (j.op==='curve'){ j.t+=dt; const s=Math.min(1, j.t/j.T);
      const a=(1-s)*(1-s), m=2*(1-s)*s, bq=s*s;
      p.set(a*j.b0.x+m*j.b1.x+bq*j.b2.x,
            a*j.b0.y+m*j.b1.y+bq*j.b2.y,
            a*j.b0.z+m*j.b1.z+bq*j.b2.z);
      if (s>=1){ d.job=null; return true; } return false; }
    if (j.op==='cw' || j.op==='ccw'){ const s=YAW_RATE*dt; j.acc+=s;
      if (j.acc>=Math.abs(j.dyaw)){ d.yaw=j.yaw0+j.dyaw; d.root.rotation.z=d.yaw; d.job=null; return true; }
      d.yaw += Math.sign(j.dyaw)*s; d.root.rotation.z=d.yaw; return false; }
    if (j.tx!==undefined){ const dx=j.tx-p.x, dy=j.ty-p.y, dz=j.tz2-p.z;
      const dist=Math.hypot(dx,dy,dz), s=(j.spd||d.speed)*dt;
      if (dist<=Math.max(s,0.02)){ p.set(j.tx,j.ty,j.tz2); d.job=null; return true; }
      p.x+=dx/dist*s; p.y+=dy/dist*s; p.z+=dz/dist*s; return false; }
    d.job=null; return true;
  }
  function step(dt){
    if (st.running || drones.some(d=>d.flying))
      drones.forEach(d=>{ d.bat=Math.max(0,d.bat-dt*0.25); });
    for (const d of drones) if (d.flying || d.job)
      for (const pr of d.props)
        pr.rotateOnAxis(PROP_SPIN, 26*dt*(pr.userData.dir||1));
    if (st.timer > 0){ st.timer -= dt;
      if (st.timer <= 0 && st.cur && st.cur.op==='sleep'){ st.timer=0; done('ok'); }
      readout(); return; }
    // advance per-drone jobs — from the script command OR manual keyboard T/L/F
    let pending = false;
    for (const d of drones) if (d.job && !stepDrone(d, dt)) pending = true;
    if (st.cur){
      if (!pending && drones.every(d=>!d.job)) done('ok');
    } else if (kbd.on && !st.queue.length){
      // free flight: rc-style velocities (fc_params: xy 1.5 m/s, z 1.0 m/s)
      // arrows = translate (fwd/back/left/right) · z/w = climb/descend · q/d = yaw
      const K = kbd.k;
      const vf = ((K.ArrowUp?1:0)-(K.ArrowDown?1:0))*1.5;
      const vl = ((K.ArrowLeft?1:0)-(K.ArrowRight?1:0))*1.5;
      const vz = ((K.z?1:0)-(K.w?1:0))*1.0;
      const wz = ((K.q?1:0)-(K.d?1:0))*YAW_RATE;
      if (vf||vl||vz||wz) for (const d of drones){
        if (!d.flying || d.job) continue;
        d.yaw += wz*dt; d.root.rotation.z = d.yaw;
        const fx=Math.cos(d.yaw), fy=Math.sin(d.yaw), p=d.root.position;
        p.x = Math.max(-2.9, Math.min(2.9, p.x + (fx*vf - fy*vl)*dt));
        p.y = Math.max(-2.9, Math.min(2.9, p.y + (fy*vf + fx*vl)*dt));
        p.z = Math.max(0.05, Math.min(5,  p.z + vz*dt));
      }
    }
    readout();
  }

  // ---- manual keyboard flight (playground, when no script is running) ------
  const kbd = {on:false, k:Object.create(null)};
  const kbtn = $('pgKbd');
  kbtn.addEventListener('click', ()=>{
    kbd.on = !kbd.on; kbtn.classList.toggle('on', kbd.on);
    kbtn.textContent = kbd.on ? '🎮 Pilotage clavier : ON' : '🎮 Pilotage clavier : OFF';
    log(kbd.on ? 'clavier activé — T pour décoller' : 'clavier désactivé', 'ok');
  });
  // letters are tracked by the character TYPED (layout-independent naming:
  // Z climbs on AZERTY and QWERTY alike); arrows by their code.
  function keyTok(e){ return e.key.length === 1 ? e.key.toLowerCase() : e.code; }
  addEventListener('keydown', e=>{
    if (!kbd.on) return;
    const tag = (e.target && e.target.tagName) || '';
    if (/TEXTAREA|INPUT|SELECT/.test(tag)) return;
    if (/^Arrow/.test(e.code) || e.code==='Space') e.preventDefault();
    const t = keyTok(e);
    kbd.k[t] = true;
    if (e.repeat || st.cur || st.queue.length) return;
    if (t==='t'){ st.armed = true;
      drones.forEach(d=>{ if (!d.flying && !d.job) d.job = {op:'takeoff', tz:TAKEOFF_Z}; });
      log('T → takeoff', 'cmd'); }
    if (t==='l'){
      drones.forEach(d=>{ if (d.flying && !d.job) d.job = {op:'land', tz:0}; });
      log('L → land', 'cmd'); }
    if (t==='f'){
      drones.forEach(d=>{ if (d.flying && !d.job && d.root.position.z > 0.6)
        d.job = {flip:{axis:'x', sign:-1, t:0, dur:0.6}}; });
      log('F → flip', 'cmd'); }
  });
  addEventListener('keyup', e=>{ kbd.k[keyTok(e)] = false; });
  function reset(clearLog){
    st.armed=false; st.running=false; st.queue=[]; st.cur=null; st.timer=0;
    spawn(defaultN);
    if (clearLog) logEl.innerHTML='';
    readout();
  }
  function run(){
    st.armed=false; st.running=false; st.queue=[]; st.cur=null; st.timer=0;
    drones.forEach((d,k)=>{ d.yaw=0; d.flying=false; d.bat=100; d.speed=SPEED0; d.job=null;
      d.root.position.set(0, homeY(k, drones.length), 0); d.root.rotation.set(0,0,0); });
    logEl.innerHTML='';
    const cmds=[];
    for (const ln of $('pgCode').value.split('\n')){ const pr=parse(ln); if (!pr) continue;
      if (pr.error){ log(ln.trim()+' → '+pr.error,'err'); readout(); return; } cmds.push(pr); }
    if (!cmds.length) return;
    if (cmds[0].op!=='command'){ log('→ error : commencez le script par "command"','err'); return; }
    st.queue=cmds; st.running=true; next();
  }

  // ---- presets: faithful mirrors of sdk/python/examples/*.py ---------------
  const PRESETS = {
    hover: ['# 01_hover.py — décoller, planer 5 s, atterrir','command','takeoff',
            'sleep 5','land'].join('\n'),
    square: ['# 02_square.py — carré de 1 m (go_xyz_speed + rotate_clockwise)','command','takeoff',
             'go 100 0 0 50','cw 90','go 100 0 0 50','cw 90',
             'go 100 0 0 50','cw 90','go 100 0 0 50','cw 90','land'].join('\n'),
    swarm: ['# 03_swarm.py — essaim de 3 : jambes parallèles indexées par i',
            'command','drones 3','takeoff',
            'go 60+40*i (i-1)*80 0 60','cw 120*(i+1)','land'].join('\n'),
    freestyle: ['# ★ Bonus (hors dépôt) — curves + flips, effet dynamique',
            'command','drones 3','takeoff','up 30+20*i',
            'flip f','curve 80 (i-1)*60 20 160 0 0 60',
            'flip b','curve 80 (1-i)*60 -20 160 0 0 50',
            'cw 120+60*i','flip l','land'].join('\n'),
  };
  for (const [id, key] of [['pgP1','hover'],['pgP2','square'],['pgP3','swarm'],['pgP4','freestyle']])
    $(id).addEventListener('click', ()=>{ $('pgCode').value = PRESETS[key]; });
  $('pgRun').addEventListener('click', run);
  $('pgReset').addEventListener('click', ()=>{ reset(true); log('réinitialisé','ok'); });

  grid.visible = false; shadow.visible = false;
  const bigGrid = new THREE.GridHelper(6, 60, 0x262d38, 0x141922);
  bigGrid.rotation.x = Math.PI/2; scene.add(bigGrid);
  camera.position.set(2.7,-2.7,1.8); controls.target.set(0,0,0.35); controls.update();

  const defaultN = Math.max(1, Math.min(MAXD, parseInt(PARAMS.get('drones')||'1',10) || 1));
  const preset = (PARAMS.get('preset')||'').toLowerCase();
  if (PRESETS[preset]) $('pgCode').value = PRESETS[preset];
  reset(true);
  // debug/test hook: pose of drone 1
  window.__pgState = () => ({ x:+drones[0].root.position.x.toFixed(3),
    y:+drones[0].root.position.y.toFixed(3), z:+drones[0].root.position.z.toFixed(3),
    yaw:+drones[0].yaw.toFixed(3) });
  return { step };
})();

const clock = new THREE.Clock();
const PROP_SPIN = new THREE.Vector3(0,0,1);

// Only render while actually on screen: with several viewers embedded in
// one page, offscreen 60 fps loops are what makes scrolling stutter.
// (IntersectionObserver in a same-origin iframe tracks visibility within
// the TOP page's viewport, so each embed pauses itself when scrolled out.)
let ioVisible = true, looping = false, hostControlled = false;
window.__vizRendering = () => looping;
function startLoop(){ if (!looping){ looping = true; clock.getDelta(); requestAnimationFrame(loop); } }
function active(){ return ioVisible && !document.hidden; }
// embedded: the HOST page observes its iframes (an iframe-local observer
// only sees the iframe's own viewport) and posts {type:'viz', visible}
addEventListener('message', e => {
  const m = e.data;
  if (m && m.type === 'viz'){ hostControlled = true;
    ioVisible = !!m.visible; if (active()) startLoop(); }
});
try {
  new IntersectionObserver(es => {
    if (hostControlled) return;            // the host page knows better
    ioVisible = es[0].isIntersecting;
    if (active()) startLoop();
  }, {threshold: 0.01}).observe(view);
} catch(_){ /* very old browsers: keep rendering */ }
document.addEventListener('visibilitychange', () => { if (active()) startLoop(); });

function loop(){
  if (!active()){ looping = false; return; }
  requestAnimationFrame(loop);
  const dt = Math.min(clock.getDelta(), 0.1);   // clamp across pauses
  if (PG) PG.step(dt);
  if (spinRate){
    for (const pr of propMeshes[mode]){
      const dir = pr.userData.dir!==undefined ? pr.userData.dir
                : ((pr.position.x>0)===(pr.position.y<0) ? 1 : -1);
      pr.rotateOnAxis(PROP_SPIN, spinRate*dt*dir);
    }
  }
  controls.update();
  renderer.render(scene, camera);
}
startLoop();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sdf", default=SDF, help="path to model.sdf")
    ap.add_argument("--out", default=OUT, help="output HTML path")
    ap.add_argument("--open", action="store_true", help="print a file:// URL to open")
    args = ap.parse_args()

    parts, meta = parse_sdf(args.sdf)
    html = build_html(parts, meta)
    with open(args.out, "w") as f:
        f.write(html)

    d = meta["dims"]
    print("== STRATOSDRONE 3D viewer ==")
    print(f"  parsed {len(parts)} visuals from {os.path.relpath(args.sdf, REPO)}")
    print(f"  wheelbase {d['wheelbase_mm']}mm · prop Ø{d['prop_d_mm']}mm · "
          f"tip-to-tip {d['tip_mm']}mm · mass {d['mass_g']}g")
    print(f"  wrote {os.path.relpath(args.out, REPO)} ({os.path.getsize(args.out)} B)")
    if args.open:
        print(f"  open:  file://{os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
