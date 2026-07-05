#!/usr/bin/env python3
"""Fr4n6-001 browser 3-D viewer generator.

Builds a single self-contained ``drone_viewer.html`` for the Fr4n6-001
(Avata-2-inspired cinewhoop). Same offline recipe as the Fr4n7 viewer:
Three.js r160 + OrbitControls + STLLoader are inlined as base64 ``data:``
URLs from ``sim/viz/vendor``, and the six part STLs (``fr4n6/cad/stl/
avata_*.stl``) are embedded too — so the file opens by double-click, no
CDN, no server.

Features: orbit + damping, BOUNDED zoom, ground grid, per-group
show/hide + wireframe toggles, prop spin slider, and a ``postMessage``
colour hook ({type:'colors', shell/dome/battery/camera/prop}) compatible
with the site's configurator broadcast.

    python3 fr4n6/viz/gen_viewer.py       # -> fr4n6/viz/drone_viewer.html
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
VENDOR = os.path.join(REPO, "sim", "viz", "vendor")
STL = os.path.join(REPO, "fr4n6", "cad", "stl")
OUT = os.path.join(HERE, "drone_viewer.html")


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
<title>Fr4n6-001 — visualisateur 3D</title>
<style>
  :root{--bg:#0b0e14;--panel:#12161d;--line:#262d38;--ink:#e6edf3;--mut:#8b949e;
        --acc:#2f6fed;--acc2:#63a4ff;}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;font:13px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
            background:var(--bg);color:var(--ink);overflow:hidden}
  #app{display:flex;height:100%}
  #side{width:290px;flex:none;background:var(--panel);border-right:1px solid var(--line);
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
  button{background:#1b212b;color:var(--ink);border:1px solid var(--line);border-radius:6px;
         padding:7px 8px;font-size:12px;cursor:pointer;transition:.12s}
  button:hover{background:#262d38;border-color:#3a4250}
  button.on{background:var(--acc);border-color:var(--acc);color:#fff}
  input[type=range]{width:100%;accent-color:var(--acc)}
  .val{color:var(--acc);font-variant-numeric:tabular-nums}
  table{width:100%;border-collapse:collapse;font-size:12px}
  td{padding:3px 0;color:var(--mut)}
  td.v{text-align:right;color:var(--ink);font-variant-numeric:tabular-nums}
  #tip{position:absolute;right:12px;top:12px;background:rgba(11,14,20,.82);
       border:1px solid var(--line);border-radius:8px;padding:8px 11px;font-size:11px;
       color:var(--mut);max-width:210px}
  #tip b{color:var(--ink)}
  body.embed #side,body.embed #tip{display:none}
  @media (max-width:700px){#app{flex-direction:column}
    #side{width:100%;max-height:44%;border-right:0;border-bottom:1px solid var(--line)}#tip{display:none}}
</style>
</head>
<body>
<div id="app">
  <div id="side">
    <header>
      <h1><b>FR4N6</b>-001 — 3D</h1>
      <p>5" cinewhoop · style Avata 2 · open source</p>
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
      <div style="display:flex;justify-content:space-between"><span>Rotation hélices</span>
        <span class="val" id="spinV">arrêt</span></div>
      <input type="range" id="spin" min="0" max="100" value="0"/>
      <div class="btns" style="margin-top:10px">
        <button id="bWire">Fil de fer</button>
        <button id="bGrid" class="on">Grille</button>
      </div>
    </div>
    <div class="sec">
      <h2>Spécifications (cible)</h2>
      <table>
        <tr><td>Entraxe</td><td class="v">220 mm</td></tr>
        <tr><td>Hélices</td><td class="v">5" (127 mm)</td></tr>
        <tr><td>Moteurs</td><td class="v">2207 brushless</td></tr>
        <tr><td>ESC</td><td class="v">4-en-1 DSHOT600</td></tr>
        <tr><td>Batterie</td><td class="v">2–6S</td></tr>
        <tr><td>MCU vol</td><td class="v">ESP32-P4 + C6</td></tr>
      </table>
    </div>
  </div>
  <div id="view">
    <div id="tip"><b>Souris :</b> glisser = orbite · molette = zoom ·
      clic-droit = pan. Style <b>DJI Avata 2</b> (cinewhoop unibody).</div>
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

const STLB64 = __STLS__;   // {shell, dome, battery, camera, motors, prop}
const PARAMS = new URLSearchParams(location.search);
const EMBED = PARAMS.has('embed');
if (EMBED) document.body.classList.add('embed');

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
controls.minDistance = 0.12; controls.maxDistance = 1.1;

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.add(new THREE.HemisphereLight(0xbfd3ff, 0x202024, 0.55));
const key = new THREE.DirectionalLight(0xffffff, 2.0); key.position.set(0.2,0.26,0.5); scene.add(key);
const rim = new THREE.DirectionalLight(0x88aaff, 0.7); rim.position.set(-0.3,-0.28,0.16); scene.add(rim);
const grid = new THREE.GridHelper(0.5, 40, 0x262d38, 0x171c24);
grid.rotation.x = Math.PI/2; scene.add(grid);

const loader = new STLLoader();
function geo(b64){ const bin = Uint8Array.from(atob(b64), c=>c.charCodeAt(0));
  const g = loader.parse(bin.buffer); g.computeVertexNormals(); return g; }
function mesh(b64, color, metal, rough){
  const m = new THREE.Mesh(geo(b64),
    new THREE.MeshStandardMaterial({color, metalness:metal, roughness:rough}));
  m.scale.setScalar(0.001);          // mm -> m
  return m;
}

const root = new THREE.Group(); scene.add(root);
const G = {};                        // group name -> THREE.Group
function group(name){ const g = new THREE.Group(); G[name]=g; root.add(g); return g; }

// static structure
const gShell = group('shell');  gShell.add(mesh(STLB64.shell, 0x2a2e35, .5, .42));
const gDome  = group('dome');   gDome.add (mesh(STLB64.dome,  0x2f6fed, .35, .45));
const gBatt  = group('battery');gBatt.add (mesh(STLB64.battery,0x3a4048, .3, .5));
const gCam   = group('camera'); gCam.add  (mesh(STLB64.camera,0x14161b, .2, .2));
const gMot   = group('motors'); gMot.add  (mesh(STLB64.motors,0x474d57, .85, .3));

// four props at the duct centres (posXY from the SCAD: 220/2/sqrt2 = 77.78 mm)
const P = 0.07778;
const gProp = group('props');
const propMeshes = [];
for (const [sx, sy] of [[1,1],[-1,1],[-1,-1],[1,-1]]){
  const pm = mesh(STLB64.prop, 0x20242c, .2, .4);
  pm.position.set(sx*P, sy*P, 0);
  pm.scale.set(0.001, (sx*sy>0)?0.001:-0.001, 0.001);   // mirror CW/CCW
  pm.userData.dir = (sx*sy>0)?1:-1;
  gProp.add(pm); propMeshes.push(pm);
}

// centre the whole drone on the grid
const box = new THREE.Box3().setFromObject(root);
const c = box.getCenter(new THREE.Vector3());
root.position.set(-c.x, -c.y, -box.min.z);

// ---- part toggles ----
const GROUPS = {
  shell:  {label:'Coque (unibody + ducts)', color:'#2a2e35'},
  dome:   {label:'Capot électronique',      color:'#2f6fed'},
  battery:{label:'Batterie',                color:'#3a4048'},
  camera: {label:'Caméra',                  color:'#14161b'},
  motors: {label:'Moteurs',                 color:'#8b929c'},
  props:  {label:'Hélices',                 color:'#20242c'},
};
const groupsEl = document.getElementById('groups');
for (const k of Object.keys(GROUPS)){
  const l = document.createElement('label'); l.className='tog';
  l.innerHTML = `<input type="checkbox" checked><span class="sw" style="background:${GROUPS[k].color}"></span>${GROUPS[k].label}`;
  l.querySelector('input').addEventListener('change', e=>{ G[k].visible = e.target.checked; });
  groupsEl.appendChild(l);
}

// ---- live recolour (configurator-compatible) ----
function setColor(g, hex){ if(!hex||!G[g]) return; const col=new THREE.Color(hex);
  G[g].traverse(o=>{ if(o.isMesh) o.material.color.copy(col); }); }
function applyColors(o){ if(!o) return;
  setColor('dome', o.capot!=null?o.capot:o.dome);
  setColor('shell', o.body!=null?o.body:o.shell);
  setColor('props', o.propFront!=null?o.propFront:(o.props!=null?o.props:o.pr));
  setColor('battery', o.battery); setColor('camera', o.camera); }
applyColors({shell:PARAMS.get('shell'), dome:PARAMS.get('dome'),
  body:PARAMS.get('body'), capot:PARAMS.get('capot'), props:PARAMS.get('props')});
addEventListener('message', e=>{ const m=e.data;
  if(m&&m.type==='colors'){ applyColors(m); window.__lastColors=m; } });
try { if (parent && parent!==window) parent.postMessage({type:'ready'}, '*'); } catch(_){}

// ---- wireframe / grid ----
let wire=false;
document.getElementById('bWire').addEventListener('click', e=>{ wire=!wire; e.target.classList.toggle('on',wire);
  root.traverse(o=>{ if(o.isMesh) o.material.wireframe=wire; }); });
document.getElementById('bGrid').addEventListener('click', e=>{ grid.visible=!grid.visible; e.target.classList.toggle('on',grid.visible); });

// ---- spin ----
let spinRate=0;
document.getElementById('spin').addEventListener('input', e=>{ spinRate=e.target.value/100*60;
  document.getElementById('spinV').textContent=e.target.value==0?'arrêt':e.target.value+'%'; });

// ---- views ----
const R=0.34;
const VIEWS={iso:[R*0.8,-R*0.8,R*0.55], top:[0.0001,0,R*1.1], front:[R*1.2,0,R*0.15], side:[0,-R*1.2,R*0.15]};
function setView(v){ const p=VIEWS[v]||VIEWS.iso; camera.position.set(p[0],p[1],p[2]);
  controls.target.set(0,0,0.02); controls.update(); }
document.querySelectorAll('[data-view]').forEach(b=> b.onclick=()=>setView(b.dataset.view));
setView('iso');

function resize(){ const w=view.clientWidth,h=view.clientHeight;
  renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();

// render only while visible (offscreen-pause, host-controlled like the site)
let ioVisible=true, looping=false, hostControlled=false;
window.__vizRendering=()=>looping;
function activeR(){ return ioVisible && !document.hidden; }
function startLoop(){ if(!looping){ looping=true; clock.getDelta(); requestAnimationFrame(loop); } }
addEventListener('message', e=>{ const m=e.data;
  if(m&&m.type==='viz'){ hostControlled=true; ioVisible=!!m.visible; if(activeR()) startLoop(); } });
try { new IntersectionObserver(es=>{ if(hostControlled) return; ioVisible=es[0].isIntersecting;
  if(activeR()) startLoop(); }, {threshold:0.01}).observe(view); } catch(_){}
document.addEventListener('visibilitychange', ()=>{ if(activeR()) startLoop(); });

const clock = new THREE.Clock();
const AXIS = new THREE.Vector3(0,0,1);
function loop(){
  if(!activeR()){ looping=false; return; }
  requestAnimationFrame(loop);
  const dt = Math.min(clock.getDelta(), 0.1);
  if(spinRate) for(const pm of propMeshes) pm.rotateOnAxis(AXIS, spinRate*dt*pm.userData.dir);
  controls.update();
  renderer.render(scene, camera);
}
startLoop();
</script>
</body>
</html>
"""


def main():
    html = (TEMPLATE
            .replace("__IMPORTMAP__", importmap())
            .replace("__STLS__", json.dumps({
                "shell": b64(os.path.join(STL, "avata_shell.stl")),
                "dome": b64(os.path.join(STL, "avata_dome.stl")),
                "battery": b64(os.path.join(STL, "avata_battery.stl")),
                "camera": b64(os.path.join(STL, "avata_camera.stl")),
                "motors": b64(os.path.join(STL, "avata_motors.stl")),
                "prop": b64(os.path.join(STL, "avata_prop.stl")),
            }, separators=(",", ":"))))
    with open(OUT, "w") as f:
        f.write(html)
    print(f"== Fr4n6-001 3D viewer ==")
    print(f"  wrote {os.path.relpath(OUT, REPO)} ({len(html)} B)")


if __name__ == "__main__":
    main()
