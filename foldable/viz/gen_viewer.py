#!/usr/bin/env python3
"""Fr4n7-F (foldable) browser 3-D viewer generator.

Builds a single self-contained ``drone_viewer.html`` for the foldable-arm
Fr4n7 variant. Same offline recipe as the other viewers: Three.js r160 +
OrbitControls + STLLoader inlined as base64 ``data:`` URLs from
``sim/viz/vendor``, plus the foldable part STLs (``foldable/cad/stl``) and
the shared Tello prop (``sim/viz/prop.stl``) — opens by double-click, no
CDN, no server.

On top of the usual features (orbit, bounded zoom, part toggles, prop spin,
postMessage recolour), this one animates the FOLDING: each arm is its own
group pivoted at its hinge; a slider + « Déployer / Replier » buttons tween
the fold, and ``postMessage {type:'deploy'|'fold'}`` (or ``?fold=1``) drives
it from a host page — the browser twin of the `deploy` SDK verb.

    python3 foldable/viz/gen_viewer.py    # -> foldable/viz/drone_viewer.html
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
VENDOR = os.path.join(REPO, "sim", "viz", "vendor")
STL = os.path.join(REPO, "foldable", "cad", "stl")
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
<title>Fr4n7-F — visualisateur 3D (bras repliables)</title>
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
  button.big{font-size:13px;font-weight:600;padding:9px 8px}
  input[type=range]{width:100%;accent-color:var(--acc)}
  .val{color:var(--acc);font-variant-numeric:tabular-nums}
  table{width:100%;border-collapse:collapse;font-size:12px}
  td{padding:3px 0;color:var(--mut)}
  td.v{text-align:right;color:var(--ink);font-variant-numeric:tabular-nums}
  #tip{position:absolute;right:12px;top:12px;background:rgba(11,14,20,.82);
       border:1px solid var(--line);border-radius:8px;padding:8px 11px;font-size:11px;
       color:var(--mut);max-width:220px}
  #tip b{color:var(--ink)}
  body.embed #side,body.embed #tip{display:none}
  @media (max-width:700px){#app{flex-direction:column}
    #side{width:100%;max-height:46%;border-right:0;border-bottom:1px solid var(--line)}#tip{display:none}}
</style>
</head>
<body>
<div id="app">
  <div id="side">
    <header>
      <h1><b>FR4N7</b>-F — 3D</h1>
      <p>bras repliables · ressorts + verrou · open source</p>
    </header>
    <div class="sec">
      <h2>Pliage</h2>
      <div class="btns">
        <button id="bDeploy" class="big on">Déployer</button>
        <button id="bFold" class="big">Replier</button>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:10px">
        <span>Position</span><span class="val" id="foldV">déployé</span></div>
      <input type="range" id="fold" min="0" max="100" value="0"/>
      <p style="margin:8px 0 0;color:var(--mut);font-size:11px">
        V1 : bouton mécanique · V2 : servo + commande <b style="color:var(--ink)">deploy</b>
        (spécifiée — voir <span style="color:var(--acc2)">DESIGN.md</span>)</p>
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
        <tr><td>Entraxe déployé</td><td class="v">118 mm</td></tr>
        <tr><td>Hélices</td><td class="v">3" (76 mm)</td></tr>
        <tr><td>Plié (hors pales)</td><td class="v">≈ 68 × 83 mm</td></tr>
        <tr><td>Moteurs</td><td class="v">8520 brushed</td></tr>
        <tr><td>Pivots</td><td class="v">M2 + ressorts</td></tr>
        <tr><td>Déverrouillage</td><td class="v">bouton / servo</td></tr>
        <tr><td>Électronique</td><td class="v">carte Fr4n7</td></tr>
      </table>
    </div>
  </div>
  <div id="view">
    <div id="tip"><b>Souris :</b> glisser = orbite · molette = zoom · clic-droit = pan.
      Bras avant <b>inversés</b> : pliés, ils ne se croisent jamais.</div>
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

const STLB64 = __STLS__;   // {body,capot,arm_fr,arm_fl,arm_rr,arm_rl,latch,button,prop}
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
controls.minDistance = 0.07; controls.maxDistance = 0.8;

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.add(new THREE.HemisphereLight(0xbfd3ff, 0x202024, 0.55));
const key = new THREE.DirectionalLight(0xffffff, 2.0); key.position.set(0.2,0.26,0.5); scene.add(key);
const rim = new THREE.DirectionalLight(0x88aaff, 0.7); rim.position.set(-0.3,-0.28,0.16); scene.add(rim);
const grid = new THREE.GridHelper(0.4, 32, 0x262d38, 0x171c24);
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

// ---- static structure ----
const gBody  = group('body');  gBody.add (mesh(STLB64.body,  0xcfd4da, .25, .55));
const gCapot = group('capot'); gCapot.add(mesh(STLB64.capot, 0x2f6fed, .35, .45));
const gMech  = group('mech');
gMech.add(mesh(STLB64.latch,  0x23272e, .3, .5));
const bt = mesh(STLB64.button, 0x2f6fed, .3, .45);
bt.position.set(0.010, -0.0296, 0.0106); bt.rotation.x = Math.PI/2;  // head outside
gMech.add(bt);

// ---- the four folding arms — each a group pivoted at its hinge ----
// FOLD_A and the pivot/motor table come from frame_foldable.scad
// (FOLD_A = 79.448 deg; pivots (±19, ∓37) mm; motors ±22.72, ∓4.72 mm local).
const FOLD_A = 1.38668;
const ARMS = {
  fr: {stl:'arm_fr', pivot:[ 0.019,-0.037], sign:+1, motor:[ 0.02272,-0.00472], front:true },
  fl: {stl:'arm_fl', pivot:[-0.019,-0.037], sign:-1, motor:[-0.02272,-0.00472], front:true },
  rr: {stl:'arm_rr', pivot:[ 0.019, 0.037], sign:-1, motor:[ 0.02272, 0.00472], front:false},
  rl: {stl:'arm_rl', pivot:[-0.019, 0.037], sign:+1, motor:[-0.02272, 0.00472], front:false},
};
const gArms = group('arms');
const gProp = group('props');        // toggle proxy — props live inside arm groups
const A = {}, propMeshes = [];
for (const k of Object.keys(ARMS)){
  const a = ARMS[k];
  const g = new THREE.Group();
  g.position.set(a.pivot[0], a.pivot[1], 0);
  g.add(mesh(STLB64[a.stl], 0xb9bec6, .3, .5));
  // prop on this arm's motor: front pods are inverted -> prop UNDER the belly
  const pm = mesh(STLB64.prop, 0x2456c9, .2, .4);
  pm.position.set(a.motor[0], a.motor[1], a.front ? -0.0035 : 0.0197);
  if (a.front) pm.rotation.x = Math.PI;              // inverted pod
  const base = (a.pivot[0]*a.pivot[1] > 0) ? 1 : -1;
  pm.userData.dir = base * (a.front ? -1 : 1);       // flip restores visual sense
  pm.userData.front = a.front;
  g.add(pm); propMeshes.push(pm);
  A[k] = g; gArms.add(g);
}

// centre the whole drone on the grid (deployed pose)
const box = new THREE.Box3().setFromObject(root);
const c = box.getCenter(new THREE.Vector3());
root.position.set(-c.x, -c.y, -box.min.z);

// ---- fold animation ----
let foldT = PARAMS.get('fold') ? 1 : 0, foldTarget = foldT;
function applyFold(t){
  for (const k of Object.keys(A)) A[k].rotation.z = ARMS[k].sign * FOLD_A * t;
  document.getElementById('fold').value = Math.round(t*100);
  document.getElementById('foldV').textContent =
    t < 0.02 ? 'déployé' : t > 0.98 ? 'replié' : Math.round(t*100)+'%';
  document.getElementById('bDeploy').classList.toggle('on', t < 0.5);
  document.getElementById('bFold').classList.toggle('on', t >= 0.5);
}
applyFold(foldT);
window.__foldT = () => foldT;
document.getElementById('bDeploy').addEventListener('click', ()=>{ foldTarget = 0; startLoop(); });
document.getElementById('bFold').addEventListener('click',  ()=>{ foldTarget = 1; startLoop(); });
document.getElementById('fold').addEventListener('input', e=>{
  foldT = foldTarget = e.target.value/100; applyFold(foldT); startLoop(); });

// ---- part toggles ----
const GROUPS = {
  body:  {label:'Châssis (chapes + pieds)', color:'#cfd4da'},
  capot: {label:'Capot',                    color:'#2f6fed'},
  arms:  {label:'Bras repliables',          color:'#b9bec6'},
  mech:  {label:'Verrou + bouton',          color:'#23272e'},
  props: {label:'Hélices',                  color:'#2456c9'},
};
const groupsEl = document.getElementById('groups');
for (const k of Object.keys(GROUPS)){
  const l = document.createElement('label'); l.className='tog';
  l.innerHTML = `<input type="checkbox" checked><span class="sw" style="background:${GROUPS[k].color}"></span>${GROUPS[k].label}`;
  l.querySelector('input').addEventListener('change', e=>{
    if (k==='props'){ for (const pm of propMeshes) pm.visible = e.target.checked; }
    else G[k].visible = e.target.checked; });
  groupsEl.appendChild(l);
}

// ---- live recolour (configurator-compatible) ----
function paint(list, hex){ if(!hex) return; const col=new THREE.Color(hex);
  for (const o of list) o.traverse(m=>{ if(m.isMesh) m.material.color.copy(col); }); }
function applyColors(o){ if(!o) return;
  paint([G.capot], o.capot!=null?o.capot:o.dome);
  paint([G.body],  o.body!=null?o.body:o.shell);
  paint(Object.values(A).map(g=>g.children[0]), o.arms);
  paint([G.mech],  o.mech);
  paint(propMeshes, o.propFront!=null?o.propFront:(o.props!=null?o.props:o.pr)); }
applyColors({body:PARAMS.get('body'), shell:PARAMS.get('shell'), capot:PARAMS.get('capot'),
  dome:PARAMS.get('dome'), arms:PARAMS.get('arms'), props:PARAMS.get('props')});
addEventListener('message', e=>{ const m=e.data; if(!m) return;
  if(m.type==='colors'){ applyColors(m); window.__lastColors=m; }
  if(m.type==='deploy'){ foldTarget=0; startLoop(); }
  if(m.type==='fold'){ foldTarget=1; startLoop(); } });
try { if (parent && parent!==window) parent.postMessage({type:'ready'}, '*'); } catch(_){}

// ---- wireframe / grid ----
let wire=false;
document.getElementById('bWire').addEventListener('click', e=>{ wire=!wire; e.target.classList.toggle('on',wire);
  root.traverse(o=>{ if(o.isMesh) o.material.wireframe=wire; }); });
document.getElementById('bGrid').addEventListener('click', e=>{ grid.visible=!grid.visible; e.target.classList.toggle('on',grid.visible); });

// ---- spin ----
let spinRate=0;
document.getElementById('spin').addEventListener('input', e=>{ spinRate=e.target.value/100*60;
  document.getElementById('spinV').textContent=e.target.value==0?'arrêt':e.target.value+'%';
  startLoop(); });

// ---- views ----
const R=0.2;
const VIEWS={iso:[R*0.85,-R*0.85,R*0.6], top:[0.0001,0,R*1.15], front:[R*1.25,0,R*0.18], side:[0,-R*1.25,R*0.18]};
function setView(v){ const p=VIEWS[v]||VIEWS.iso; camera.position.set(p[0],p[1],p[2]);
  controls.target.set(0,0,0.015); controls.update(); }
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
function loop(){
  if(!activeR()){ looping=false; return; }
  requestAnimationFrame(loop);
  const dt = Math.min(clock.getDelta(), 0.1);
  if (foldT !== foldTarget){
    const step = dt/1.2;                                  // full sweep ~1.2 s
    foldT += Math.sign(foldTarget-foldT)*Math.min(step, Math.abs(foldTarget-foldT));
    applyFold(foldT);
  }
  if(spinRate) for(const pm of propMeshes) pm.rotation.z += spinRate*dt*pm.userData.dir;
  else if (foldT > 0.55) for(const pm of propMeshes){     // transport pose: blades along the arms
    const r = pm.rotation.z, tgt = Math.round((r-Math.PI/2)/Math.PI)*Math.PI + Math.PI/2;
    pm.rotation.z += (tgt-r)*Math.min(1, dt*5);
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
    stl = lambda n: b64(os.path.join(STL, n + ".stl"))
    html = (TEMPLATE
            .replace("__IMPORTMAP__", importmap())
            .replace("__STLS__", json.dumps({
                "body": stl("body"),
                "capot": stl("capot"),
                "arm_fr": stl("arm_fr"),
                "arm_fl": stl("arm_fl"),
                "arm_rr": stl("arm_rr"),
                "arm_rl": stl("arm_rl"),
                "latch": stl("latch"),
                "button": stl("button"),
                "prop": b64(os.path.join(REPO, "sim", "viz", "prop.stl")),
            }, separators=(",", ":"))))
    with open(OUT, "w") as f:
        f.write(html)
    print("== Fr4n7-F foldable 3D viewer ==")
    print(f"  wrote {os.path.relpath(OUT, REPO)} ({len(html)} B)")


if __name__ == "__main__":
    main()
