#!/usr/bin/env python3
"""Stratos FPV Configurator — a self-contained, parametric drone configurator.

Pick a class (2" / 3" / 5" / 7"), swap real popular parts (frame, motors, FC,
RX, camera, VTX, props, battery), recolour every group, load a preset build,
and see the quad rebuilt in 3-D instantly. FPV style. The geometry is fully
PROCEDURAL and scales with the class dims, so any size renders correctly.

    python3 configurator/gen_configurator.py   # -> configurator/configurator.html

Part specs are curated from the popular models sold by StudioSPORT and
La Caméra Embarquée (KV, sizes, cells, weights are public catalogue figures).
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
VENDOR = os.path.join(REPO, "sim", "viz", "vendor")
OUT = os.path.join(HERE, "configurator.html")


def data_url(path):
    with open(path, "rb") as f:
        return "data:text/javascript;base64," + base64.b64encode(f.read()).decode("ascii")


def importmap():
    v = lambda *p: data_url(os.path.join(VENDOR, *p))
    return json.dumps({"imports": {
        "three": v("three.module.js"),
        "three/addons/controls/OrbitControls.js": v("addons", "controls", "OrbitControls.js"),
        "three/addons/environments/RoomEnvironment.js": v("addons", "environments", "RoomEnvironment.js"),
    }}, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Class geometry (all mm). wb = motor-to-motor diagonal (the "wheelbase").
# ---------------------------------------------------------------------------
CLASSES = {
    "2": dict(label='2" — Tiny / Whoop', wb=110, body_l=62, body_w=30, plate=2.0,
              arm_w=6, arm_t=3.0, motorD=8.6, motorH=7, statorD=6, bell=8.4,
              propD=51, blades=3, stack=25.5, screw=2.0, standoff=16,
              batt=[52, 20, 15], camW=14, vtxW=13, mass="55-80 g"),
    "3": dict(label='3" — Cinewhoop / LR', wb=155, body_l=78, body_w=34, plate=2.0,
              arm_w=7, arm_t=3.0, motorD=15, motorH=9, statorD=13, bell=15,
              propD=76, blades=3, stack=25.5, screw=2.0, standoff=22,
              batt=[68, 34, 24], camW=19, vtxW=20, mass="130-190 g"),
    "5": dict(label='5" — Freestyle / Race', wb=220, body_l=95, body_w=40, plate=2.5,
              arm_w=10, arm_t=4.0, motorD=28, motorH=13, statorD=22, bell=27,
              propD=127, blades=3, stack=30.5, screw=3.0, standoff=32,
              batt=[105, 42, 32], camW=19, vtxW=30, mass="480-650 g"),
    "7": dict(label='7" — Long Range', wb=300, body_l=120, body_w=46, plate=3.0,
              arm_w=12, arm_t=5.0, motorD=32, motorH=16, statorD=28, bell=31,
              propD=178, blades=2, stack=30.5, screw=3.0, standoff=38,
              batt=[140, 46, 46], camW=19, vtxW=30, mass="700-950 g"),
}

# ---------------------------------------------------------------------------
# Parts catalogue — real popular models (StudioSPORT / La Caméra Embarquée).
# Each entry: name + short spec string. `cls` limits it to compatible classes.
# ---------------------------------------------------------------------------
CATALOG = {
    "frame": [
        dict(n="WE are FPV JeNo Pocket V2", s="2.5\" wide-X, carbone 3/2 mm", cls=["2"]),
        dict(n="GEPRC Cinelog25", s="2.5\" cinewhoop, ducts TPU", cls=["2"]),
        dict(n="BetaFPV Pavo Pico", s="2\" cinewhoop O3/O4", cls=["2"]),
        dict(n="GEPRC Cinelog35 V2", s="3.5\" cinewhoop 6S", cls=["3"]),
        dict(n="iFlight Nazgul Evoque F3", s="3\" freestyle", cls=["3"]),
        dict(n="Flywoo Firefly 3\"", s="3\" DC16 nano LR", cls=["3"]),
        dict(n="iFlight Nazgul5 V3", s="5\" freestyle, bras 5 mm", cls=["5"]),
        dict(n="GEPRC Mark5", s="5\" freestyle, DeadCat", cls=["5"]),
        dict(n="TBS Source One V5", s="5\" open-source", cls=["5"]),
        dict(n="ImpulseRC Apex", s="5\" premium, arms 6 mm", cls=["5"]),
        dict(n="iFlight Chimera7 Pro", s="7\" LR DeadCat", cls=["7"]),
        dict(n="GEPRC MK5 7\" LR", s="7\" long range", cls=["7"]),
        dict(n="Flywoo Explorer LR 7\"", s="7\" ultra-light LR", cls=["7"]),
    ],
    "motor": [
        dict(n="BetaFPV 1102 18000KV", s="1102 · 1S", cls=["2"]),
        dict(n="iFlight XING 1103 8000KV", s="1103 · 2S", cls=["2"]),
        dict(n="T-Motor F1404 3800KV", s="1404 · 4S", cls=["3"]),
        dict(n="iFlight XING2 1507 3600KV", s="1507 · 4S", cls=["3"]),
        dict(n="Emax ECO II 2207 1700KV", s="2207 · 6S", cls=["5"]),
        dict(n="iFlight XING2 2207 1800KV", s="2207 · 6S", cls=["5"]),
        dict(n="T-Motor F60 Pro V 2207 1750KV", s="2207 · 6S", cls=["5"]),
        dict(n="RCINPOWER GTS 2306 1950KV", s="2306 · 6S", cls=["5"]),
        dict(n="T-Motor F90 2806.5 1300KV", s="2806.5 · 6S", cls=["7"]),
        dict(n="iFlight XING2 2807 1300KV", s="2807 · 6S", cls=["7"]),
    ],
    "fc": [
        dict(n="JHEMCU GHF411 AIO 20A", s="F411 · BLHeli_S 20A · 25.5", cls=["2", "3"]),
        dict(n="SpeedyBee F405 AIO 25A", s="F405 · 25A · 25.5", cls=["2", "3"]),
        dict(n="Mamba F405 MK2 + 35A", s="F405 · 4in1 35A", cls=["3", "5"]),
        dict(n="SpeedyBee F405 V4 55A", s="F405 · 55A · 30.5", cls=["5"]),
        dict(n="Mamba F722 + F60 60A", s="F722 · 60A · 30.5", cls=["5"]),
        dict(n="Holybro Kakute H7 + Tekko32 65A", s="H7 · 65A · 30.5", cls=["5", "7"]),
        dict(n="T-Motor F7 + F55A Pro II", s="F7 · 4in1 55A", cls=["5", "7"]),
    ],
    "rx": [
        dict(n="HappyModel EP1 ELRS 2.4G", s="ELRS 2.4 · T-antenne", cls=["2", "3", "5", "7"]),
        dict(n="RadioMaster RP1 ELRS 2.4G", s="ELRS 2.4 · nano", cls=["2", "3", "5", "7"]),
        dict(n="BetaFPV ELRS Lite 2.4G", s="ELRS 2.4 · ultra-light", cls=["2", "3"]),
        dict(n="TBS Crossfire Nano RX", s="Crossfire 868/915", cls=["5", "7"]),
        dict(n="RadioMaster RP4TD ELRS Diversity", s="ELRS 2.4 · diversité", cls=["5", "7"]),
        dict(n="ELRS 915 MHz nano (LR)", s="ELRS 915 · long range", cls=["7"]),
    ],
    "cam": [
        dict(n="DJI O4 Air Unit Lite", s="Numérique HD · caméra + air unit", cls=["2", "3", "5", "7"]),
        dict(n="DJI O4 Air Unit Pro", s="Numérique HD · 4K", cls=["3", "5", "7"]),
        dict(n="DJI O3 Air Unit", s="Numérique HD · 19 mm", cls=["3", "5", "7"]),
        dict(n="Walksnail Avatar HD Mini", s="Numérique HD 1080", cls=["3", "5", "7"]),
        dict(n="Caddx Ratel 2", s="Analogique · 1200TVL · 19 mm", cls=["3", "5", "7"]),
        dict(n="RunCam Phoenix 2", s="Analogique · 1000TVL", cls=["3", "5", "7"]),
        dict(n="Caddx Ant / Nano", s="Analogique nano · 14 mm", cls=["2"]),
    ],
    "vtx": [
        dict(n="(intégré à la caméra numérique)", s="DJI / Walksnail", cls=["2", "3", "5", "7"]),
        dict(n="Rush Tank Ultimate 2G4", s="Analogique · 25-1000 mW", cls=["3", "5", "7"]),
        dict(n="TBS Unify Pro32 HV", s="Analogique · 5-800 mW", cls=["3", "5", "7"]),
        dict(n="HappyModel OVX303", s="Analogique nano · 25-300 mW", cls=["2", "3"]),
    ],
    "prop": [
        dict(n="Gemfan 2020 tri", s="2\" · tri-pale", cls=["2"]),
        dict(n="HQ 3018 tri", s="3\" · tri-pale", cls=["3"]),
        dict(n="Gemfan D63 (2.5\")", s="2.5\" · tri-pale", cls=["2"]),
        dict(n="Gemfan 51466 tri", s="5.1\" · tri-pale freestyle", cls=["5"]),
        dict(n="HQProp 5.1x3.1x3", s="5\" · race", cls=["5"]),
        dict(n="Gemfan 7040 bi", s="7\" · bi-pale LR", cls=["7"]),
        dict(n="HQProp 7x4x3", s="7\" · tri-pale", cls=["7"]),
    ],
    "battery": [
        dict(n="GNB 1S 450 mAh", s="1S · 450 mAh", cls=["2"]),
        dict(n="CNHL 2S 550 mAh", s="2S · 550 mAh", cls=["2"]),
        dict(n="DOGCOM 3S 560 mAh", s="3S · 560 mAh", cls=["2", "3"]),
        dict(n="CNHL 4S 650 mAh", s="4S · 650 mAh", cls=["3"]),
        dict(n="GNB 6S 1050 mAh", s="6S · 1050 mAh · race", cls=["5"]),
        dict(n="CNHL 6S 1300 mAh", s="6S · 1300 mAh · freestyle", cls=["5"]),
        dict(n="Tattu 6S 1550 mAh", s="6S · 1550 mAh", cls=["5"]),
        dict(n="CNHL 6S 3000 mAh", s="6S · 3000 mAh · LR", cls=["7"]),
        dict(n="Molicel P42A 6S2P", s="6S2P Li-ion · LR", cls=["7"]),
    ],
}

# Preset builds — pick real, coherent combos.
PRESETS = {
    "tiny": dict(label='🐝 Tiny Whoop 2"', cls="2", sel=dict(
        frame="WE are FPV JeNo Pocket V2", motor="iFlight XING 1103 8000KV",
        fc="JHEMCU GHF411 AIO 20A", rx="HappyModel EP1 ELRS 2.4G",
        cam="DJI O4 Air Unit Lite", vtx="(intégré à la caméra numérique)",
        prop="Gemfan D63 (2.5\")", battery="DOGCOM 3S 560 mAh")),
    "cine3": dict(label='🎥 Cinewhoop 3"', cls="3", sel=dict(
        frame="GEPRC Cinelog35 V2", motor="iFlight XING2 1507 3600KV",
        fc="SpeedyBee F405 AIO 25A", rx="RadioMaster RP1 ELRS 2.4G",
        cam="DJI O3 Air Unit", vtx="(intégré à la caméra numérique)",
        prop="HQ 3018 tri", battery="CNHL 4S 650 mAh")),
    "free5": dict(label='🔥 Freestyle 5"', cls="5", sel=dict(
        frame="iFlight Nazgul5 V3", motor="iFlight XING2 2207 1800KV",
        fc="SpeedyBee F405 V4 55A", rx="RadioMaster RP1 ELRS 2.4G",
        cam="DJI O4 Air Unit Pro", vtx="(intégré à la caméra numérique)",
        prop="Gemfan 51466 tri", battery="CNHL 6S 1300 mAh")),
    "race5": dict(label='🏁 Racing 5"', cls="5", sel=dict(
        frame="TBS Source One V5", motor="RCINPOWER GTS 2306 1950KV",
        fc="Mamba F722 + F60 60A", rx="TBS Crossfire Nano RX",
        cam="Caddx Ratel 2", vtx="TBS Unify Pro32 HV",
        prop="HQProp 5.1x3.1x3", battery="GNB 6S 1050 mAh")),
    "lr7": dict(label='🛰️ Long Range 7"', cls="7", sel=dict(
        frame="iFlight Chimera7 Pro", motor="iFlight XING2 2807 1300KV",
        fc="Holybro Kakute H7 + Tekko32 65A", rx="ELRS 915 MHz nano (LR)",
        cam="DJI O3 Air Unit", vtx="(intégré à la caméra numérique)",
        prop="Gemfan 7040 bi", battery="Molicel P42A 6S2P")),
}

# default colours per group
COLORS = dict(plate="#15181d", arms="#15181d", motors="#c9962e", props="#e8912a",
              stack="#0f6b39", camera="#1b1e24", vtx="#20242b", battery="#22262d",
              antenna="#dadade", hardware="#c8ccd2")

GROUPS = [("plate", "Châssis (plaques + bras)"), ("motors", "Moteurs"),
          ("props", "Hélices"), ("stack", "FC / ESC (stack)"),
          ("camera", "Caméra / VTX numérique"), ("vtx", "VTX analogique"),
          ("battery", "Batterie"), ("antenna", "Antennes RX"),
          ("hardware", "Visserie / entretoises")]

CATEGORIES = [("frame", "Châssis"), ("motor", "Moteurs"), ("fc", "FC / ESC"),
              ("prop", "Hélices"), ("cam", "Caméra"), ("vtx", "VTX"),
              ("rx", "Récepteur"), ("battery", "Batterie")]


TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Stratos FPV Configurator</title>
<style>
  :root{--bg:#0b0e14;--panel:#12161d;--line:#262d38;--ink:#e6edf3;--mut:#8b949e;
        --acc:#2f6fed;--acc2:#63a4ff;--btn:#1b212b;--btnh:#262d38;}
  body.light{--bg:#eef1f5;--panel:#f7f9fc;--line:#d3d9e0;--ink:#1a1f26;--mut:#5a636e;
        --btn:#e6eaf0;--btnh:#d7dde6;}
  *{box-sizing:border-box} html,body{margin:0;height:100%;overflow:hidden;
    font:13px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
  #app{display:flex;height:100%}
  .side{width:310px;flex:none;background:var(--panel);border-right:1px solid var(--line);
    display:flex;flex-direction:column;overflow-y:auto}
  #view{flex:1;position:relative} canvas{display:block}
  header{padding:13px 16px;border-bottom:1px solid var(--line)}
  header h1{margin:0;font-size:15px;letter-spacing:.3px} header h1 b{color:var(--acc)}
  header p{margin:3px 0 0;color:var(--mut);font-size:11px}
  .sec{padding:11px 16px;border-bottom:1px solid var(--line)}
  .sec h2{margin:0 0 8px;font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--mut)}
  .row{display:flex;gap:6px;flex-wrap:wrap}
  button{background:var(--btn);color:var(--ink);border:1px solid var(--line);border-radius:6px;
    padding:7px 9px;font-size:12px;cursor:pointer;transition:.12s;flex:1}
  button:hover{background:var(--btnh);border-color:var(--acc)} button.on{background:var(--acc);border-color:var(--acc);color:#fff}
  select{width:100%;background:var(--btn);color:var(--ink);border:1px solid var(--line);
    border-radius:6px;padding:7px;font-size:12px;margin-top:2px}
  label.f{display:block;margin:8px 0 0} label.f span{color:var(--mut);font-size:11px}
  .spec{color:var(--acc2);font-size:11px;margin-top:2px;min-height:14px}
  .cg{display:flex;align-items:center;gap:8px;margin:5px 0;cursor:pointer}
  .cg input[type=color]{width:16px;height:16px;padding:0;border:1px solid var(--line);border-radius:3px;
    background:none;cursor:pointer;-webkit-appearance:none;flex:none}
  .cg input[type=color]::-webkit-color-swatch{border:none;border-radius:2px}
  .cg span{flex:1} .cg input[type=checkbox]{accent-color:var(--acc)}
  table{width:100%;border-collapse:collapse;font-size:12px} td{padding:2px 0;color:var(--mut)}
  td.v{text-align:right;color:var(--ink)}
  #tip{position:absolute;right:12px;top:12px;background:rgba(11,14,20,.8);border:1px solid var(--line);
    border-radius:8px;padding:8px 11px;font-size:11px;color:var(--mut);max-width:230px}
  #tip b{color:var(--ink)}
</style></head>
<body><div id="app">
  <div class="side">
    <header><h1><b>STRATOS</b> · FPV Configurator</h1>
      <p>Choisis une taille, échange les pièces, personnalise — rendu 3D instantané.</p></header>
    <div class="sec"><h2>Configurations prédéfinies</h2><div class="row" id="presets"></div></div>
    <div class="sec"><h2>Taille du châssis</h2><div class="row" id="classes"></div></div>
    <div class="sec"><h2>Pièces</h2><div id="parts"></div></div>
    <div class="sec"><h2>Couleurs des pièces</h2><div id="colors"></div>
      <div class="row" style="margin-top:8px"><button id="bReset">Couleurs par défaut</button></div></div>
    <div class="sec"><h2>Vues & affichage</h2>
      <div class="row"><button data-view="iso">Iso</button><button data-view="top">Dessus</button>
        <button data-view="front">Face</button><button data-view="side">Côté</button></div>
      <div class="row" style="margin-top:6px"><button id="bSpin" class="on">⟳ Hélices</button>
        <button id="bTheme">☀/🌙</button></div></div>
    <div class="sec"><h2>Fiche du build</h2><table id="specs"></table></div>
  </div>
  <div id="view"><div id="tip"><b>Souris</b> : glisser = orbite · molette = zoom · clic-droit = pan.</div></div>
</div>
<script type="importmap">__IMPORTMAP__</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const CLASSES=__CLASSES__, CATALOG=__CATALOG__, PRESETS=__PRESETS__,
      DEFCOL=__COLORS__, GROUPS=__GROUPS__, CATS=__CATS__;

const view=document.getElementById('view');
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.05;
view.appendChild(renderer.domElement);
const scene=new THREE.Scene(); scene.background=new THREE.Color(0x0b0e14);
const camera=new THREE.PerspectiveCamera(42,1,0.001,100); camera.up.set(0,0,1);
const controls=new OrbitControls(camera,renderer.domElement); controls.enableDamping=true;
const pmrem=new THREE.PMREMGenerator(renderer);
scene.environment=pmrem.fromScene(new RoomEnvironment(),0.04).texture;
scene.add(new THREE.HemisphereLight(0xbfd3ff,0x202024,0.5));
const key=new THREE.DirectionalLight(0xffffff,2.0); key.position.set(0.3,0.4,0.8); scene.add(key);
let grid=new THREE.GridHelper(1,20,0x2a3340,0x161c24); grid.rotation.x=Math.PI/2; scene.add(grid);

const root=new THREE.Group(); scene.add(root);
let G={};   // named part groups (current build)
const state={cls:'5', sel:{}, colors:Object.assign({},DEFCOL), spin:true};

// ---- geometry helpers (mm in, m out) ----
const M=v=>v/1000;
function matOf(name,o){ o=o||{}; const m=new THREE.MeshStandardMaterial({
  color:new THREE.Color(state.colors[name]||'#888'), metalness:o.m!=null?o.m:.35, roughness:o.r!=null?o.r:.55});
  if(o.op!=null){m.transparent=true;m.opacity=o.op;m.depthWrite=false;m.side=THREE.DoubleSide;} return m; }
function addBox(g,name,w,d,h,pos,rot,o){ const m=new THREE.Mesh(new THREE.BoxGeometry(M(w),M(d),M(h)),matOf(name,o));
  if(pos)m.position.set(M(pos[0]),M(pos[1]),M(pos[2])); if(rot)m.rotation.set(rot[0]||0,rot[1]||0,rot[2]||0); g.add(m); return m; }
function addCyl(g,name,dTop,dBot,h,pos,o,seg){ const m=new THREE.Mesh(
  new THREE.CylinderGeometry(M(dTop/2),M(dBot/2),M(h),seg||28),matOf(name,o));
  m.rotation.x=Math.PI/2; if(pos)m.position.set(M(pos[0]),M(pos[1]),M(pos[2])); g.add(m); return m; }
function grp(n){ const g=new THREE.Group(); G[n]=g; root.add(g); return g; }

function rrShape(w,d,r){ const s=new THREE.Shape(); const x=w/2,y=d/2;
  s.moveTo(-x+r,-y); s.lineTo(x-r,-y); s.quadraticCurveTo(x,-y,x,-y+r); s.lineTo(x,y-r);
  s.quadraticCurveTo(x,y,x-r,y); s.lineTo(-x+r,y); s.quadraticCurveTo(-x,y,-x,y-r);
  s.lineTo(-x,-y+r); s.quadraticCurveTo(-x,-y,-x+r,-y); return s; }
function addPlate(g,name,w,d,h,z,r){ const geo=new THREE.ExtrudeGeometry(rrShape(M(w),M(d),M(r||2/1000)),
  {depth:M(h),bevelEnabled:false}); const m=new THREE.Mesh(geo,matOf(name,{m:.25,r:.5}));
  m.position.z=M(z); g.add(m); return m; }

function motorRadius(){ return CLASSES[state.cls].wb/2; }       // mm centre->motor
function motorPositions(){ const r=motorRadius()*Math.SQRT1_2;
  return [[r,r],[-r,r],[-r,-r],[r,-r]]; }

// build one propeller (hub + N curved-ish blades), translucent
function buildProp(C){ const g=new THREE.Group(); const R=C.propD/2;
  g.add(addCyl(g,'props',C.bell*0.5,C.bell*0.5,3,[0,0,0],{},20));
  for(let b=0;b<C.blades;b++){ const bl=new THREE.Mesh(
      new THREE.BoxGeometry(M(R*0.92),M(R*0.16),M(0.8)),matOf('props',{m:.05,r:.35,op:.6}));
    bl.position.set(M(R*0.5),0,M(1.6)); bl.rotation.z=0.18;
    const pv=new THREE.Group(); pv.add(bl); pv.rotation.z=b*2*Math.PI/C.blades; g.add(pv);}
  return g; }

let propPivots=[];
function buildDrone(){
  root.clear(); G={}; propPivots=[];
  const C=CLASSES[state.cls];
  const pos=motorPositions();
  // ---------- CHASSIS : plaques + bras ----------
  const gP=grp('plate');
  addPlate(gP,'plate',C.body_w,C.body_l,C.plate,0,4);                 // bottom plate
  // arms centre -> each motor
  pos.forEach(([x,y])=>{ const len=Math.hypot(x,y)*0.96; const ang=Math.atan2(y,x);
    const m=addBox(gP,'arms',len,C.arm_w,C.arm_t,[x*0.5,y*0.5,0],[0,0,ang]); });
  // top plate on standoffs
  addPlate(gP,'plate',C.body_w,C.body_l*0.62,C.plate*0.8,C.standoff,4);
  // ---------- VISSERIE / entretoises ----------
  const gH=grp('hardware'); const st=[[C.body_w*0.38,C.body_l*0.28],[-C.body_w*0.38,C.body_l*0.28],
    [C.body_w*0.38,-C.body_l*0.28],[-C.body_w*0.38,-C.body_l*0.28]];
  st.forEach(([x,y])=>addCyl(gH,'hardware',C.screw+1.6,C.screw+1.6,C.standoff,[x,y,C.standoff/2],{m:.85,r:.3},14));
  // ---------- MOTEURS ----------
  const gM=grp('motors'); const mz=C.plate+C.motorH/2;
  pos.forEach(([x,y])=>{ addCyl(gM,'motors',C.bell,C.statorD,C.motorH,[x,y,mz],{m:.8,r:.35},28);
    addCyl(gM,'hardware',2,2,C.motorH*0.4,[x,y,C.plate+C.motorH],{m:.9,r:.25},12); });   // shaft
  // ---------- HELICES ----------
  const gPr=grp('props'); const pz=C.plate+C.motorH+1.5;
  pos.forEach(([x,y])=>{ const p=buildProp(C); p.position.set(M(x),M(y),M(pz)); gPr.add(p); propPivots.push(p); });
  // ---------- STACK (FC/ESC) ----------
  const gS=grp('stack'); const sk=C.stack;
  addBox(gS,'stack',sk+3,sk+3,1.4,[0,0,C.plate+4],null,{m:.2,r:.5});
  addBox(gS,'hardware',6,4,3,[sk*0.3,-sk*0.3,C.plate+6],null,{m:.4,r:.5});   // usb-ish
  // ---------- CAMERA / VTX ----------
  const gC=grp('camera'); const camY=C.body_l*0.42; const cw=C.camW;
  const isDigital=/DJI|Walksnail|O3|O4/i.test(state.sel.cam||'');
  addBox(gC,'camera',cw,cw*0.9,cw,[0,camY,C.standoff*0.7],[ -0.5,0,0],{m:.4,r:.4});      // cam body
  const lens=new THREE.Mesh(new THREE.CylinderGeometry(M(cw*0.32),M(cw*0.34),M(cw*0.4),24),
    new THREE.MeshStandardMaterial({color:0x0a1420,metalness:.6,roughness:.12}));
  lens.rotation.x=Math.PI/2*0.4-Math.PI/2; lens.position.set(0,M(camY+cw*0.5),M(C.standoff*0.78)); gC.add(lens);
  if(isDigital){ addBox(gC,'camera',sk-2,sk-2,C.plate+6,[0,-6,C.plate+9],null,{m:.35,r:.5}); } // air unit
  // ---------- VTX analogique ----------
  const gV=grp('vtx'); if(!isDigital){ addBox(gV,'vtx',C.vtxW,C.vtxW*0.8,3,[0,-C.body_l*0.18,C.standoff*0.6],null,{m:.3,r:.5}); }
  // ---------- BATTERIE ----------
  const gB=grp('battery'); const bt=C.batt; const bz=C.standoff+bt[2]/2+1;
  addBox(gB,'battery',bt[1],bt[0],bt[2],[0,-C.body_l*0.02,bz],null,{m:.1,r:.55});
  addBox(gB,'hardware',7,6,5,[0,-bt[0]/2-4,bz],[Math.PI/2,0,0],{m:.2,r:.5});   // XT30
  // ---------- ANTENNES RX (V arrière, gaines TPU blanches) ----------
  const gA=grp('antenna'); const ay=-C.body_l*0.34;
  [[1,-1],[-1,-1]].forEach(([sx])=>{ const u=new THREE.Group();
    const tubeL=C.wb*0.16, antL=C.wb*0.26;
    const tube=new THREE.Mesh(new THREE.CylinderGeometry(M(2.7),M(2.7),M(tubeL),16),matOf('antenna',{m:.1,r:.85}));
    tube.rotation.x=Math.PI/2; tube.position.set(0,0,M(tubeL/2)); u.add(tube);
    const coax=new THREE.Mesh(new THREE.CylinderGeometry(M(0.8),M(0.8),M(antL),12),
      new THREE.MeshStandardMaterial({color:0x141414,metalness:.2,roughness:.5}));
    coax.rotation.x=Math.PI/2; coax.position.set(0,0,M(tubeL+antL/2-2)); u.add(coax);
    const dir=new THREE.Vector3(sx*0.75,-0.9,0.22).normalize();
    u.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),dir);
    u.position.set(M(sx*C.body_w*0.28),M(ay),M(C.plate+2)); gA.add(u); });

  applyColors(); applyToggles(); frameCamera(); refreshSpecs();
}

function applyColors(){ for(const [k] of GROUPS){ const g=G[k]; if(!g)continue;
  const col=new THREE.Color(state.colors[k]||'#888');
  g.traverse(o=>{ if(o.isMesh && o.material && !o.material.__fixed) o.material.color.copy(col); }); } }
function applyToggles(){ for(const [k] of GROUPS){ const g=G[k]; if(g&&state['hide_'+k]) g.visible=false; } }

function frameCamera(){ const box=new THREE.Box3().setFromObject(root);
  const s=new THREE.Vector3(); box.getSize(s); const c=new THREE.Vector3(); box.getCenter(c);
  const d=Math.max(s.x,s.y,s.z)*1.9+0.05; camera.position.set(c.x+d*0.7,c.y-d*0.8,c.z+d*0.55);
  controls.target.copy(c); controls.update(); }
const VIEWS={iso:[0.7,-0.8,0.55],top:[0,0.02,1.3],front:[0,-1.3,0.18],side:[1.3,0,0.18]};
function setView(v){ const box=new THREE.Box3().setFromObject(root),c=new THREE.Vector3(),s=new THREE.Vector3();
  box.getCenter(c); box.getSize(s); const d=Math.max(s.x,s.y,s.z)*1.9+0.05; const p=VIEWS[v]||VIEWS.iso;
  camera.position.set(c.x+p[0]*d,c.y+p[1]*d,c.z+p[2]*d); controls.target.copy(c); controls.update(); }

// ---------- UI ----------
const $=id=>document.getElementById(id);
function opts(cat){ return CATALOG[cat].filter(p=>p.cls.includes(state.cls)); }
function buildParts(){ const host=$('parts'); host.innerHTML='';
  for(const [cat,label] of CATS){ const list=opts(cat);
    const l=document.createElement('label'); l.className='f';
    l.innerHTML=`<span>${label}</span>`;
    const sel=document.createElement('select'); sel.id='sel_'+cat;
    list.forEach(p=>{ const o=document.createElement('option'); o.value=p.n; o.textContent=p.n; sel.appendChild(o); });
    if(state.sel[cat] && list.some(p=>p.n===state.sel[cat])) sel.value=state.sel[cat];
    else state.sel[cat]=list[0]?list[0].n:'';
    const sp=document.createElement('div'); sp.className='spec'; sp.id='spec_'+cat;
    const cur=list.find(p=>p.n===sel.value); sp.textContent=cur?cur.s:'';
    sel.addEventListener('change',()=>{ state.sel[cat]=sel.value;
      const c=list.find(p=>p.n===sel.value); sp.textContent=c?c.s:''; buildDrone(); });
    l.appendChild(sel); host.appendChild(l); host.appendChild(sp); } }

function buildColors(){ const host=$('colors'); host.innerHTML='';
  for(const [k,label] of GROUPS){ const row=document.createElement('label'); row.className='cg';
    row.innerHTML=`<input type="checkbox" checked><input type="color" value="${state.colors[k]||'#888888'}"><span>${label}</span>`;
    row.querySelector('input[type=color]').addEventListener('input',e=>{ state.colors[k]=e.target.value; applyColors(); });
    row.querySelector('input[type=checkbox]').addEventListener('change',e=>{ state['hide_'+k]=!e.target.checked;
      if(G[k])G[k].visible=e.target.checked; });
    host.appendChild(row); } }

function buildClasses(){ const host=$('classes'); host.innerHTML='';
  for(const k of Object.keys(CLASSES)){ const b=document.createElement('button');
    b.textContent=k+'"'; b.className=(k===state.cls)?'on':''; b.style.flex='0 0 auto'; b.style.minWidth='46px';
    b.title=CLASSES[k].label;
    b.addEventListener('click',()=>{ state.cls=k; state.sel={}; buildClasses(); buildParts(); buildDrone(); });
    host.appendChild(b); } }

function buildPresets(){ const host=$('presets'); host.innerHTML='';
  for(const [id,p] of Object.entries(PRESETS)){ const b=document.createElement('button');
    b.textContent=p.label; b.style.flex='1 1 46%';
    b.addEventListener('click',()=>{ state.cls=p.cls; state.sel=Object.assign({},p.sel);
      buildClasses(); buildParts(); buildDrone(); }); host.appendChild(b); } }

function refreshSpecs(){ const C=CLASSES[state.cls]; const rows=[
  ['Classe',C.label],['Entraxe',C.wb+' mm'],['Hélices',(C.propD/25.4).toFixed(1)+'" ('+C.propD+' mm)'],
  ['Châssis',state.sel.frame||'—'],['Moteurs',state.sel.motor||'—'],['FC/ESC',state.sel.fc||'—'],
  ['Caméra',state.sel.cam||'—'],['Récepteur',state.sel.rx||'—'],['Batterie',state.sel.battery||'—'],
  ['Masse (ordre)',C.mass]];
  $('specs').innerHTML=rows.map(r=>`<tr><td>${r[0]}</td><td class="v">${r[1]}</td></tr>`).join(''); }

$('bReset').addEventListener('click',()=>{ state.colors=Object.assign({},DEFCOL); buildColors(); applyColors(); });
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));
$('bSpin').addEventListener('click',e=>{ state.spin=!state.spin; e.target.classList.toggle('on',state.spin); });
$('bTheme').addEventListener('click',()=>{ document.body.classList.toggle('light');
  const lg=document.body.classList.contains('light'); scene.background=new THREE.Color(lg?0xeef1f5:0x0b0e14);
  scene.remove(grid); grid=new THREE.GridHelper(1,20,lg?0xb9c2cd:0x2a3340,lg?0xd3d9e0:0x161c24);
  grid.rotation.x=Math.PI/2; scene.add(grid); });

function resize(){ const w=view.clientWidth,h=view.clientHeight; renderer.setSize(w,h);
  camera.aspect=w/h; camera.updateProjectionMatrix(); }
addEventListener('resize',resize);

// boot with the Freestyle 5" preset
state.cls='5'; state.sel=Object.assign({},PRESETS.free5.sel);
buildPresets(); buildClasses(); buildParts(); buildColors(); buildDrone(); resize(); setView('iso');

let t=0;
(function loop(){ requestAnimationFrame(loop); t+=0.016;
  if(state.spin) propPivots.forEach((p,i)=>{ p.rotation.z += (i%2?1:-1)*0.9; });
  controls.update(); renderer.render(scene,camera); })();
</script></body></html>
"""


def main():
    html = (TEMPLATE
            .replace("__IMPORTMAP__", importmap())
            .replace("__CLASSES__", json.dumps(CLASSES, separators=(",", ":")))
            .replace("__CATALOG__", json.dumps(CATALOG, separators=(",", ":")))
            .replace("__PRESETS__", json.dumps(PRESETS, separators=(",", ":")))
            .replace("__COLORS__", json.dumps(COLORS, separators=(",", ":")))
            .replace("__GROUPS__", json.dumps(GROUPS, separators=(",", ":")))
            .replace("__CATS__", json.dumps(CATEGORIES, separators=(",", ":"))))
    with open(OUT, "w") as f:
        f.write(html)
    print("== Stratos FPV Configurator ==")
    print(f"  wrote {os.path.relpath(OUT, REPO)} ({len(html)} B)")


if __name__ == "__main__":
    main()
