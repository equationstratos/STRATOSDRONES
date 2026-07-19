#!/usr/bin/env python3
"""Fr4n9-001 (fpv2) browser 3-D viewer + PLAYGROUND flight simulator.

Same self-contained recipe as every Stratos viewer (Three.js r160 inlined
from ``sim/viz/vendor``, part STLs embedded, opens by double-click) — PLUS
the full in-browser flight simulator ported from the Fr4n7 viewer
(``sim/viz/gen_viewer.py`` PG closure): Tello-SDK script runner, presets,
swarm, and 🎮 keyboard flight (T/L/F + arrows + Z/W/Q/D), rebound on the
fpv2 airframe (98 mm wheelbase, 2" props).

    python3 fpv2/viz/gen_viewer.py             # -> fpv2/viz/drone_viewer.html
    open drone_viewer.html?playground=1        #    the simulator
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
VENDOR = os.path.join(REPO, "sim", "viz", "vendor")
STL = os.path.join(REPO, "fpv2", "cad", "stl")
OUT = os.path.join(HERE, "drone_viewer.html")

MODEL = dict(name="FR4N9", sub="FPV extérieur 2\" · 98 mm · 2S", wb=98,
             posxy=0.034648, prop_z=0.024, motor_z=0.0114, canopy_z=0.0162,
             frame_z=0.008,
             elec=dict(board=[0,0,6.6], airunit=[0,3,11.6], fpvcam=[0,-20,5.2], rxmod=[0,5,17.0], antennas=[0,0,10.8], battery=[0,2,-4.5]),
             specs=[("Entraxe", "98 mm"), ("Hélices", "2\" (51 mm) tri-pales"),
                    ("Moteurs", "1102 ~10000KV 2S"),
                    ("ESC", "AIO BLHeli_S/Bluejay"),
                    ("Radio", "ELRS (CRSF)"), ("Vidéo", "5,8 GHz analogique"),
                    ("Batterie", "2S 650 mAh"), ("Batterie (pose)", "sous la plaque (sangle)"), ("AUW cible", "90-110 g")])


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
        --acc:#2f6fed;--acc2:#63a4ff;}
  *{box-sizing:border-box}
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
  button{background:#1b212b;color:var(--ink);border:1px solid var(--line);border-radius:6px;
         padding:7px 8px;font-size:12px;cursor:pointer;transition:.12s}
  button:hover{background:#262d38;border-color:#3a4250}
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
  #tip{position:absolute;right:12px;top:12px;background:rgba(11,14,20,.82);
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
      <h2>Affichage</h2>
      <div style="display:flex;justify-content:space-between"><span>Rotation hélices</span>
        <span class="val" id="spinV">arrêt</span></div>
      <input type="range" id="spin" min="0" max="100" value="40"/>
      <div class="btns" style="margin-top:10px">
        <button id="bWire">Fil de fer</button>
        <button id="bGrid" class="on">Grille</button>
      </div>
      <div class="mini">Ouvrez <b>?playground=1</b> pour le simulateur de vol
        (clavier + scripts SDK).</div>
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
      clic-droit = pan. Le 2" freestyle : radio <b>ELRS</b>, vidéo
      <b>5,8 GHz analogique</b>, moteurs 1102 2S.</div>
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

// ---- the drone: ONE group whose origin is the ground under its centre ----
// (the playground moves/clones this group; feet touch z=0)
const frameRoot = new THREE.Group(); scene.add(frameRoot);
const G = {};
function group(name){ const g = new THREE.Group(); G[name]=g; frameRoot.add(g); return g; }

const gFrame  = group('frame');  { const m0 = mesh(STLB64.frame, 0x23272e, .3, .55);
  m0.position.z = M.frame_z; gFrame.add(m0); }
const gCanopy = group('canopy'); { const m1 = mesh(STLB64.canopy, 0xe8e8ea, .25, .5);
  m1.position.z = M.canopy_z; gCanopy.add(m1); }
const gMot = group('motors');
for (const [sx, sy] of [[1,1],[-1,1],[-1,-1],[1,-1]]){
  const mm = mesh(STLB64.motor, 0x2e6e63, .8, .32);
  mm.position.set(sx*M.posxy, sy*M.posxy, M.motor_z);
  gMot.add(mm);
}
const gProp = group('props');
const propMeshes = [];
for (const [sx, sy] of [[1,1],[-1,1],[-1,-1],[1,-1]]){
  const pm = mesh(STLB64.prop, 0x4a4e55, .2, .38);
  pm.position.set(sx*M.posxy, sy*M.posxy, M.prop_z);
  pm.scale.set(0.001, (sx*sy>0)?0.001:-0.001, 0.001);   // CW/CCW mirror
  pm.userData.dir = (sx*sy>0)?1:-1;
  pm.userData.front = (sy<0);
  gProp.add(pm); propMeshes.push(pm);
}

// electronics + battery + antennas (positions from the SCAD assembly)
function place(b64, colr, met, rgh, off){
  const m2 = mesh(b64, colr, met, rgh);
  m2.position.set(off[0]/1000, off[1]/1000, M.frame_z + off[2]/1000);
  return m2;
}
const gElec = group('elec');
gElec.add(place(STLB64.board,   0x0a5a30, .2, .5, M.elec.board));
gElec.add(place(STLB64.airunit, 0x1a1c20, .5, .45, M.elec.airunit));
gElec.add(place(STLB64.fpvcam,  0x17181c, .35, .4, M.elec.fpvcam));
gElec.add(place(STLB64.rxmod,   0x1c2430, .3, .5, M.elec.rxmod));
const gBatt = group('battery');
gBatt.add(place(STLB64.battery, 0x2b2f36, .25, .55, M.elec.battery));
const gAnt = group('antennas');
gAnt.add(place(STLB64.antennas, 0xd8dadc, .25, .45, M.elec.antennas));

// ---- part toggles ----
const GROUPS = {
  frame:  {label:'Châssis (plaque + pods)', color:'#23272e'},
  canopy: {label:'Canopy (plaques + pont)', color:'#e8e8ea'},
  motors: {label:'Moteurs 1102 (sarcelle)', color:'#2e6e63'},
  props:  {label:'Hélices 2" (fumées)',     color:'#4a4e55'},
  elec:   {label:'Électronique (carte + air unit + cam + RX)', color:'#0a5a30'},
  battery:{label:'Batterie 2S (sous la plaque)', color:'#2b2f36'},
  antennas:{label:'Antennes (VTX + RX)',        color:'#101012'},
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
  setColor('frame',  o.body!=null?o.body:o.frame);
  setColor('canopy', o.capot!=null?o.capot:o.canopy);
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
let spinRate=0.4*60;                       // hélices en rotation par défaut
document.getElementById('spinV').textContent='40%';
document.getElementById('spin').addEventListener('input', e=>{ spinRate=e.target.value/100*60;
  document.getElementById('spinV').textContent=e.target.value==0?'arrêt':e.target.value+'%'; });
const R=0.22;
const VIEWS={iso:[R*0.9,-R*0.9,R*0.62], top:[0.0001,0,R*1.25], front:[0,-R*1.35,R*0.2], side:[R*1.35,0,R*0.2]};
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
  const SPACING = 0.6, MAXD = 6;      // tighter formation: 65 mm micros
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
  };
  for (const [id, keyn] of [['pgP1','hover'],['pgP2','square'],['pgP3','swarm'],['pgP4','freestyle']])
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
                {k: MODEL[k] for k in ("posxy", "prop_z", "motor_z", "canopy_z", "frame_z", "elec")},
                separators=(",", ":")))
            .replace("__STLS__", json.dumps({
                "frame": b64(os.path.join(STL, "frame.stl")),
                "canopy": b64(os.path.join(STL, "canopy.stl")),
                "prop": b64(os.path.join(STL, "prop.stl")),
                "motor": b64(os.path.join(STL, "motor.stl")),
                "board": b64(os.path.join(STL, "board.stl")),
                "airunit": b64(os.path.join(STL, "airunit.stl")),
                "fpvcam": b64(os.path.join(STL, "fpvcam.stl")),
                "rxmod": b64(os.path.join(STL, "rxmod.stl")),
                "battery": b64(os.path.join(STL, "battery.stl")),
                "antennas": b64(os.path.join(STL, "antennas.stl")),
            }, separators=(",", ":"))))
    with open(OUT, "w") as f:
        f.write(html)
    print(f"== {MODEL['name']}-001 3D viewer + playground ==")
    print(f"  wrote {os.path.relpath(OUT, REPO)} ({len(html)} B)")


if __name__ == "__main__":
    main()
