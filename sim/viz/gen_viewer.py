#!/usr/bin/env python3
"""Generate a self-contained interactive 3-D viewer for the STRATOSDRONE.

The drone's canonical geometry lives in ``sim/models/stratosdrone/model.sdf``
(the same rigid body Gazebo simulates).  This script parses that SDF and bakes
every ``<visual>`` — body, canopy, camera, battery, the four arms / motors /
props / ducts — into a single ``drone_viewer.html`` powered by Three.js.

Because the viewer is generated *from the SDF*, it can never drift from the
simulation model: re-run this script after editing ``model.sdf`` and the 3-D
view updates to match.  The HTML is fully self-contained (Three.js pulled from
a CDN via an import-map) — double-click it on any machine with a browser.

What the viewer gives you, to *validate or rethink* the design:
  • orbit / zoom / pan, plus ISO / TOP / FRONT / SIDE preset views
  • per-group show/hide (shell, arms, motors, props, ducts) + wireframe
  • an **exploded view** slider to inspect the vertical stack-up
  • spinning props (with direction matching a real quad's CW/CCW layout)
  • live dimension read-outs derived from the geometry (wheelbase, prop Ø,
    tip-to-tip footprint, overall L×W×H, mass)
  • drag-and-drop of the printed-frame STLs (hardware/frame/**/stl/*.stl) so you
    can overlay the real 3-D-printed parts on the functional model and check fit

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
    """Group a visual by name prefix, for the show/hide layer toggles."""
    if name.startswith("arm"):
        return "arms"
    if name.startswith("motor"):
        return "motors"
    if name.startswith("prop"):
        return "props"
    if name.startswith("duct"):
        return "ducts"
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

        # material diffuse rgba (fall back to a neutral grey)
        diffuse = [0.6, 0.6, 0.62, 1.0]
        mat = vis.find("material")
        if mat is not None and mat.findtext("diffuse"):
            diffuse = _floats(mat.findtext("diffuse"), 4)

        # opacity: explicit <transparency> wins, else diffuse alpha
        tr = vis.findtext("transparency")
        opacity = (1.0 - float(tr)) if tr not in (None, "") else diffuse[3]

        part = {
            "name": name,
            "group": category(name),
            "pose": pose,                       # x y z roll pitch yaw (m, rad)
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

    # collision hull (shown as an optional wireframe envelope)
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

    # wheelbase = diagonal distance between opposite motors
    wheelbase = 0.0
    if len(motors) >= 2:
        xs = [m["pose"][0] for m in motors]
        ys = [m["pose"][1] for m in motors]
        wheelbase = math.hypot(max(xs) - min(xs), max(ys) - min(ys))

    prop_d = 2 * max((p.get("radius", 0) for p in props), default=0)

    # tip-to-tip footprint: outermost prop edge across the diagonal
    tip = 0.0
    for p in props:
        x, y = p["pose"][0], p["pose"][1]
        tip = max(tip, 2 * (math.hypot(x, y) + p.get("radius", 0)) / math.sqrt(2))

    # crude axis-aligned bounding box over part centres ± half-extent
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
    """Inline a JS file as a base64 data: URL module."""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return "data:text/javascript;base64," + b64


def build_importmap():
    """Build an import-map whose entries are inlined data: URLs, so the viewer
    is one self-contained file that opens by double-click (no CDN, no local web
    server, no file:// CORS problem — ES modules from data: URLs are allowed).

    OrbitControls / STLLoader import only the bare specifier ``three``, which
    resolves through this same map, so the inlined modules chain correctly."""
    imports = {
        "three": _data_url(os.path.join(VENDOR, "three.module.js")),
        "three/addons/controls/OrbitControls.js":
            _data_url(os.path.join(VENDOR, "addons", "controls", "OrbitControls.js")),
        "three/addons/loaders/STLLoader.js":
            _data_url(os.path.join(VENDOR, "addons", "loaders", "STLLoader.js")),
    }
    return json.dumps({"imports": imports}, separators=(",", ":"))


def build_html(parts, meta):
    payload = json.dumps({"parts": parts, "meta": meta}, separators=(",", ":"))
    return (TEMPLATE
            .replace("/*__DATA__*/", payload)
            .replace("__IMPORTMAP__", build_importmap()))


TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>STRATOSDRONE — visualisateur 3D</title>
<style>
  :root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--ink:#e6edf3;--mut:#8b949e;
        --acc:#e6730d;--acc2:#2f81f7;}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;font:13px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
            background:var(--bg);color:var(--ink);overflow:hidden}
  #app{display:flex;height:100%}
  #side{width:300px;flex:none;background:var(--panel);border-right:1px solid var(--line);
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
  label.tog{display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none}
  label.tog input{accent-color:var(--acc)}
  .sw{width:11px;height:11px;border-radius:3px;flex:none}
  .btns{display:grid;grid-template-columns:1fr 1fr;gap:6px}
  button{background:#21262d;color:var(--ink);border:1px solid var(--line);border-radius:6px;
         padding:7px 8px;font-size:12px;cursor:pointer;transition:.12s}
  button:hover{background:#30363d;border-color:#484f58}
  button.on{background:var(--acc);border-color:var(--acc);color:#fff}
  input[type=range]{width:100%;accent-color:var(--acc)}
  .val{color:var(--acc);font-variant-numeric:tabular-nums}
  table{width:100%;border-collapse:collapse;font-size:12px}
  td{padding:3px 0;color:var(--mut)}
  td.v{text-align:right;color:var(--ink);font-variant-numeric:tabular-nums}
  .spec td.v{color:var(--acc2)}
  #drop{border:1.5px dashed var(--line);border-radius:8px;padding:14px;text-align:center;
        color:var(--mut);font-size:11px;cursor:pointer;transition:.15s}
  #drop.hot{border-color:var(--acc);color:var(--ink);background:#21262d}
  #hud{position:absolute;left:12px;bottom:12px;background:rgba(13,17,23,.82);
       border:1px solid var(--line);border-radius:8px;padding:9px 12px;font-size:11px;
       color:var(--mut);backdrop-filter:blur(4px);pointer-events:none}
  #hud b{color:var(--acc)}
  #tip{position:absolute;right:12px;top:12px;background:rgba(13,17,23,.82);
       border:1px solid var(--line);border-radius:8px;padding:8px 11px;font-size:11px;
       color:var(--mut);max-width:210px}
  #tip b{color:var(--ink)}
  .mini{font-size:10px;color:var(--mut);margin-top:6px}
  a{color:var(--acc2)}
</style>
</head>
<body>
<div id="app">
  <div id="side">
    <header>
      <h1><b>STRATOS</b>DRONE — 3D</h1>
      <p>généré depuis <code>model.sdf</code> · Tello EDU class</p>
    </header>

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
        <button id="bAxes" class="on">Axes</button>
        <button id="bHull">Coque collision</button>
      </div>
    </div>

    <div class="sec">
      <h2>Dimensions (mesurées)</h2>
      <table id="dims"></table>
    </div>

    <div class="sec">
      <h2>STRATOSDRONE vs Tello EDU</h2>
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

  <div id="view">
    <div id="tip"><b>Souris :</b> glisser = orbite · molette = zoom ·
      clic-droit = pan. Le drone est orienté <b>FLU</b> (X avant, Y gauche, Z haut).</div>
    <div id="hud"></div>
  </div>
</div>

<!-- Three.js (r160) is inlined as base64 data: URLs by gen_viewer.py, so this
     single file works fully offline and opens by double-click — no CDN, no web
     server, no file:// CORS problem. Re-generate with sim/viz/gen_viewer.py. -->
<script type="importmap">
__IMPORTMAP__
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

const DATA = /*__DATA__*/;
const PARTS = DATA.parts, META = DATA.meta;

const GROUPS = {
  shell:  {label:'Corps / canopy / caméra', color:'#c8821f'},
  arms:   {label:'Bras',                    color:'#2f81f7'},
  motors: {label:'Moteurs',                 color:'#9aa4ad'},
  props:  {label:'Hélices',                 color:'#e6730d'},
  ducts:  {label:'Carénages (ducts)',       color:'#6e7681'},
};

// ---- scene (Z-up to match the SDF FLU frame) -------------------------------
const view = document.getElementById('view');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d1117);

const camera = new THREE.PerspectiveCamera(45, 1, 0.001, 100);
camera.up.set(0, 0, 1);

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
view.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;

scene.add(new THREE.AmbientLight(0xffffff, 0.55));
const key = new THREE.DirectionalLight(0xffffff, 1.5);
key.position.set(0.1, 0.15, 0.3); scene.add(key);
const fill = new THREE.DirectionalLight(0x88aaff, 0.5);
fill.position.set(-0.2, -0.1, 0.1); scene.add(fill);

// ground grid on the XY plane (Z up), axes gizmo
const grid = new THREE.GridHelper(0.3, 30, 0x30363d, 0x21262d);
grid.rotation.x = Math.PI / 2; scene.add(grid);
const axes = new THREE.AxesHelper(0.06); scene.add(axes);

// ---- build meshes from the SDF parts --------------------------------------
const groupObjs = {};               // group -> THREE.Group
for (const g in GROUPS){ groupObjs[g] = new THREE.Group(); scene.add(groupObjs[g]); }
const propMeshes = [];

function sdfMatrix(pose){            // SDF pose -> Matrix4 (R = Rz·Ry·Rx, then T)
  const [x,y,z,r,p,yw] = pose;
  const m = new THREE.Matrix4().makeRotationZ(yw)
    .multiply(new THREE.Matrix4().makeRotationY(p))
    .multiply(new THREE.Matrix4().makeRotationX(r));
  m.setPosition(x, y, z);
  return m;
}

for (const part of PARTS){
  let geo;
  if (part.type === 'box'){
    geo = new THREE.BoxGeometry(part.size[0], part.size[1], part.size[2]);
  } else {                          // SDF cylinder axis = Z; Three axis = Y
    geo = new THREE.CylinderGeometry(part.radius, part.radius, part.length, 40);
    geo.rotateX(Math.PI/2);
  }
  const mat = new THREE.MeshStandardMaterial({
    color:new THREE.Color(part.color[0], part.color[1], part.color[2]),
    transparent: part.opacity < 1, opacity: part.opacity,
    metalness:0.25, roughness:0.55, side:THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.applyMatrix4(sdfMatrix(part.pose));
  mesh.userData = {part, home:mesh.position.clone()};
  groupObjs[part.group].add(mesh);

  if (part.group === 'props'){
    // visible 2-blade spinner so rotation reads clearly
    const blade = new THREE.Mesh(
      new THREE.BoxGeometry(part.radius*1.9, part.radius*0.16, 0.0016),
      new THREE.MeshStandardMaterial({color:mat.color, metalness:.2, roughness:.6}));
    blade.applyMatrix4(sdfMatrix(part.pose));
    blade.userData = {home:blade.position.clone()};
    // CW/CCW by diagonal (FR & BL one way; FL & BR the other)
    const n = part.name;
    blade.userData.dir = (n.endsWith('fr')||n.endsWith('bl')) ? 1 : -1;
    groupObjs.props.add(blade);
    propMeshes.push(blade);
  }
}

// collision hull wireframe (hidden by default)
let hullMesh = null;
if (META.hull){
  const h = META.hull;
  const g = new THREE.BoxGeometry(h.size[0], h.size[1], h.size[2]);
  hullMesh = new THREE.LineSegments(new THREE.EdgesGeometry(g),
    new THREE.LineBasicMaterial({color:0x3fb950}));
  hullMesh.applyMatrix4(sdfMatrix(h.pose));
  hullMesh.visible = false; scene.add(hullMesh);
}

// ---- explode: push each group's meshes radially + up -----------------------
const EXPLODE = {shell:[0,0], arms:[0.022,0], motors:[0.045,0.004],
                 props:[0.045,0.06], ducts:[0.045,0.03]};   // [radial, z] metres
function applyExplode(t){
  for (const g in groupObjs){
    const [kr,kz] = EXPLODE[g] || [0,0];
    for (const m of groupObjs[g].children){
      const h = m.userData.home; if(!h) continue;
      const rad = Math.hypot(h.x, h.y) || 1;
      m.position.set(h.x*(1 + t*kr/rad*8), h.y*(1 + t*kr/rad*8), h.z + t*kz);
    }
  }
}

// ---- STL drag & drop (printed frame overlay) ------------------------------
const stlGroup = new THREE.Group(); scene.add(stlGroup);
const stlLoader = new STLLoader();
let stlOpacity = 1;
function addSTL(name, buf){
  const geo = stlLoader.parse(buf);
  geo.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({color:0x58a6ff, transparent:true,
    opacity:stlOpacity, metalness:.1, roughness:.7, side:THREE.DoubleSide});
  const mesh = new THREE.Mesh(geo, mat);
  // OpenSCAD STLs are in mm, modelled around origin; SDF is metres -> scale.
  mesh.scale.setScalar(0.001);
  stlGroup.add(mesh);
  const d = document.getElementById('stlList');
  d.innerHTML += `<div>+ ${name}</div>`;
}
const drop = document.getElementById('drop');
function readFiles(files){
  for (const f of files){
    if(!f.name.toLowerCase().endsWith('.stl')) continue;
    const rd = new FileReader();
    rd.onload = e => addSTL(f.name, e.target.result);
    rd.readAsArrayBuffer(f);
  }
}
['dragenter','dragover'].forEach(ev=>drop.addEventListener(ev,e=>{
  e.preventDefault(); drop.classList.add('hot');}));
['dragleave','drop'].forEach(ev=>drop.addEventListener(ev,e=>{
  e.preventDefault(); drop.classList.remove('hot');}));
drop.addEventListener('drop', e=>readFiles(e.dataTransfer.files));
drop.addEventListener('click', ()=>{
  const i=document.createElement('input'); i.type='file'; i.accept='.stl'; i.multiple=true;
  i.onchange=()=>readFiles(i.files); i.click();});
document.getElementById('stlOp').addEventListener('input', e=>{
  stlOpacity = e.target.value/100;
  document.getElementById('stlOpV').textContent = e.target.value+'%';
  stlGroup.traverse(o=>{ if(o.material){o.material.opacity=stlOpacity;} });
});

// ---- UI: component toggles -------------------------------------------------
const gEl = document.getElementById('groups');
for (const g in GROUPS){
  const lab = document.createElement('label'); lab.className='tog';
  lab.innerHTML = `<input type="checkbox" checked data-g="${g}">
    <span class="sw" style="background:${GROUPS[g].color}"></span>${GROUPS[g].label}`;
  gEl.appendChild(lab);
}
gEl.addEventListener('change', e=>{
  const g = e.target.dataset.g; if(!g) return;
  groupObjs[g].visible = e.target.checked;
});

// ---- UI: display toggles + sliders ----------------------------------------
let wire=false, spinRate=0;
const bWire=document.getElementById('bWire'), bGrid=document.getElementById('bGrid'),
      bAxes=document.getElementById('bAxes'), bHull=document.getElementById('bHull');
bWire.onclick=()=>{wire=!wire; bWire.classList.toggle('on',wire);
  scene.traverse(o=>{ if(o.isMesh && o.material && stlGroup!==o.parent){o.material.wireframe=wire;} });};
bGrid.onclick=()=>{grid.visible=!grid.visible; bGrid.classList.toggle('on',grid.visible);};
bAxes.onclick=()=>{axes.visible=!axes.visible; bAxes.classList.toggle('on',axes.visible);};
bHull.onclick=()=>{ if(hullMesh){hullMesh.visible=!hullMesh.visible;
  bHull.classList.toggle('on',hullMesh.visible);} };

document.getElementById('explode').addEventListener('input', e=>{
  const t=e.target.value/100; applyExplode(t);
  document.getElementById('explodeV').textContent=e.target.value+'%';});
document.getElementById('spin').addEventListener('input', e=>{
  spinRate = e.target.value/100 * 40;
  document.getElementById('spinV').textContent = e.target.value==0?'arrêt':e.target.value+'%';});

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
  `<b>${PARTS.length}</b> composants · entraxe <b>${d.wheelbase_mm}mm</b> ·
   Ø hélice <b>${d.prop_d_mm}mm</b> · <b>${d.mass_g}g</b>`;

// ---- camera presets --------------------------------------------------------
const R = 0.22;
const VIEWS = {
  iso:[R*0.8, -R*0.8, R*0.6], top:[0.0001, 0, R*1.1],
  front:[R*1.2, 0, 0.02], side:[0, -R*1.2, 0.02],
};
function setView(v){
  const p = VIEWS[v] || VIEWS.iso;
  camera.position.set(p[0], p[1], p[2]);
  controls.target.set(0, 0, 0.005);
  controls.update();
}
document.querySelectorAll('[data-view]').forEach(b=>
  b.onclick=()=>setView(b.dataset.view));
setView('iso');

// ---- resize + render loop --------------------------------------------------
function resize(){
  const w=view.clientWidth, h=view.clientHeight;
  renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();

const clock = new THREE.Clock();
function loop(){
  requestAnimationFrame(loop);
  const dt = clock.getDelta();
  if (spinRate){
    for (const b of propMeshes){
      b.rotateOnAxis(new THREE.Vector3(0,0,1), spinRate*dt*b.userData.dir);
    }
  }
  controls.update();
  renderer.render(scene, camera);
}
loop();
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
    print(f"== STRATOSDRONE 3D viewer ==")
    print(f"  parsed {len(parts)} visuals from {os.path.relpath(args.sdf, REPO)}")
    print(f"  wheelbase {d['wheelbase_mm']}mm · prop Ø{d['prop_d_mm']}mm · "
          f"tip-to-tip {d['tip_mm']}mm · mass {d['mass_g']}g")
    print(f"  wrote {os.path.relpath(args.out, REPO)} ({os.path.getsize(args.out)} B)")
    if args.open:
        print(f"  open:  file://{os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
