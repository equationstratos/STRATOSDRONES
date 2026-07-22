#!/usr/bin/env python3
"""Fr4n10-001 (TinyHoop MK1) browser 3-D viewer + PLAYGROUND flight simulator.

Same self-contained recipe as every Stratos viewer (Three.js r160 inlined
from ``sim/viz/vendor``, part STLs embedded, opens by double-click) — PLUS
the full in-browser flight simulator (Tello-SDK script runner, presets,
swarm, and 🎮 keyboard flight), rebound on the TinyHoop MK1 airframe (2.5"
wide-X, ~115 mm wheelbase, 63.5 mm props). The playground is kinematic and
airframe-agnostic; the same verbs run against the Gazebo sim and the drone.

    python3 TinyHoopMK1/viz/gen_viewer.py       # -> TinyHoopMK1/viz/drone_viewer.html
    open drone_viewer.html?playground=1         #    the simulator
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
VENDOR = os.path.join(REPO, "sim", "viz", "vendor")
STL = os.path.join(REPO, "TinyHoopMK1", "cad", "stl")
TPU = os.path.join(REPO, "TinyHoopMK1", "cad", "frame_jeno", "tpu")
PARTS = os.path.join(REPO, "TinyHoopMK1", "cad", "frame_jeno", "parts")
DJI = os.path.join(REPO, "TinyHoopMK1", "cad", "dji_o4")
OUT = os.path.join(HERE, "drone_viewer.html")

# the 4 real motor-mount holes of the front-right corner (measured in the STEP)
_MHOLE = [(42.1,34.7),(45.9,29.6),(47.3,38.5),(51.0,33.4)]
_MOTOR_SCREWS = [[sx*x, sy*y, 3.3] for sx in (1,-1) for sy in (1,-1) for (x,y) in _MHOLE]
_FRAME_STAND = [[0,25.6],[8.5,-32.2],[-8.5,-32.2]]          # 3 real frame standoffs
_BOARD_STAND = [[18,0],[-18,0],[0,18],[0,-18]]              # AIO 25.5@45° corners
_STACK_SCREWS = [[x,y,17.4] for (x,y) in _FRAME_STAND] + [[x,y,6.4] for (x,y) in _BOARD_STAND]

MODEL = dict(name="FR4N10", sub="FPV programmable / essaim · 2,5\" · 2S-3S", wb=116,
             motors=[[46.6,34.1],[-46.6,34.1],[-46.6,-34.1],[46.6,-34.1]],
             prop_z=0.0135, motor_z=0.003, frame_z=0.0,
             elec=dict(board=[0,0,4], battery=[0,4,24],
                       o4cam=[0,42,10], o4airunit=[0,0,13], o4antenna=[0,-47,41],
                       cap=[12,-22,4], buzzer=[11,-31,6], gps=[-9,-16,20.8],
                       rx=[-11,-29,4], xt30=[0,-25,15], grommet=[0,0,11]),
             standoffs=dict(frame=_FRAME_STAND, board=_BOARD_STAND),
             # ALL screws: 16 motor-mount + 3 frame-standoff tops + 4 board tops
             screws=_MOTOR_SCREWS + _STACK_SCREWS,
             cammount=[0,0,0],            # O4 mount parts are already in frame coords
             # per-group explode offsets (mm along Z, × slider)
             explode=dict(bottom=[0,0,0], top=[0,0,56], standoffs=[0,0,26],
                          camcage=[0,0,40], camera=[0,0,48],
                          cammount_top=[0,26,60], cammount_bottom=[0,20,52],
                          airunit=[0,0,-18], motors=[0,0,-40], props=[0,0,78],
                          elec=[0,0,-30], battery=[0,0,94], screws=[0,0,66],
                          tpu=[0,0,-26], antenna=[0,0,90], cap=[0,0,-8],
                          extras=[0,0,-15]),
             specs=[("Entraxe", "~115 mm (wide-X)"), ("Hélices", "2,5\" Gemfan 2520"),
                    ("Moteurs", "1203-1303 · 2S-3S"),
                    ("ESC", "AIO BLHeli_S/Bluejay · DShot600"),
                    ("Radio", "ELRS (CRSF) + LoRa 868 (essaim/PC)"),
                    ("Vidéo", "5,8 GHz analogique OU DJI O4 Lite"),
                    ("Modes", "manuel · stabilisé · programmable · essaim"),
                    ("Position", "flow + ToF (GPS-ready)"),
                    ("Batterie", "2S-3S 450-560 mAh"), ("AUW cible", "115-145 g")])


def data_url(path):
    with open(path, "rb") as f:
        return "data:text/javascript;base64," + base64.b64encode(f.read()).decode("ascii")


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def importmap():
    v = lambda *p: data_url(os.path.join(VENDOR, *p))
    return json.dumps({"imports": {
        "three": v("three.module.js"),
        "three/addons/controls/OrbitControls.js": v("addons", "controls", "OrbitControls.js"),
        "three/addons/loaders/STLLoader.js": v("addons", "loaders", "STLLoader.js"),
        "three/addons/environments/RoomEnvironment.js": v("addons", "environments", "RoomEnvironment.js"),
    }}, separators=(",", ":"))


TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>__NAME__-001 — visualisateur 3D + simulateur</title>
<style>
  :root{--bg:#0b0e14;--panel:#12161d;--line:#262d38;--ink:#e6edf3;--mut:#8b949e;
        --acc:#2f6fed;--acc2:#63a4ff;--btn:#1b212b;--btnh:#262d38;--tip:rgba(11,14,20,.82);}
  body.light{--bg:#eef1f5;--panel:#f7f9fc;--line:#d3d9e0;--ink:#1a1f26;--mut:#5a636e;
        --acc:#2f6fed;--acc2:#1b4fd0;--btn:#e6eaf0;--btnh:#d7dde6;--tip:rgba(247,249,252,.9);}
  *{box-sizing:border-box}
  label.tog input[type=color].pick{width:15px;height:15px;padding:0;border:1px solid var(--line);
        border-radius:3px;background:none;cursor:pointer;flex:none;appearance:none;-webkit-appearance:none}
  label.tog input[type=color].pick::-webkit-color-swatch{border:none;border-radius:2px}
  label.tog input[type=color].pick::-webkit-color-swatch-wrapper{padding:0}
  label.tog span{flex:1}
  html,body{margin:0;height:100%;font:13px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
            background:var(--bg);color:var(--ink);overflow:hidden}
  #app{display:flex;height:100%}
  .sidebar{width:290px;flex:none;background:var(--panel);border-right:1px solid var(--line);
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
  label.tog{display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none;margin:5px 0}
  label.tog input{accent-color:var(--acc)}
  .sw{width:11px;height:11px;border-radius:3px;flex:none}
  .btns{display:grid;grid-template-columns:1fr 1fr;gap:6px}
  button{background:var(--btn);color:var(--ink);border:1px solid var(--line);border-radius:6px;
         padding:7px 8px;font-size:12px;cursor:pointer;transition:.12s}
  button:hover{background:var(--btnh);border-color:var(--acc)}
  button.on{background:var(--acc);border-color:var(--acc);color:#fff}
  input[type=range]{width:100%;accent-color:var(--acc)}
  .val{color:var(--acc);font-variant-numeric:tabular-nums}
  table{width:100%;border-collapse:collapse;font-size:12px}
  td{padding:3px 0;color:var(--mut)}
  td.v{text-align:right;color:var(--ink);font-variant-numeric:tabular-nums}
  .mini{color:var(--mut);font-size:11px;margin-top:7px}
  .mini b{color:var(--ink)}
  #pgCode{width:100%;height:150px;resize:vertical;background:#0b0e14;color:var(--ink);
          border:1px solid var(--line);border-radius:6px;font:12px/1.5 ui-monospace,monospace;
          padding:8px}
  .pg-log{height:110px;overflow-y:auto;background:#0b0e14;border:1px solid var(--line);
          border-radius:6px;padding:7px 9px;font:11px/1.6 ui-monospace,monospace}
  .pg-log .cmd{color:var(--acc2)} .pg-log .ok{color:#4cc38a} .pg-log .err{color:#ff6b63}
  #tip{position:absolute;right:12px;top:12px;background:var(--tip);
       border:1px solid var(--line);border-radius:8px;padding:8px 11px;font-size:11px;
       color:var(--mut);max-width:220px}
  #tip b{color:var(--ink)}
  #pg{display:none}
  body.play #side{display:none}
  body.play #pg{display:flex}
  body.embed .sidebar,body.embed #tip{display:none}
  @media (max-width:700px){#app{flex-direction:column}
    .sidebar{width:100%;max-height:46%;border-right:0;border-bottom:1px solid var(--line)}
    #tip{display:none}#pgCode{height:100px}}
</style>
</head>
<body>
<div id="app">
  <div id="side" class="sidebar">
    <header>
      <h1><b>__NAME__</b>-001 — 3D</h1>
      <p>__SUB__ · open source</p>
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
      <h2>Électronique</h2>
      <button id="bElec" class="on" style="width:100%">Électronique : STRATOS TINYHOOP AIO</button>
      <div id="bom" class="mini" style="display:none;margin-top:9px">
        <b>Build « standard » (composants du commerce, repo JeNo) :</b>
        <table style="margin-top:5px">
          <tr><td>FC / ESC</td><td class="v">JHEMCU GHF411 AIO (STEP réel)</td></tr>
          <tr><td>Moteurs</td><td class="v">1104 7500KV (Readytosky)</td></tr>
          <tr><td>Hélices</td><td class="v">Gemfan 2520</td></tr>
          <tr><td>Caméra</td><td class="v">DJI O4 Lite (caméra + air unit + antenne)</td></tr>
          <tr><td>RX</td><td class="v">ELRS (antenne céram.)</td></tr>
          <tr><td>VTX</td><td class="v">analogique 5,8 GHz (si non-O4)</td></tr>
          <tr><td>Batterie</td><td class="v">2S-3S 450-560 mAh</td></tr>
        </table>
        <div style="margin-top:5px">Vole en Betaflight — <b>non</b> programmable /
          essaim (ça, c'est la carte STRATOS).</div>
      </div>
    </div>
    <div class="sec">
      <h2>Affichage</h2>
      <div style="display:flex;justify-content:space-between"><span>Rotation hélices</span>
        <span class="val" id="spinV">arrêt</span></div>
      <input type="range" id="spin" min="0" max="100" value="40"/>
      <div style="display:flex;justify-content:space-between;margin-top:10px">
        <span>Vue éclatée</span><span class="val" id="expV">0 %</span></div>
      <input type="range" id="exp" min="0" max="100" value="0"/>
      <div class="btns" style="margin-top:10px">
        <button id="bWire">Fil de fer</button>
        <button id="bGrid" class="on">Grille</button>
        <button id="bTheme">☀ Clair / 🌙 Sombre</button>
        <button id="bReset">Couleurs par défaut</button>
      </div>
      <div class="mini">Ouvrez <b>?playground=1</b> pour le simulateur de vol
        (clavier + scripts SDK).</div>
    </div>
    <div class="sec">
      <h2>Réglage caméra / support</h2>
      <div class="mini" style="margin-bottom:8px">Choisis la pièce, aligne-la
        avec les curseurs, puis <b>relève les valeurs</b> et donne-les moi.</div>
      <select id="camTarget" style="width:100%;background:var(--btn);color:var(--ink);
        border:1px solid var(--line);border-radius:6px;padding:6px;margin-bottom:8px">
        <option value="camera">Caméra O4 Lite</option>
        <option value="cammount_top">Support HAUT (TPU)</option>
        <option value="cammount_bottom">Support BAS (TPU)</option>
      </select>
      <div style="display:flex;justify-content:space-between"><span>Latéral (X)</span>
        <span class="val" id="camXV">0.0 mm</span></div>
      <input type="range" id="camX" min="-15" max="15" step="0.5" value="0"/>
      <div style="display:flex;justify-content:space-between;margin-top:6px"><span>Profondeur (Y)</span>
        <span class="val" id="camYV">0.0 mm</span></div>
      <input type="range" id="camY" min="-20" max="20" step="0.5" value="0"/>
      <div style="display:flex;justify-content:space-between;margin-top:6px"><span>Vertical (Z)</span>
        <span class="val" id="camZV">0.0 mm</span></div>
      <input type="range" id="camZ" min="-15" max="15" step="0.5" value="0"/>
      <div style="display:flex;justify-content:space-between;margin-top:6px"><span>Rotation X (°)</span>
        <span class="val" id="camRXV">0°</span></div>
      <input type="range" id="camRX" min="-90" max="90" step="1" value="0"/>
      <div style="display:flex;justify-content:space-between;margin-top:6px"><span>Rotation Y (°)</span>
        <span class="val" id="camRYV">0°</span></div>
      <input type="range" id="camRY" min="-90" max="90" step="1" value="0"/>
      <div style="display:flex;justify-content:space-between;margin-top:6px"><span>Rotation Z (°)</span>
        <span class="val" id="camRZV">0°</span></div>
      <input type="range" id="camRZ" min="-90" max="90" step="1" value="0"/>
      <div class="mini" style="margin-top:8px"><b id="camDelta">camera : X 0 · Y 0 · Z 0 · RX 0 · RY 0 · RZ 0</b>
        — copie-moi cette ligne.</div>
      <button id="camReset" style="width:100%;margin-top:8px">Réinitialiser cette pièce</button>
    </div>
    <div class="sec">
      <h2>Spécifications (cible)</h2>
      <table>__SPECS__</table>
    </div>
  </div>

  <div id="pg" class="sidebar">
    <header>
      <h1><b>__NAME__</b>-001 — Simulateur</h1>
      <p>pilotez le __SUB__ (SDK Tello + clavier)</p>
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
      <h2>Presets</h2>
      <div class="btns">
        <button id="pgP1">01 · Hover</button>
        <button id="pgP2">02 · Carré</button>
        <button id="pgP3">03 · Swarm ×3</button>
        <button id="pgP4">★ Freestyle</button>
        <button id="pgP5" style="grid-column:1/-1">⚡ Run FPV (nerveux)</button>
      </div>
    </div>
    <div class="sec">
      <h2>Pilotage clavier</h2>
      <button id="pgKbd" style="width:100%">🎮 Pilotage clavier : OFF</button>
      <div class="mini"><b>T</b> décoller · <b>↑↓←→</b> translater ·
        <b>Z</b> monter · <b>W</b> descendre · <b>Q/D</b> pivoter ·
        <b>F</b> flip · <b>L</b> atterrir.</div>
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
  </div>

  <div id="view">
    <div id="tip"><b>Souris :</b> glisser = orbite · molette = zoom ·
      clic-droit = pan. 2,5" programmable/essaim : <b>ELRS</b> + <b>LoRa 868</b>,
      vidéo analogique <b>ou O4 Lite</b>, 4 modes.</div>
  </div>
</div>

<script type="importmap">
__IMPORTMAP__
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const STLB64 = __STLS__;   // {frame, canopy, prop, motor}
const M = __MODEL__;       // geometry constants (metres)
const PARAMS = new URLSearchParams(location.search);
const EMBED = PARAMS.has('embed');
const PLAY  = PARAMS.has('playground');
if (EMBED) document.body.classList.add('embed');
if (PLAY)  document.body.classList.add('play');

const view = document.getElementById('view');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0e14);
const camera = new THREE.PerspectiveCamera(42, 1, 0.001, 100);
camera.up.set(0, 0, 1);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,
  matchMedia('(max-width:700px)').matches ? 1.25 : 1.5));
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
view.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.08;
controls.minDistance = PLAY ? 0.3 : 0.08; controls.maxDistance = PLAY ? 14 : 0.8;

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.add(new THREE.HemisphereLight(0xbfd3ff, 0x202024, 0.55));
const key = new THREE.DirectionalLight(0xffffff, 2.0); key.position.set(0.2,0.26,0.5); scene.add(key);
const rim = new THREE.DirectionalLight(0x88aaff, 0.7); rim.position.set(-0.3,-0.28,0.16); scene.add(rim);
let grid;
function makeGrid(light){ if(grid){ scene.remove(grid); grid.geometry.dispose(); grid.material.dispose(); }
  grid = new THREE.GridHelper(0.4, 32, light?0x9aa4b0:0x262d38, light?0xc2c9d2:0x171c24);
  grid.rotation.x = Math.PI/2; scene.add(grid); }
makeGrid(false);

const loader = new STLLoader();
function geo(b64){ const bin = Uint8Array.from(atob(b64), c=>c.charCodeAt(0));
  const g = loader.parse(bin.buffer); g.computeVertexNormals(); return g; }
function mesh(b64, color, metal, rough, opts){
  const mat = new THREE.MeshStandardMaterial({color, metalness:metal, roughness:rough});
  if (opts && opts.opacity!=null){ mat.transparent=true; mat.opacity=opts.opacity;
    mat.depthWrite=false; mat.side=THREE.DoubleSide; }
  const m = new THREE.Mesh(geo(b64), mat);
  m.scale.setScalar(0.001);          // mm -> m
  return m;
}

// ---- the drone: ONE group whose origin is the ground under its centre ----
// (the playground moves/clones this group; feet touch z=0)
const frameRoot = new THREE.Group(); scene.add(frameRoot);
const G = {};
function group(name){ const g = new THREE.Group(); G[name]=g; frameRoot.add(g); return g; }
// a group whose ORIGIN is a chosen pivot (mm) so sliders can translate AND
// rotate the part about its own centre; the mesh is re-offset to stay in place.
function adjGroup(name, meshObj, px, py, pz){
  const g = group(name);
  g.position.set(px/1000, py/1000, pz/1000);
  meshObj.position.set(meshObj.position.x - px/1000,
                       meshObj.position.y - py/1000,
                       meshObj.position.z - pz/1000);
  g.add(meshObj); g.userData.base = g.position.clone(); return g;
}

const CARBON = 0x1a1d21;
function place(b64, colr, met, rgh, off){
  const m2 = mesh(b64, colr, met, rgh);
  if (off) m2.position.set(off[0]/1000, off[1]/1000, M.frame_z + off[2]/1000);
  return m2;
}
// the REAL JeNo Pocket V2 frame, SPLIT from the STEP into separate solids so
// each explodes on its own: bottom plate, camera cage, standoffs, camera.
// The top plate is REPLACED by our STRATOS top (same envelope) per the brief.
const TPU = 0x2b2f36;
const gBottom = group('bottom'); { const m=mesh(STLB64.frame_bottom, CARBON,.3,.5);
  m.position.z=M.frame_z; gBottom.add(m); }
const gTop = group('top'); { const m=mesh(STLB64.frame_top, CARBON,.3,.5);
  m.position.z=M.frame_z; gTop.add(m); }        // STRATOS top plate
// clean aluminium standoffs: 3 tall frame posts (z3→17) + 4 short board posts
const gStand = group('standoffs');
for (const [x,y] of M.standoffs.frame){ const s=mesh(STLB64.standoff, 0xc2c5cb,.9,.3);
  s.position.set(x/1000, y/1000, 0.003); gStand.add(s); }
for (const [x,y] of M.standoffs.board){ const s=mesh(STLB64.standoff, 0xc2c5cb,.9,.3);
  s.position.set(x/1000, y/1000, 0.003); s.scale.set(0.001,0.001,0.001*3/14); gStand.add(s); }
const gCage = group('camcage'); { const m=mesh(STLB64.camcage, CARBON,.3,.5);
  m.position.z=M.frame_z; gCage.add(m); }
// DJI O4 Lite camera head, seated in the TPU mount at the nose (real STEP).
// Grey body + a glossy lens disc so it actually reads inside the dark cage.
const gCam = (()=>{ const m=mesh(STLB64.o4cam, 0x30343b,.5,.35);  // dark-grey body
  m.rotation.z = Math.PI/2;                          // lens faces +Y (nose)
  m.position.set(M.elec.o4cam[0]/1000, M.elec.o4cam[1]/1000, M.elec.o4cam[2]/1000);
  const g = adjGroup('camera', m, 0, 42, 20);        // pivot at camera centre
  // soft rubber gasket around the lens — fills the gap between camera and the
  // TPU mount (matte black silicone O-ring); rides with the camera group
  const rub = new THREE.Mesh(new THREE.TorusGeometry(0.0064, 0.0014, 14, 40),
    new THREE.MeshStandardMaterial({color:0x0b0b0d, metalness:0.0, roughness:0.97}));
  rub.rotation.x = Math.PI/2;                         // ring axis along +Y (lens)
  rub.position.set(0, 12.0/1000, -1/1000);           // thin gasket at the lens front
  g.add(rub);
  return g; })();
// DJI O4 Lite air unit (VTX) — stacked ABOVE the FC on soft-mount grommets,
// aligned on the same 25.5@45° pattern, with a ribbon cable down to the camera.
const gAir = group('airunit');
{ const air = place(STLB64.o4airunit, 0x11532e,.3,.5, M.elec.o4airunit);  // PCB green
  air.rotation.z = Math.PI/4; gAir.add(air); }
// 4 rubber grommets between the FC top and the VTX (the soft-mount stack)
for (const [x,y] of M.standoffs.board){
  const g = new THREE.Mesh(new THREE.CylinderGeometry(0.0022,0.0022,0.0045,18),
    new THREE.MeshStandardMaterial({color:0xe38a1c, metalness:.1, roughness:.6}));
  g.rotation.x = Math.PI/2;
  g.position.set(x/1000, y/1000, (M.elec.grommet[2])/1000); gAir.add(g);
}
// the O4 ribbon cable: VTX -> camera at the nose (a thin dark swept strip)
{ const pts=[]; const y0=M.elec.o4airunit[1], y1=M.elec.o4cam[1];
  for (let i=0;i<=12;i++){ const t=i/12; const y=y0+(y1-y0)*t;
    const z=M.elec.o4airunit[2]+2 + Math.sin(t*Math.PI)*6;
    pts.push(new THREE.Vector3(0.003, y/1000, z/1000)); }
  const cur=new THREE.CatmullRomCurve3(pts);
  const rib=new THREE.Mesh(new THREE.TubeGeometry(cur,24,0.0016,8,false),
    new THREE.MeshStandardMaterial({color:0x1a1c20, metalness:.2, roughness:.6}));
  gAir.add(rib); }
// real WE are FPV 2-part O4 camera mount — TOP and BOTTOM as SEPARATE
// pivot-groups so each can be translated AND rotated on its own
const gMountT = adjGroup('cammount_top',
  mesh(STLB64.cam_mount_top, TPU,.1,.8), 0, 43.45, 24.45);
const gMountB = adjGroup('cammount_bottom',
  mesh(STLB64.cam_mount_bottom, TPU,.1,.8), 0, 43.5, 11.3);
// real TPU protection: arm bumpers ×4 + back bumper + VTX antenna mount
const gTpu = group('tpu');
for (const [sx, sy] of [[1,1],[-1,1],[1,-1],[-1,-1]]){
  const ab = mesh(STLB64.arm_bumper, TPU,.1,.8);
  ab.scale.set(sx*0.001, sy*0.001, 0.001); gTpu.add(ab);
}
gTpu.add(mesh(STLB64.back_bumper, TPU,.1,.8));
gTpu.add(mesh(STLB64.vtx_mount, TPU,.1,.8));
// real Readytosky 1104 motors on the measured hole centres (±46.6, ±34.1)
const gMot = group('motors');
for (const [mx, my] of M.motors){
  const mm = mesh(STLB64.motor, 0x3a3d43, .85, .3);
  mm.position.set(mx/1000, my/1000, M.motor_z);
  gMot.add(mm);
}
const gProp = group('props');
const propMeshes = [];
for (const [mx, my] of M.motors){
  const cw = (mx*my > 0);
  const pm = mesh(STLB64.prop, 0xd8721e, .05, .35, {opacity:0.55});
  pm.position.set(mx/1000, my/1000, M.prop_z);
  pm.scale.set(0.001, cw?0.001:-0.001, 0.001);
  pm.userData.dir = cw?1:-1;
  pm.userData.front = (my > 0);
  gProp.add(pm); propMeshes.push(pm);
}
// AIO board — two interchangeable options on the 25.5 @45° stack:
//  · JHEMCU GHF411 AIO (real STEP you provided) — shown by default
//  · STRATOS TINYHOOP AIO (our custom board, green)
// the "Électronique" button swaps which one is visible.
const gElec = group('elec');
const boardCustom = place(STLB64.board, 0x0b6b39, .15, .5, M.elec.board);
boardCustom.rotation.z = Math.PI/4; boardCustom.visible = false; gElec.add(boardCustom);
const boardGhf = place(STLB64.ghf411, 0x14161b, .35, .45, M.elec.board);
boardGhf.rotation.z = Math.PI/4; gElec.add(boardGhf);   // 45° = real JeNo AIO mount, default
const gBatt = group('battery');
gBatt.add(place(STLB64.battery, 0x22262d, .1, .55, M.elec.battery));
// M2 screws on the real standoffs + camera plates
const gScrew = group('screws');
for (const s of M.screws){ const sc = place(STLB64.screw, 0xd6d9de, .9, .25, s);
  gScrew.add(sc); }
// 4 stack screws capping the VTX-on-FC soft-mount at the board corners
for (const [x,y] of M.standoffs.board){
  const sc = place(STLB64.screw, 0xd6d9de, .9, .25, [x, y, M.elec.o4airunit[2]+3]);
  gScrew.add(sc); }
// the SINGLE DJI O4 Lite antenna (real STEP), seated in the rear TPU mount the
// RIGHT way up: the fat connector/ferrite end drops into the tube, the thin
// whip rises up-and-back (~26° off vertical)
const gAnt = group('antenna');
{ const a = place(STLB64.o4antenna, 0x101216, .2, .5, M.elec.o4antenna);
  a.rotation.x = -1.12; gAnt.add(a); }   // connector down, whip up-and-back
// LiPo capacitor (25 V 22 µF, Ø6×12) SEATED IN ITS PRINTED TPU HOLDER
const gCap = group('cap');
gCap.add(place(STLB64.cap_holder, TPU, .1, .85, M.elec.cap));       // TPU snap-clip
gCap.add(place(STLB64.cap, 0x1b3a8f, .25, .45,                      // the can, in the bore
  [M.elec.cap[0], M.elec.cap[1], M.elec.cap[2]+0.6]));
// ---- a swept round tube between two points (mm) — for wires ----
function wireTube(p0, p1, r, col){
  const pts=[new THREE.Vector3(p0[0]/1000,p0[1]/1000,p0[2]/1000),
             new THREE.Vector3((p0[0]+p1[0])/2000,(p0[1]+p1[1])/2000,(Math.max(p0[2],p1[2])+4)/1000),
             new THREE.Vector3(p1[0]/1000,p1[1]/1000,p1[2]/1000)];
  const c=new THREE.CatmullRomCurve3(pts);
  return new THREE.Mesh(new THREE.TubeGeometry(c,20,r/1000,8,false),
    new THREE.MeshStandardMaterial({color:col, metalness:.1, roughness:.55}));
}
// build extras: buzzer, GPS/compass, ELRS RX (PCB + antenna in TPU holder),
// battery XT30 red/black leads to the ESC, and the 4 motor phase cables
const gEx = group('extras');
gEx.add(place(STLB64.buzzer, 0x141519, .3,  .5,  M.elec.buzzer));   // Ø8 buzzer
gEx.add(place(STLB64.gps,    0x0a0c10, .2,  .5,  M.elec.gps));      // GPS/compass
// ELRS RX: the PCB in its TPU tray, and the iFlight T-antenna standing
// PERPENDICULAR to the drone in its own printed TPU mast-holder
gEx.add(place(STLB64.rx_holder, TPU, .1, .85, M.elec.rx));          // TPU tray
gEx.add(place(STLB64.rx_pcb, 0x0f3d0f, .2, .5,                      // RX board
  [M.elec.rx[0], M.elec.rx[1], M.elec.rx[2]+1.6]));
{ const ap = [M.elec.rx[0], M.elec.rx[1]-6, M.elec.rx[2]];
  gEx.add(place(STLB64.rx_ant_tpu, TPU, .1, .85, ap));             // TPU mast holder
  gEx.add(place(STLB64.rx, 0x141414, .25, .5,                       // T-antenna, upright
    [ap[0], ap[1], ap[2]+3])); }                                    // mast +Z = perpendicular
// battery XT30 connector + red(+)/black(-) leads down to the ESC pads
{ const xt = M.elec.xt30;
  const conn = new THREE.Mesh(new THREE.BoxGeometry(0.009,0.007,0.006),
    new THREE.MeshStandardMaterial({color:0xf0b000, metalness:.2, roughness:.5}));
  conn.position.set(xt[0]/1000, xt[1]/1000, xt[2]/1000); gEx.add(conn);
  gEx.add(wireTube([xt[0]+2, xt[1], xt[2]-1], [4, -6, 8], 0.85, 0xd21f1f));   // red +
  gEx.add(wireTube([xt[0]-2, xt[1], xt[2]-1], [-4, -6, 8], 0.85, 0x111214)); }// black -
for (const [mx, my] of M.motors){                                  // 4 phase cables
  const c = mesh(STLB64.cable, 0x2a2c30, .2, .6);
  c.position.set(mx/1000, my/1000, M.frame_z + 0.004);
  c.scale.set(mx<0?-0.001:0.001, my<0?-0.001:0.001, 0.001); gEx.add(c); }

// ---- part toggles + per-part colour pickers ----
const GROUPS = {
  bottom:   {label:'Plaque basse (carbone réel)', color:'#1a1d21'},
  top:      {label:'Plaque haute (JeNo, sans texte)', color:'#1a1d21'},
  standoffs:{label:'Entretoises', color:'#b9bcc2'},
  camcage:  {label:'Cage caméra (carbone)', color:'#1a1d21'},
  camera:   {label:'Caméra DJI O4 Lite', color:'#121316'},
  airunit:  {label:'Air unit DJI O4 Lite (PCB nue)', color:'#11532e'},
  cammount_top:    {label:'Support caméra HAUT (TPU)', color:'#2b2f36'},
  cammount_bottom: {label:'Support caméra BAS (TPU)', color:'#2b2f36'},
  tpu:      {label:'Protections TPU (bumpers)', color:'#2b2f36'},
  motors:   {label:'Moteurs 1104 (Readytosky)', color:'#3a3d43'},
  props:    {label:'Hélices 2,5" (2520)',  color:'#d8721e'},
  elec:     {label:'Carte AIO (STRATOS / GHF411)', color:'#0b6b39'},
  battery:  {label:'Batterie 3S 560 mAh (DOGCOM)', color:'#22262d'},
  screws:   {label:'Visserie M2 (moteurs + stack)', color:'#d6d9de'},
  antenna:  {label:'Antenne DJI O4 (unique, dans le TPU)', color:'#101216'},
  cap:      {label:'Condensateur 25 V 22 µF (support TPU)', color:'#1b3a8f'},
  extras:   {label:'Buzzer · GPS · RX+TPU · câbles XT30', color:'#3a6ea5'},
};
// remember each group's assembled position so the explode slider can offset it
for (const k of Object.keys(GROUPS)){
  if (G[k]) { G[k].userData.home = G[k].position.clone();
              G[k].userData.exp = (M.explode&&M.explode[k])||[0,0,0]; } }
const groupsEl = document.getElementById('groups');
for (const k of Object.keys(GROUPS)){
  const l = document.createElement('label'); l.className='tog';
  l.innerHTML = `<input type="checkbox" checked>`+
    `<input type="color" class="pick" value="${GROUPS[k].color}" title="couleur">`+
    `<span>${GROUPS[k].label}</span>`;
  l.querySelector('input[type=checkbox]').addEventListener('change',
    e=>{ if(G[k]) G[k].visible = e.target.checked; });
  l.querySelector('input[type=color]').addEventListener('input',
    e=>setColor(k, e.target.value));
  groupsEl.appendChild(l);
}

// ---- explode view ----
function setExplode(f){                       // f in 0..1
  for (const k of Object.keys(GROUPS)){ const g=G[k]; if(!g||!g.userData.home) continue;
    const e=g.userData.exp;
    g.position.set(g.userData.home.x + e[0]/1000*f,
                   g.userData.home.y + e[1]/1000*f,
                   g.userData.home.z + e[2]/1000*f); }
}

// ---- live recolour (configurator-compatible) ----
function setColor(g, hex){ if(!hex||!G[g]) return; const col=new THREE.Color(hex);
  G[g].traverse(o=>{ if(o.isMesh) o.material.color.copy(col); }); }
function applyColors(o){ if(!o) return;
  setColor('frame',  o.body!=null?o.body:o.frame);
  setColor('props',  o.propFront!=null?o.propFront:(o.props!=null?o.props:o.pr)); }
applyColors({body:PARAMS.get('body'), capot:PARAMS.get('capot'), props:PARAMS.get('props')});
addEventListener('message', e=>{ const m=e.data;
  if(m&&m.type==='colors'){ applyColors(m); window.__lastColors=m; } });
try { if (parent && parent!==window) parent.postMessage({type:'ready'}, '*'); } catch(_){}

// ---- wireframe / grid / spin / views ----
let wire=false;
document.getElementById('bWire').addEventListener('click', e=>{ wire=!wire; e.target.classList.toggle('on',wire);
  scene.traverse(o=>{ if(o.isMesh) o.material.wireframe=wire; }); });
document.getElementById('bGrid').addEventListener('click', e=>{ grid.visible=!grid.visible; e.target.classList.toggle('on',grid.visible); });

// ---- exploded view ----
{ const el=document.getElementById('exp'), v=document.getElementById('expV');
  el.addEventListener('input', e=>{ const f=+e.target.value/100; setExplode(f);
    v.textContent=e.target.value+' %'; }); }

// ---- light / dark theme (dark by default = current look) ----
let light=false;
function applyTheme(){ document.body.classList.toggle('light', light);
  scene.background = new THREE.Color(light?0xeef1f5:0x0b0e14);
  makeGrid(light); }
document.getElementById('bTheme').addEventListener('click', ()=>{ light=!light; applyTheme(); });

// ---- reset colours to defaults ----
document.getElementById('bReset').addEventListener('click', ()=>{
  const keys=Object.keys(GROUPS);
  keys.forEach(k=> setColor(k, GROUPS[k].color));
  document.querySelectorAll('.pick').forEach((el,i)=>{ el.value=GROUPS[keys[i]].color; }); });

// ---- real GHF411 (default) vs STRATOS custom electronics ----
function applyElec(std){                    // std = show the real GHF411
  const b = document.getElementById('bElec');
  b.textContent = std ? 'Électronique : JHEMCU GHF411 (réel)'
                      : 'Électronique : STRATOS TINYHOOP AIO';
  b.classList.toggle('on', !std);           // "on" highlights our custom board
  document.getElementById('bom').style.display = std ? 'block' : 'none';
  boardGhf.visible = std;                    // real JHEMCU GHF411 AIO
  boardCustom.visible = !std;                // STRATOS custom board
}
let stdElec=true;                            // default: show the FC you provided
applyElec(stdElec);
document.getElementById('bElec').addEventListener('click', ()=>{
  stdElec=!stdElec; applyElec(stdElec);
});
// ---- per-part fine-adjust: translate + rotate the chosen part about its pivot ----
// DEF = the alignment the owner dialled in; it is applied at load and is the
// "reset" target, so the nose is correctly seated out of the box.
{ const DEF = { camera:         {x:0, y:0,   z:-6,   rx:27, ry:0, rz:0},
                cammount_top:   {x:0, y:-2,  z:-1,   rx:-6, ry:0, rz:0},
                cammount_bottom:{x:0, y:4.5, z:-1.5, rx:-5, ry:0, rz:0} };
  const cp = o => Object.assign({}, o);
  const off = { camera:cp(DEF.camera), cammount_top:cp(DEF.cammount_top),
                cammount_bottom:cp(DEF.cammount_bottom) };
  const el = id => document.getElementById(id);
  const D = Math.PI/180;
  const applyTarget = (t)=>{ const o=off[t]; const g=G[t];
    if (g){ const b = g.userData.base || new THREE.Vector3();
      g.position.set(b.x + o.x/1000, b.y + o.y/1000, b.z + o.z/1000);
      g.rotation.set(o.rx*D, o.ry*D, o.rz*D);
      g.userData.home = g.position.clone(); } };
  const applyCam = ()=>{
    const t = el('camTarget').value; const o = off[t]; applyTarget(t);
    el('camXV').textContent = o.x.toFixed(1)+' mm';
    el('camYV').textContent = o.y.toFixed(1)+' mm';
    el('camZV').textContent = o.z.toFixed(1)+' mm';
    el('camRXV').textContent = o.rx+'°';
    el('camRYV').textContent = o.ry+'°';
    el('camRZV').textContent = o.rz+'°';
    el('camDelta').textContent = t+' : X '+o.x+' · Y '+o.y+' · Z '+o.z
      +' · RX '+o.rx+' · RY '+o.ry+' · RZ '+o.rz;
  };
  const bind = (id, k)=> el(id).addEventListener('input', e=>{
    off[el('camTarget').value][k] = +e.target.value; applyCam(); });
  bind('camX','x'); bind('camY','y'); bind('camZ','z');
  bind('camRX','rx'); bind('camRY','ry'); bind('camRZ','rz');
  const sync = ()=>{ const o=off[el('camTarget').value];
    el('camX').value=o.x; el('camY').value=o.y; el('camZ').value=o.z;
    el('camRX').value=o.rx; el('camRY').value=o.ry; el('camRZ').value=o.rz; applyCam(); };
  el('camTarget').addEventListener('change', sync);
  el('camReset').addEventListener('click', ()=>{ off[el('camTarget').value]=cp(DEF[el('camTarget').value]); sync(); });
  ['camera','cammount_top','cammount_bottom'].forEach(applyTarget);   // apply at load
  sync();                                                             // reflect in UI
}
let spinRate=0.4*60;                       // hélices en rotation par défaut
document.getElementById('spinV').textContent='40%';
document.getElementById('spin').addEventListener('input', e=>{ spinRate=e.target.value/100*60;
  document.getElementById('spinV').textContent=e.target.value==0?'arrêt':e.target.value+'%'; });
const R=0.17;
// +Y is the nose (camera end): iso + front look at the drone from the front
const VIEWS={iso:[R*0.9,R*0.95,R*0.6], top:[0.0001,0,R*1.25], front:[0,R*1.4,R*0.22], side:[R*1.35,0,R*0.2]};
function setView(v){ const p=VIEWS[v]||VIEWS.iso; camera.position.set(p[0],p[1],p[2]);
  controls.target.set(0,0,0.018); controls.update(); }
document.querySelectorAll('[data-view]').forEach(b=> b.onclick=()=>setView(b.dataset.view));
if (!PLAY) setView('iso');

function resize(){ const w=view.clientWidth,h=view.clientHeight;
  renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();

// ===========================================================================
//  Playground — ported from the Fr4n7 viewer (sim/viz/gen_viewer.py), rebound
//  on the fpv85 airframe. Verbs/ranges mirror fc_core/src/fc_sdk.c.
// ===========================================================================
const PROP_SPIN = new THREE.Vector3(0,0,1);
const PG = (function(){
  if (!PLAY) return null;
  const DEG = Math.PI/180, SPEED0 = 1.0, YAW_RATE = 96*DEG;
  const CLIMB = 0.42, DESC = 0.45, TAKEOFF_Z = 0.8;
  const SPACING = 0.6, MAXD = 6;      // tighter formation: 85 mm micros
  const $ = id => document.getElementById(id);
  const logEl = $('pgLog');
  function log(msg, cls){ const d=document.createElement('div');
    if(cls) d.className=cls; d.textContent=msg; logEl.appendChild(d);
    logEl.scrollTop = logEl.scrollHeight; }

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
          if (v.slice(0,6).some(x=>!(x>=RANGE.go[0]&&x<=RANGE.go[1])) ||
              !(v[6]>=10&&v[6]<=60)) return abort('→ error (curve: ±500 cm, speed 10-60)');
          const bod=(x,y,z)=>({x:p.x+fx*(x/100)-fy*(y/100),
                               y:p.y+fy*(x/100)+fx*(y/100),
                               z:Math.max(0.05,p.z+z/100)});
          job.b0={x:p.x,y:p.y,z:p.z}; job.b1=bod(v[0],v[1],v[2]); job.b2=bod(v[3],v[4],v[5]);
          let len=0, px=job.b0.x, py=job.b0.y, pz=job.b0.z;
          for (let q=1;q<=20;q++){ const s=q/20, a=(1-s)*(1-s), m2=2*(1-s)*s, bq=s*s;
            const qx=a*job.b0.x+m2*job.b1.x+bq*job.b2.x, qy=a*job.b0.y+m2*job.b1.y+bq*job.b2.y,
                  qz=a*job.b0.z+m2*job.b1.z+bq*job.b2.z;
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
      const a=(1-s)*(1-s), m2=2*(1-s)*s, bq=s*s;
      p.set(a*j.b0.x+m2*j.b1.x+bq*j.b2.x,
            a*j.b0.y+m2*j.b1.y+bq*j.b2.y,
            a*j.b0.z+m2*j.b1.z+bq*j.b2.z);
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
        pr.rotateOnAxis(PROP_SPIN, 30*dt*(pr.userData.dir||1));
    if (st.timer > 0){ st.timer -= dt;
      if (st.timer <= 0 && st.cur && st.cur.op==='sleep'){ st.timer=0; done('ok'); }
      readout(); return; }
    let pending = false;
    for (const d of drones) if (d.job && !stepDrone(d, dt)) pending = true;
    if (st.cur){
      if (!pending && drones.every(d=>!d.job)) done('ok');
    } else if (kbd.on && !st.queue.length){
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

  const kbd = {on:false, k:Object.create(null)};
  const kbtn = $('pgKbd');
  kbtn.addEventListener('click', ()=>{
    kbd.on = !kbd.on; kbtn.classList.toggle('on', kbd.on);
    kbtn.textContent = kbd.on ? '🎮 Pilotage clavier : ON' : '🎮 Pilotage clavier : OFF';
    log(kbd.on ? 'clavier activé — T pour décoller' : 'clavier désactivé', 'ok');
  });
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

  const PRESETS = {
    hover: ['# hover — décoller, planer 5 s, atterrir','command','takeoff',
            'sleep 5','land'].join('\n'),
    square: ['# carré de 1 m','command','takeoff',
             'go 100 0 0 50','cw 90','go 100 0 0 50','cw 90',
             'go 100 0 0 50','cw 90','go 100 0 0 50','cw 90','land'].join('\n'),
    swarm: ['# essaim de 3 micros FPV (jambes indexées par i)',
            'command','drones 3','takeoff',
            'go 60+40*i (i-1)*80 0 60','cw 120*(i+1)','land'].join('\n'),
    freestyle: ['# ★ freestyle FPV — curves + flips','command','drones 3','takeoff','up 30+20*i',
            'flip f','curve 80 (i-1)*60 20 160 0 0 60',
            'flip b','curve 80 (1-i)*60 -20 160 0 0 50',
            'cw 120+60*i','flip l','land'].join('\n'),
    fpv: ['# ⚡ RUN FPV — rapide & nerveux : dives, power loops, split-S, slalom',
            'command','speed 100','takeoff','up 80',
            '# acceleration en courbe (montee qui s ouvre)',
            'curve 120 50 30 240 -20 -20 60',
            '# power loop avant',
            'flip f','curve 60 0 70 130 0 -50 60',
            '# whip yaw agressif + tonneau',
            'cw 180','flip r',
            '# split-S : demi-tonneau + plongée sèche',
            'flip l','down 60',
            '# slalom incurvé nerveux (gauche / droite)',
            'curve 130 70 15 260 -70 0 60',
            'curve 130 -70 -15 260 70 0 60',
            '# ligne rapide basse + power loop arrière',
            'go 300 0 0 100','flip b','cw 150',
            '# dernière plongée + sortie',
            'down 50','go 200 0 40 100','flip f','land'].join('\n'),
  };
  for (const [id, keyn] of [['pgP1','hover'],['pgP2','square'],['pgP3','swarm'],['pgP4','freestyle'],['pgP5','fpv']])
    $(id).addEventListener('click', ()=>{ $('pgCode').value = PRESETS[keyn]; });
  $('pgRun').addEventListener('click', run);
  $('pgReset').addEventListener('click', ()=>{ reset(true); log('réinitialisé','ok'); });

  grid.visible = false;
  const bigGrid = new THREE.GridHelper(6, 60, 0x262d38, 0x141922);
  bigGrid.rotation.x = Math.PI/2; scene.add(bigGrid);
  camera.position.set(2.4,-2.4,1.6); controls.target.set(0,0,0.35); controls.update();

  const defaultN = Math.max(1, Math.min(MAXD, parseInt(PARAMS.get('drones')||'1',10) || 1));
  const preset = (PARAMS.get('preset')||'').toLowerCase();
  if (PRESETS[preset]) $('pgCode').value = PRESETS[preset];
  reset(true);
  window.__pgState = () => ({ x:+drones[0].root.position.x.toFixed(3),
    y:+drones[0].root.position.y.toFixed(3), z:+drones[0].root.position.z.toFixed(3),
    yaw:+drones[0].yaw.toFixed(3) });
  return { step };
})();

// ---- render only while visible (offscreen-pause, host-controlled) ----
let ioVisible=true, looping=false, hostControlled=false;
window.__vizRendering=()=>looping;
window.__propState=()=>({ n:propMeshes.length,
  posxy:+Math.abs(propMeshes[0].position.x).toFixed(6),
  ang:+propMeshes[0].rotation.z.toFixed(4), spin:spinRate>0 });
function activeR(){ return ioVisible && !document.hidden; }
function startLoop(){ if(!looping){ looping=true; clock.getDelta(); requestAnimationFrame(loop); } }
addEventListener('message', e=>{ const m=e.data;
  if(m&&m.type==='viz'){ hostControlled=true; ioVisible=!!m.visible; if(activeR()) startLoop(); } });
try { new IntersectionObserver(es=>{ if(hostControlled) return; ioVisible=es[0].isIntersecting;
  if(activeR()) startLoop(); }, {threshold:0.01}).observe(view); } catch(_){}
document.addEventListener('visibilitychange', ()=>{ if(activeR()) startLoop(); });

const clock = new THREE.Clock();
function loop(){
  if(!activeR()){ looping=false; return; }
  requestAnimationFrame(loop);
  const dt = Math.min(clock.getDelta(), 0.1);
  if (PG) PG.step(dt);
  else if(spinRate) for(const pm of propMeshes) pm.rotateOnAxis(PROP_SPIN, spinRate*dt*pm.userData.dir);
  controls.update();
  renderer.render(scene, camera);
}
startLoop();
</script>
</body>
</html>
"""


def main():
    specs = "".join(f'<tr><td>{k}</td><td class="v">{v}</td></tr>'
                    for k, v in MODEL["specs"])
    html = (TEMPLATE
            .replace("__IMPORTMAP__", importmap())
            .replace("__NAME__", MODEL["name"])
            .replace("__SUB__", MODEL["sub"])
            .replace("__SPECS__", specs)
            .replace("__MODEL__", json.dumps(
                {k: MODEL[k] for k in ("motors", "prop_z", "motor_z", "frame_z",
                                       "elec", "screws", "standoffs",
                                       "cammount", "explode")},
                separators=(",", ":")))
            .replace("__STLS__", json.dumps({
                # REAL WE are FPV geometry, split from the STEP + the 02-TPU
                # files; STRATOS top plate, motors (real Readytosky 1104),
                # props, board, battery, screws, antenna are our own meshes.
                "frame_bottom": b64(os.path.join(PARTS, "frame_bottom.stl")),
                "frame_top": b64(os.path.join(STL, "jeno_top.stl")),
                "standoff": b64(os.path.join(STL, "standoff_post.stl")),
                "camcage": b64(os.path.join(PARTS, "cam_cage.stl")),
                # DJI O4 Lite system (real STEP -> STL, provided by the owner)
                "o4cam": b64(os.path.join(DJI, "o4_cam_head.stl")),
                "o4airunit": b64(os.path.join(DJI, "o4_airunit.stl")),
                "o4antenna": b64(os.path.join(DJI, "o4_antenna.stl")),
                "cam_mount_top": b64(os.path.join(TPU, "o4_mount_top.stl")),
                "cam_mount_bottom": b64(os.path.join(TPU, "o4_mount_bottom.stl")),
                "arm_bumper": b64(os.path.join(TPU, "arm_bumper.stl")),
                "back_bumper": b64(os.path.join(TPU, "back_bumper.stl")),
                "vtx_mount": b64(os.path.join(TPU, "vtx_antenna_mount.stl")),
                "motor": b64(os.path.join(PARTS, "motor_1104.stl")),
                "prop": b64(os.path.join(STL, "prop.stl")),
                "board": b64(os.path.join(STL, "board.stl")),
                "ghf411": b64(os.path.join(DJI, "ghf411_aio.stl")),
                "battery": b64(os.path.join(STL, "battery.stl")),
                "screw": b64(os.path.join(STL, "screw.stl")),
                "cap": b64(os.path.join(STL, "capacitor.stl")),
                "buzzer": b64(os.path.join(STL, "buzzer.stl")),
                "gps": b64(os.path.join(STL, "gps_module.stl")),
                "rx": b64(os.path.join(STL, "rx_antenna.stl")),
                "cap_holder": b64(os.path.join(STL, "cap_holder.stl")),
                "rx_pcb": b64(os.path.join(STL, "rx_pcb.stl")),
                "rx_holder": b64(os.path.join(STL, "rx_holder.stl")),
                "rx_ant_tpu": b64(os.path.join(STL, "rx_ant_tpu.stl")),
                "cable": b64(os.path.join(STL, "motor_cable.stl")),
            }, separators=(",", ":"))))
    with open(OUT, "w") as f:
        f.write(html)
    print(f"== {MODEL['name']}-001 3D viewer + playground ==")
    print(f"  wrote {os.path.relpath(OUT, REPO)} ({len(html)} B)")


if __name__ == "__main__":
    main()
