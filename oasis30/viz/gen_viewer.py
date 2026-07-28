#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OASIS 30 — visualisateur 3-D + simulateur d'assemblage, en pages autonomes.

Même recette que les autres visualisateurs du dépôt (voir
`TinyHoopMK1/viz/gen_viewer.py`, dont sont repris tels quels le socle Three.js,
le tissu carbone procédural, les helpers `mesh/group/place` et le module
d'assemblage) — rebranché sur le châssis **Sub250 OasisFly30** :

  · les pièces carbone et imprimées viennent de `../cad/stl/viz/` (maillage
    grossier, généré par `../cad/export.py` en même temps que les STL
    d'impression : les deux ne peuvent donc pas diverger) ;
  · les 4 pièces **Sub250 d'origine** sont reprises telles quelles ;
  · l'électronique se choisit dans un sélecteur : **stock O4 Pro** ou
    **Stratos programmable**.

    python3 oasis30/viz/gen_viewer.py
        -> oasis30/viz/drone_viewer.html      (visualisateur)
        -> oasis30/build/build.html           (simulateur d'assemblage)
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OASIS = os.path.dirname(HERE)
REPO = os.path.dirname(OASIS)
VENDOR = os.path.join(REPO, "sim", "viz", "vendor")
VIZSTL = os.path.join(OASIS, "cad", "stl", "viz")
TH = os.path.join(REPO, "TinyHoopMK1", "cad", "stl")
OUT = os.path.join(HERE, "drone_viewer.html")

import sys
sys.path.insert(0, os.path.join(OASIS, "cad"))
import tune as T                                            # noqa: E402

# ─────────────────────────────────────────────────────── modèle
MODEL = dict(
    name="OASIS 30", sub="Sub250 OasisFly30 · 3\" · 150 mm · 4S",
    wb=T.WB, track_x=T.TRACK_X, track_y=T.TRACK_Y, prop_d=T.PROP_D,
    mx=T.MX, my=T.MY, arm_angle=None,                       # calculé en JS
    z=dict(bottom=T.Z_BOTTOM, arm=T.Z_ARM, arm_t=T.ARM_T, mid=T.Z_MID, deck=T.Z_DECK,
           standoff=T.Z_DECK + T.PLATE_D, top=T.Z_TOP, total=T.H_TOTAL),
    cage=dict(gap=T.CAGE_GAP, t=T.CAGE_T, y=T.CAM_Y, z=T.CAM_Z, tilt=T.CAM_TILT,
              w=T.CAM_W, h=T.CAM_H),
    standoffs=dict(top=T.STANDOFFS_TOP, cam=T.STANDOFFS_CAM),
    stack=T.STACK, stack_y=T.STACK_Y, xt30_y=T.XT30_Y, ground=11.2 - T.Z_ARM,                   # patin de pied sous le bras
    specs=[("Entraxe", "150 mm (125 × 82,9)"), ("Hélices", "3\" · 76 mm"),
           ("Moteurs", "1404 4500 KV"), ("Plaques", "basse 2,5 · médiane 2,5 · roof 2,0"),
           ("Bras", "3 mm carbone"), ("Stack", "20×20 (VTX 25,5)"),
           ("Vidéo", "DJI O4 Pro"), ("Batterie", "4S 660-720 mAh XT30"),
           ("Hauteur", "32,5 mm"), ("Masse châssis", "~170 g sans batterie")],
)


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
        "three/addons/geometries/RoundedBoxGeometry.js": v("addons", "geometries", "RoundedBoxGeometry.js"),
    }}, separators=(",", ":"))


def stls():
    o = lambda n: b64(os.path.join(VIZSTL, n + ".stl"))
    t = lambda n: b64(os.path.join(TH, n + ".stl"))
    return {
        # ── carbone (généré par ../cad/export.py)
        "bottom": o("bottom_plate"), "mid": o("mid_plate"), "deck": o("deck_plate"),
        "top": o("top_plate"), "arm": o("arm"), "cage": o("cam_side_plate"),
        "standoff": o("standoff"),
        # ── pièces imprimées Stratos
        "guard": o("arm_guard"), "battpad": o("batt_pad"),
        "grommet": o("xt30_grommet"), "gpsmount": o("gps_mount"),
        "bumper": o("rear_bumper"),
        # ── pièces Sub250 d'origine, telles quelles
        "flanc_g": o("flanc_gauche"), "flanc_d": o("flanc_droit"),
        "footpad": o("sub250_foot_pad"),
        "rxplate": o("sub250_rx_plate"), "tailmount": o("sub250_tail_mount"),
        # ── DJI O4 Pro : STEP du constructeur, converti par prep_vendor.py
        "o4air": o("dji_air_unit"), "o4cam": o("dji_camera"), "o4ant": o("dji_antenna"),
        # ── moteur XING2 1404 : STEP du constructeur, même conversion
        "motor": o("xing2_1404"),
        # ── pièces réutilisées du TinyHoop MK1 (mêmes composants du commerce)
        "prop": t("prop"), "screw": t("screw"), "cap": t("capacitor"),
        "gps": t("gps_module"), "rxpcb": t("rx_pcb"), "board": t("board"),
    }


TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>OASIS 30 · 3D</title>
<style>
  :root{--bg:#0b0e14;--panel:#12161d;--line:#262d38;--ink:#e6edf3;--mut:#8b949e;
        --acc:#2f6fed;--acc2:#63a4ff;--btn:#1b212b;--btnh:#262d38;--ok:#47d18a;}
  body.light{--bg:#eef1f5;--panel:#f7f9fc;--line:#d3d9e0;--ink:#1a1f26;--mut:#5a636e;
        --acc:#2f6fed;--acc2:#1b4fd0;--btn:#e6eaf0;--btnh:#d7dde6;}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;font:13px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
            background:var(--bg);color:var(--ink);overflow:hidden}
  #app{display:flex;height:100%}
  .sidebar{width:300px;flex:none;background:var(--panel);border-right:1px solid var(--line);
           display:flex;flex-direction:column;overflow-y:auto}
  #view{flex:1;position:relative}
  canvas{display:block;width:100%;height:100%}
  header{padding:14px 16px;border-bottom:1px solid var(--line)}
  header h1{margin:0;font-size:15px;letter-spacing:.3px}
  header h1 b{color:var(--acc2)}
  header p{margin:3px 0 0;color:var(--mut);font-size:11px}
  .sec{padding:12px 16px;border-bottom:1px solid var(--line)}
  .sec h2{margin:0 0 9px;font-size:11px;text-transform:uppercase;letter-spacing:.6px;
          color:var(--mut);font-weight:600}
  label.tog{display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none;margin:4px 0}
  label.tog input[type=checkbox]{accent-color:var(--acc)}
  label.tog span{flex:1}
  label.tog input[type=color]{width:15px;height:15px;padding:0;border:1px solid var(--line);
        border-radius:3px;background:none;cursor:pointer;flex:none;appearance:none;-webkit-appearance:none}
  label.tog input[type=color]::-webkit-color-swatch{border:none;border-radius:2px}
  label.tog input[type=color]::-webkit-color-swatch-wrapper{padding:0}
  label.tog.on span{color:var(--acc2);font-weight:600}
  .btns{display:grid;grid-template-columns:1fr 1fr;gap:6px}
  button,select{background:var(--btn);color:var(--ink);border:1px solid var(--line);
        border-radius:7px;padding:7px 9px;font:inherit;font-size:12px;cursor:pointer;width:100%}
  button:hover{background:var(--btnh)}
  button.pri{background:var(--acc);border-color:var(--acc);color:#fff}
  input[type=range]{width:100%;accent-color:var(--acc)}
  .modes{display:grid;gap:6px}
  .mode{display:flex;gap:10px;align-items:center;padding:9px 10px;border:1px solid var(--line);
        border-radius:9px;cursor:pointer;background:var(--btn)}
  .mode:hover{background:var(--btnh)}
  .mode.on{border-color:var(--acc);background:linear-gradient(90deg,rgba(47,111,237,.18),transparent)}
  .mode .ic{font-size:17px;line-height:1}
  .mode b{display:block;font-size:12.5px}
  .mode i{font-style:normal;font-size:10.5px;color:var(--mut)}
  #hud{position:absolute;left:12px;bottom:12px;font-size:11px;color:var(--mut);
       background:rgba(11,14,20,.66);padding:6px 10px;border-radius:8px;pointer-events:none;
       max-width:70%}
  body.light #hud{background:rgba(247,249,252,.8)}
  #fs{position:absolute;right:12px;top:12px;width:auto;padding:6px 11px;opacity:.85}
  table.spec{width:100%;border-collapse:collapse;font-size:11.5px}
  table.spec td{padding:2.5px 0;vertical-align:top}
  table.spec td:first-child{color:var(--mut);width:44%}
  .note{font-size:11px;color:var(--mut);margin-top:8px;line-height:1.45}
  .plist{max-height:none}
  .prow{display:flex;align-items:center;gap:7px;padding:3px 5px;border-radius:6px;cursor:pointer}
  .prow:hover{background:var(--btn)}
  .prow.sel{background:rgba(47,111,237,.2);outline:1px solid var(--acc)}
  .prow .nm{flex:1;font-size:12px}
  .prow .qt{font-size:10px;color:var(--mut)}
  .prow.done .nm{color:var(--ok)}
  body:not(.build) .buildonly{display:none}
  body.build .viewonly{display:none}
  .adjrow{display:grid;grid-template-columns:24px 1fr 46px;align-items:center;gap:6px;
          font-size:11px;color:var(--mut);margin:2px 0}
  .adjrow b{color:var(--ink);text-align:right;font-weight:600;font-variant-numeric:tabular-nums}
  #adjOut{white-space:pre-line;user-select:text;font-size:10.5px;line-height:1.5;
          background:var(--btn);border:1px solid var(--line);border-radius:6px;
          padding:6px 8px;margin-top:8px;max-height:120px;overflow:auto}
</style>
<script type="importmap">__IMPORTMAP__</script>
</head>
<body>
<div id="app">
  <aside class="sidebar">
    <header>
      <h1>OASIS <b>30</b></h1>
      <p id="subtitle">__SUB__</p>
    </header>

    <div class="sec">
      <h2>Mode</h2>
      <div class="modes" id="modes">
        <div class="mode" data-mode="view"><span class="ic">🔍</span>
          <span><b>Visualisateur</b><i>explorer, isoler, éclater</i></span></div>
        <div class="mode" data-mode="build"><span class="ic">🔧</span>
          <span><b>Assemblage</b><i>monter le drone pièce par pièce</i></span></div>
      </div>
    </div>

    <div class="sec">
      <h2>Électronique</h2>
      <select id="elecSel">
        <option value="stock">Stock Sub250 — RedFox A3 + DJI O4 Pro</option>
        <option value="stratos">Stratos programmable — TINYHOOP AIO + LoRa</option>
      </select>
      <div class="note" id="elecNote"></div>
    </div>

    <div class="sec">
      <h2>Composants</h2>
      <div id="parts" class="plist"></div>
    </div>

    <div class="sec buildonly">
      <h2>Assemblage</h2>
      <div class="btns">
        <button id="asmAll" class="pri">Tout assembler</button>
        <button id="asmScatter">Éparpiller</button>
        <button id="asmTidy">Ranger les pièces</button>
        <button id="asmGhost">Fantômes : oui</button>
      </div>
      <div class="note" id="asmNote">Un clic surligne · un double-clic emboîte.</div>
    </div>

    <div class="sec">
      <h2>Vue</h2>
      <label class="tog"><span>Éclatée</span></label>
      <input type="range" id="explode" min="0" max="100" value="0"/>
      <div class="btns" style="margin-top:8px">
        <button id="vIso">Iso</button><button id="vTop">Dessus</button>
        <button id="vSide">Côté</button><button id="vFront">Face</button>
        <button id="wire">Fil de fer</button><button id="theme">Thème clair</button>
      </div>
    </div>

    <div class="sec viewonly" id="adjSec">
      <h2>Réglages</h2>
      <select id="adjSel"></select>
      <div id="adjRows" style="margin-top:8px"></div>
      <div class="btns" style="margin-top:8px">
        <button id="adjReset">Remettre à zéro</button>
        <button id="adjCopy">Copier les valeurs</button>
      </div>
      <div id="adjOut"></div>
    </div>

    <div class="sec">
      <h2>Fiche</h2>
      <table class="spec" id="specs"></table>
      <div class="note">Châssis re-modélisé d'après les cotes publiées et les
        photos du kit. Les 4 pièces imprimées Sub250 sont les fichiers d'origine.</div>
    </div>
  </aside>

  <div id="view"><button id="fs">⛶ Plein écran</button><div id="hud"></div></div>
</div>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const M = __MODEL__;
const STLB64 = __STLS__;
const PARAMS = new URLSearchParams(location.search);
const BUILD = __BUILD_DEFAULT__ ? !PARAMS.has('nobuild') : PARAMS.has('build');
if (BUILD) document.body.classList.add('build');
document.getElementById('subtitle').textContent = M.sub;

const ARM_ANGLE = Math.atan2(M.my, M.mx);
const D = Math.PI / 180;

/* ─────────────────────────────── socle (repris du visualisateur TinyHoop) */
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
try { window.__cam = camera; window.__ctr = controls; } catch(_){}
controls.enableDamping = true; controls.dampingFactor = .08;
controls.minDistance = .08; controls.maxDistance = BUILD ? 2.0 : 1.2;

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), .04).texture;
scene.add(new THREE.HemisphereLight(0xbfd3ff, 0x202024, .55));
const key = new THREE.DirectionalLight(0xffffff, 2.0); key.position.set(.2,.26,.5); scene.add(key);
const rim = new THREE.DirectionalLight(0x88aaff, .7); rim.position.set(-.3,-.28,.16); scene.add(rim);
let grid;
function makeGrid(light){ if(grid){ scene.remove(grid); grid.geometry.dispose(); grid.material.dispose(); }
  grid = new THREE.GridHelper(.5, 40, light?0x9aa4b0:0x262d38, light?0xc2c9d2:0x171c24);
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
  m.scale.setScalar(.001);                       // mm -> m
  return m;
}
/* tissu carbone procédural — identique au TinyHoop MK1 */
function carbonMaps(){
  const S=256, N=8;
  const cn=document.createElement('canvas'); cn.width=cn.height=S;
  const cr=document.createElement('canvas'); cr.width=cr.height=S;
  const n=cn.getContext('2d'), r=cr.getContext('2d');
  n.fillStyle='#8080ff'; n.fillRect(0,0,S,S);
  r.fillStyle='#6f6f6f'; r.fillRect(0,0,S,S);
  const t=S/N;
  for(let j=0;j<N;j++) for(let i=0;i<N;i++){
    const horiz = (((i+j)>>1) & 1)===0, x0=i*t, y0=j*t;
    const g = horiz ? n.createLinearGradient(x0,y0,x0,y0+t) : n.createLinearGradient(x0,y0,x0+t,y0);
    g.addColorStop(0,'#8f8fff'); g.addColorStop(.5,'#8080ff'); g.addColorStop(1,'#7373ff');
    n.fillStyle=g; n.fillRect(x0,y0,t,t);
    const rg = horiz ? r.createLinearGradient(x0,y0,x0,y0+t) : r.createLinearGradient(x0,y0,x0+t,y0);
    rg.addColorStop(0,'#8a8a8a'); rg.addColorStop(.5,'#5f5f5f'); rg.addColorStop(1,'#828282');
    r.fillStyle=rg; r.fillRect(x0,y0,t,t);
  }
  const mk=(cv)=>{ const tx=new THREE.CanvasTexture(cv);
    tx.wrapS=tx.wrapT=THREE.RepeatWrapping; tx.colorSpace=THREE.NoColorSpace; return tx; };
  return { normal: mk(cn), rough: mk(cr) };
}
const CARBON_TEX = carbonMaps();
function planarUV(g, pitch){ g.computeBoundingBox();
  const p=g.attributes.position, uv=new Float32Array(p.count*2);
  for(let i=0;i<p.count;i++){ uv[i*2]=p.getX(i)/pitch; uv[i*2+1]=p.getY(i)/pitch; }
  g.setAttribute('uv', new THREE.BufferAttribute(uv,2)); }
function carbonMesh(b64, color){
  const g=geo(b64); planarUV(g, 5.5);
  const mat=new THREE.MeshStandardMaterial({color, metalness:.22, roughness:.46,
    normalMap:CARBON_TEX.normal, normalScale:new THREE.Vector2(.4,.4),
    roughnessMap:CARBON_TEX.rough});
  const m=new THREE.Mesh(g, mat); m.scale.setScalar(.001); return m;
}

/* ─────────────────────────────── la scène du drone */
const frameRoot = new THREE.Group(); scene.add(frameRoot);
frameRoot.position.z = M.ground/1000;               // les patins touchent le sol
const G = {}; try { window.G = G; window.THREE = THREE; } catch(_){}
function group(name){ const g = new THREE.Group(); G[name]=g; frameRoot.add(g); return g; }
/* Groupe RÉGLABLE : son origine est posée sur la pièce elle-même, pas au centre
   du drone — sans ça une rotation ferait tourner la pièce autour du châssis
   entier au lieu de la faire pivoter sur place. */
function adjGroup(name, px, py, pz){
  const g = group(name);
  g.position.set(px/1000, py/1000, pz/1000);
  g.userData.pivot = [px, py, pz];
  g.userData.base = g.position.clone();
  g.userData.baseRot = g.rotation.clone();
  return g;
}
function addAt(g, m, x, y, z){            // place un maillage dans un groupe réglable
  const p = g.userData.pivot;
  m.position.set((x - p[0])/1000, (y - p[1])/1000, (z - p[2])/1000);
  g.add(m); return m;
}
/* Certains STL sortent de la CAO **déjà à leur place** dans le drone (les
   plaques, les joues de cage) : il ne faut surtout pas leur rajouter l'offset
   du groupe, sinon la pièce part deux fois plus loin que voulu. */
function addAbs(g, m){ return addAt(g, m, 0, 0, 0); }
function keep(m){ m.userData.keepColor = true; return m; }

const CARBON = 0x1a1d21, TPU = 0x24272d, ALU = 0xb9bec7, SUB250 = 0x2ec4b6;

/* plaques : les STL sont déjà à leur Z réel, sortis de la CAO */
const gBottom = group('bottom'); gBottom.add(carbonMesh(STLB64.bottom, CARBON));
const gMid    = group('mid');    gMid.add(carbonMesh(STLB64.mid, CARBON));
const gDeck   = group('deck');   gDeck.add(carbonMesh(STLB64.deck, CARBON));
const gTop    = group('top');    gTop.add(carbonMesh(STLB64.top, CARBON));

/* bras : le STL est à plat à l'origine, on le repivote aux 4 angles.
   Le bras étant symétrique par rapport à son axe, une rotation suffit —
   pas besoin de miroir. */
const ARM_R_IN = 16.0;
const gArms = group('arms');
const ARM_DIR = [ARM_ANGLE, Math.PI-ARM_ANGLE, Math.PI+ARM_ANGLE, -ARM_ANGLE];
for (const a of ARM_DIR){
  const g = new THREE.Group(); g.rotation.z = a;
  const m = carbonMesh(STLB64.arm, CARBON);
  m.position.set(ARM_R_IN/1000, 0, M.z.arm/1000);
  g.add(m); gArms.add(g);
}

/* cage caméra : le STL est le flanc droit, le gauche est son miroir */
/* Le STL `cam_side_plate` sort de la CAO **à sa place** (x 12,35→14,85 ·
   y 43→65 · z 5,5→31) : on ne lui ajoute aucun décalage. Le pivot du groupe est
   posé sur l'axe de basculement de la caméra, c'est autour de lui que tournent
   les curseurs de réglage. */
const gCage = adjGroup('cage', 0, M.cage.y, M.cage.z);
for (const sx of [1,-1]){
  const m = carbonMesh(STLB64.cage, CARBON);
  m.scale.x = sx*.001;
  addAbs(gCage, m);
}

/* entretoises */
const gStand = group('standoffs');
for (const [x,y] of M.standoffs.top.concat(M.standoffs.cam)){
  const m = mesh(STLB64.standoff, ALU, .85, .28);
  m.position.set(x/1000, y/1000, M.z.standoff/1000);
  gStand.add(m);
}

/* pièces imprimées Stratos */
/* Pas de berceau TPU dans le montage : le STEP DJI montre que la caméra O4 Pro
   porte ses **propres tourillons** Ø 2,1 en y = ±10, et que sa largeur hors
   tourillons est de 23,8 mm — elle bascule donc directement entre les deux
   joues carbone, dont l'écart intérieur est de 24,7. C'est ce que montrent les
   photos du châssis. `cam_cradle_bottom/top` restent dans `cad/` : ils ne
   servent qu'à une caméra sans tourillons. */

const gGuards = group('guards');
for (const a of ARM_DIR){
  const g = new THREE.Group(); g.rotation.z = a;
  const m = mesh(STLB64.guard, TPU, .1, .84);
  m.rotation.z = Math.PI/2;                        // le canal suit l'axe du bras
  m.position.set(46/1000, 0, (M.z.arm-1.6)/1000);
  g.add(m); gGuards.add(g);
}

const gPad = group('battpad');
{ const m = mesh(STLB64.battpad, TPU, .1, .86);
  m.position.set(0, 2/1000, (M.z.total)/1000); gPad.add(m); }

const gGrommet = group('grommet');
{ const m = mesh(STLB64.grommet, TPU, .1, .84);
  m.position.set(0, M.xt30_y/1000, (M.z.top-1.6)/1000); gGrommet.add(m); }

const gBumper = group('bumper');
{ const m = mesh(STLB64.bumper, TPU, .1, .86);
  m.position.set(0, -65/1000, (M.z.bottom-2.2)/1000); gBumper.add(m); }

/* pièces Sub250 d'origine */
/* Deux fichiers imprimables distincts : `flanc_gauche.stl` (la pièce Sub250
   telle quelle) et `flanc_droit.stl` (son miroir, généré par prep_sub250.py).
   Chacun est un GROUPE à part — donc sa propre ligne dans la liste des
   composants, avec son affichage et sa couleur.
   La face du flanc est dans le plan X-Z du fichier : la rotation de -90° autour
   de Z amène sa longueur d'avant en arrière. */
const SIDE_X = 13.0;
function poserFlanc(nom, b64, sx){
  const g = group(nom);
  const m = mesh(b64, SUB250, .06, .78);
  m.rotation.z = -Math.PI/2;
  m.position.set(sx*SIDE_X/1000, -6/1000, 0);
  g.add(m);
  return g;
}
const gFlancG = poserFlanc('flanc_g', STLB64.flanc_g, -1);
const gFlancD = poserFlanc('flanc_d', STLB64.flanc_d, +1);
const gFeet = group('feet');
for (const [i,[sx,sy]] of [[1,1],[-1,1],[-1,-1],[1,-1]].entries()){
  const g = new THREE.Group();
  g.rotation.z = ARM_DIR[i] - Math.PI/2;           // +Y local -> vers le bout du bras
  const m = mesh(STLB64.footpad, SUB250, .06, .8);
  m.position.z = (M.z.arm - 11.2)/1000;
  g.add(m);
  g.position.set(sx*M.mx/1000, sy*M.my/1000, 0);
  gFeet.add(g);
}
const gRxPlate = adjGroup('rxplate', 0, -52, M.z.total + 3);
addAt(gRxPlate, mesh(STLB64.rxplate, 0xd8dce2, .06, .7), 0, -52, M.z.total);
/* Étrier de queue Sub250 — réglable depuis le panneau « Réglages ».
   Orientation : 90° sur X **puis −90° sur Z**. C'est ce couple qui amène les
   deux alésages d'antenne côte à côte, axe vers l'arrière, comme sur la photo
   du châssis nu : le Y du fichier devient la gauche-droite du drone et son Z
   part vers l'arrière. Le seul 90° sur X les mettait l'un au-dessus de l'autre. */
const TAIL_Y = -44, TAIL_Z = 8;
const gTail = adjGroup('tailmount', 0, TAIL_Y, TAIL_Z);
gTail.rotation.set(90*D, 0, -90*D); gTail.userData.baseRot = gTail.rotation.clone();
addAt(gTail, mesh(STLB64.tailmount, SUB250, .06, .78), 0, TAIL_Y, TAIL_Z);
/* Alésages d'antenne **relevés dans le STL Sub250**, pas devinés : deux perçages
   Ø 3,0 mm, axe parallèle au Z du fichier, en (x = −4,2 ; y = ±10,7), profonds
   de 17,3 mm. C'est exactement le diamètre du fourreau d'une antenne DJI. */
const TAIL_BORE = { x: -4.2, y: 10.7, z0: 0.0, depth: 17.3 };

/* Moteurs XING2 1404 — le STEP du constructeur, converti par prep_vendor.py.
   Le fichier a l'arbre sur +Z, le plan de pose à z = −4,25 et la sortie de fils
   vers −Y. On plaque donc ce plan sur la face haute du bras (z = 5,5) et on
   fait tourner le moteur pour que les fils partent vers le centre du drone :
   une rotation de (angle du bras − 90°) amène le −Y du fichier sur l'axe du
   bras, pointe rentrante. */
const MOTOR_BASE = -4.25;                        // plan de pose dans le fichier
const MOTOR_Z = M.z.arm + M.z.arm_t - MOTOR_BASE;  // -> le plan tombe sur le bras
const MOTOR_BELL = 9.54;                         // haut de cloche dans le fichier
const gMotors = group('motors');
for (const [i,[sx,sy]] of [[1,1],[-1,1],[-1,-1],[1,-1]].entries()){
  const m = mesh(STLB64.motor, 0x2b2f36, .72, .34);
  m.rotation.z = ARM_DIR[i] - Math.PI/2;
  m.position.set(sx*M.mx/1000, sy*M.my/1000, MOTOR_Z/1000);
  gMotors.add(m);
}

/* hélices 3" : le STL 2,5" du TinyHoop remis à l'échelle */
const gProps = group('props');
const PROP_SCALE = M.prop_d/63.6;   // le STL est un 2,5\" de 63,6 mm
for (const [i,[sx,sy]] of [[1,1],[-1,1],[-1,-1],[1,-1]].entries()){
  // NE PAS recentrer sur la boîte englobante : le moyeu du STL est déjà en
  // (0,0) — une hélice tripale a une boîte naturellement décentrée.
  const m = mesh(STLB64.prop, 0xd8721e, .05, .35, {opacity:.55});
  m.scale.setScalar(.001*PROP_SCALE);
  if (i%2) m.scale.y *= -1;                        // CW / CCW
  // posée sur le haut de cloche, mesuré dans le STEP (z = 9,54 du fichier)
  m.position.set(sx*M.mx/1000, sy*M.my/1000, (MOTOR_Z + MOTOR_BELL + .3)/1000);
  gProps.add(m);
}

/* ─────────────────────────────── électronique : deux variantes */
function pcb(w,l,h,color){
  return new THREE.Mesh(new RoundedBoxGeometry(w/1000,l/1000,h/1000,3,.0008),
    new THREE.MeshStandardMaterial({color, metalness:.2, roughness:.55}));
}
const gElec = group('elec');
const ELEC = {};
{ // ── variante STOCK : RedFox A3 45A AIO + DJI O4 Pro
  const g = new THREE.Group();
  const fc = pcb(30,30,3.2, 0x0f1a2e); fc.position.set(0,M.stack_y/1000,(M.z.mid+5)/1000); g.add(fc);
  const rx = mesh(STLB64.rxpcb, 0x0f3d0f, .2, .5);
  rx.position.set(0,-30/1000,(M.z.mid+3)/1000); g.add(rx);
  ELEC.stock = g; gElec.add(g);
}
{ // ── variante STRATOS : carte TINYHOOP AIO + SX1262 + GPS
  const g = new THREE.Group();
  const fc = mesh(STLB64.board, 0x0b6b39, .15, .5);
  fc.position.set(0,M.stack_y/1000,(M.z.mid+4)/1000); g.add(fc);
  const lora = pcb(16,24,3.2, 0x14161b); lora.position.set(0,14/1000,(M.z.mid+11)/1000); g.add(lora);
  const gpsm = mesh(STLB64.gpsmount, TPU, .1, .84);
  gpsm.position.set(0, 30/1000, M.z.deck/1000); g.add(gpsm);
  const gps = mesh(STLB64.gps, 0x0a0c10, .2, .5);
  gps.position.set(0, 30/1000, (M.z.deck+8)/1000); g.add(gps);
  const rx = mesh(STLB64.rxpcb, 0x0f3d0f, .2, .5);
  rx.position.set(0,-30/1000,(M.z.mid+3)/1000); g.add(rx);
  ELEC.stratos = g; g.visible = false; gElec.add(g);
}
/* ─────────────────────────────── DJI O4 Pro — les STEP du constructeur
   Trois pièces converties par `../cad/prep_vendor.py`, avec leur repère propre :

     · `dji_air_unit` — 33,4 carré × 13,0, centré en X/Y, posé sur z = 0.
       Le connecteur de nappe sort en −Y et l'USB-C en −X.
     · `dji_camera`   — l'ORIGINE EST L'AXE DE BASCULE : les deux tourillons
       Ø 2,1 sont en (x = 0 ; y = ±10 ; z = 0). L'objectif regarde vers −X.
     · `dji_antenna`  — fourreau Ø 3,5, axe +Z, démarrant à z = 0.

   Deux rotations amènent la caméra dans le drone : −90° sur Z met l'objectif
   vers l'avant (+Y) et l'axe de bascule sur X ; puis CAM_TILT sur X la cabre.
   Dans l'ordre XYZ de Three.js, `rotation.set(tilt, 0, −90°)` fait exactement
   ça. La caméra est alors posée sur l'axe percé dans les joues (0 ; 55 ; 18). */
const AIR_Z = M.z.mid + 8;                         // au-dessus du stack de vol

const gO4air = group('o4air');
{ const m = mesh(STLB64.o4air, 0x1a1d22, .35, .42);
  m.rotation.z = Math.PI;                          // nappe vers l'avant, USB-C à droite
  m.position.set(0, M.stack_y/1000, AIR_Z/1000);
  gO4air.add(m); }

/* Groupe réglable dont le pivot EST l'axe de bascule : le curseur RX du panneau
   « Réglages » règle donc directement l'inclinaison de la caméra. */
const gO4cam = adjGroup('o4cam', 0, M.cage.y, M.cage.z);
{ const m = mesh(STLB64.o4cam, 0x1c1f24, .3, .45);
  m.rotation.set(M.cage.tilt*D, 0, -Math.PI/2);
  addAt(gO4cam, m, 0, M.cage.y, M.cage.z);
  /* Nappe caméra : le STEP la donne droite sur 148 mm, ce qui n'a aucun sens
     une fois montée. On la retrace pliée, de l'arrière de la caméra jusqu'au
     connecteur de l'air unit. Points en millimètres du drone. */
  const P = [[0, M.cage.y - 11.0, M.cage.z - 6.4],
             [0, M.cage.y - 19,   M.cage.z - 6.0],
             [0, 28,              AIR_Z + 2.0],
             [1.5, 15,            AIR_Z + 1.5]];
  const Q = gO4cam.userData.pivot;
  const rib = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(
      P.map(([x,y,z]) => new THREE.Vector3((x-Q[0])/1000, (y-Q[1])/1000, (z-Q[2])/1000))),
      24, .0016, 5),
    new THREE.MeshStandardMaterial({color:0x8a5a2b, metalness:.15, roughness:.6}));
  rib.scale.z = .55;                               // une nappe est plate
  gO4cam.add(rib); }

const gCap = group('cap');
{ const c = mesh(STLB64.cap, 0x1b3a8f, .25, .45);
  c.rotation.y = Math.PI/2; c.position.set(0,-26/1000,(M.z.deck+M.z.deck-M.z.mid+3.5)/1000); gCap.add(c); }

/* antennes */
/* Antennes VTX — ENFILÉES DANS LES ALÉSAGES du support de queue, et rattachées
   à lui : régler le support emmène les antennes avec, elles ne peuvent plus en
   sortir. Le STL DJI est un fourreau Ø 3,5 sur les 32 mm du haut et un corps de
   connecteur en bas ; on le recule de la profondeur du perçage pour que le
   fourreau remplisse l'alésage et que le connecteur reste **dans** le châssis,
   côté air unit — c'est le sens du câble sur le vrai drone.
   Le groupe reste réglable : ses curseurs font varier l'enfoncement. */
const gAntV = adjGroup('ant_vtx', 0, 0, 0);
gTail.add(gAntV);                                  // repère local du support
{ /* Le fourreau du STEP DJI, Ø 3,5 sur 85 mm, axe +Z : il tombe pile dans
     l'axe des alésages, aucune rotation à faire. Le connecteur MMCX a été
     coupé à la conversion — il n'est pas ici, il est sur l'air unit, à l'autre
     bout du coaxial tracé juste en dessous. */
  for (const sy of [1, -1])
    addAt(gAntV, mesh(STLB64.o4ant, 0x0f1114, .2, .5),
          TAIL_BORE.x, sy*TAIL_BORE.y, TAIL_BORE.z0);

  /* Coaxial : de l'air unit à l'entrée de l'alésage. La courbe se décrit en
     millimètres du DRONE, puis se convertit dans le repère du support — sinon
     régler le support la déformerait. Le support envoie X_fichier sur −Z,
     Y_fichier sur +X et Z_fichier sur −Y, d'où l'inverse ci-dessous. */
  const toTail = (x, y, z) => new THREE.Vector3(
    (TAIL_Z - z)/1000, x/1000, (TAIL_Y - y)/1000);
  for (const sy of [1, -1]){
    const co = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([
        toTail(sy*11, -17,   AIR_Z + 3),   // au ras de la face arrière de l'air unit
        toTail(sy*15, -24,   AIR_Z + 1),
        toTail(sy*14, -34,   TAIL_Z + 6),
        toTail(sy*TAIL_BORE.y, TAIL_Y, TAIL_Z - TAIL_BORE.x),
      ]), 22, .00085, 6),
      new THREE.MeshStandardMaterial({color:0x101216, metalness:.2, roughness:.55}));
    gAntV.add(co);
  }
}
/* Antennes RX — COUCHÉES dans les gorges de la platine Sub250. Construites en
   primitives plutôt que reprises du STL TinyHoop : celui-ci a 30 mm de coaxial
   entre le brin et le connecteur, ce qui envoyait le câble sous la batterie.
   Ici : le brin de 26 mm dans sa gorge, et un bout de coaxial qui part vers
   l'avant au ras de la platine — c'est tout ce qu'on voit sur le vrai drone. */
const RXP_TOP = M.z.total + 5.9;                  // face haute de la platine
const gAntR = adjGroup('ant_rx', 0, -52, RXP_TOP);
{ const matR = new THREE.MeshStandardMaterial({color:0x141414, metalness:.25, roughness:.5});
  for (const [dy, sx] of [[4, 1], [-4, -1]]){
    const el = new THREE.Mesh(new THREE.CylinderGeometry(.0016, .0016, .026, 12), matR);
    el.rotation.z = Math.PI/2;                     // le brin suit X
    addAt(gAntR, el, 0, -52 + dy, RXP_TOP + 1.6);
    // la courbe est décrite en millimètres du drone puis ramenée dans le repère
    // du groupe (pivot 0 ; −52 ; RXP_TOP) — sinon les curseurs la décaleraient deux fois
    const P = gAntR.userData.pivot;
    const at = (x, y, z) => new THREE.Vector3((x-P[0])/1000, (y-P[1])/1000, (z-P[2])/1000);
    const co = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([
        at(sx*13, -52 + dy, RXP_TOP + 1.6),
        at(sx*13, -45 + dy, RXP_TOP + 1.2),
        at(sx*11, -40 + dy, RXP_TOP - 1.0),
      ]), 14, .0011, 6), matR);
    gAntR.add(co);
  }
}

/* batterie 4S 660 mAh + faisceau XT30 */
const gBatt = group('battery');
{ const bw=30, bl=62, bh=26;
  const b = new THREE.Mesh(new RoundedBoxGeometry(bw/1000,bl/1000,bh/1000,5,.0022),
    new THREE.MeshStandardMaterial({color:0x14161b, metalness:.15, roughness:.62}));
  b.position.set(0,2/1000,(M.z.total+bh/2+3)/1000); gBatt.add(b);
  const y0=2-bl/2, z0=M.z.total+bh/2+3;
  for (const [col,dx] of [[0xc0392b,-3],[0x111214,3]]){
    const cv=[];
    for (let i=0;i<=16;i++){ const t=i/16;
      cv.push(new THREE.Vector3(dx/1000,
        (y0 - 3*Math.sin(t*Math.PI*0.9))/1000,
        (z0 - 4 - 18*t + 5*Math.sin(t*Math.PI))/1000)); }
    const w = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(cv),24,.0011,8),
      new THREE.MeshStandardMaterial({color:col, metalness:.1, roughness:.6}));
    gBatt.add(w);
  }
}

/* Câbles moteur : 3 fils de phase par moteur, passés dans le canal du
   protège-bras puis rabattus sous la plaque médiane jusqu'aux pads de l'ESC. */
const gWires = group('cables');
{ const PH = [0xc0392b, 0x111214, 0xe6e6e6];        // les 3 phases
  for (const [i,[sx,sy]] of [[1,1],[-1,1],[-1,-1],[1,-1]].entries()){
    const a = ARM_DIR[i], ca = Math.cos(a), sa = Math.sin(a);
    for (let k=0;k<3;k++){
      const off = (k-1)*1.15;                       // les 3 fils côte à côte
      const pts = [];
      const at = (r, z, lat) => new THREE.Vector3(
        (r*ca - lat*sa)/1000, (r*sa + lat*ca)/1000, z/1000);
      pts.push(at(72, M.z.arm + 2.0, off*0.6));                   // sortie du moteur
      pts.push(at(60, M.z.arm + 5.0, off));                       // remontée sur le bras
      pts.push(at(46, M.z.arm + 5.2, off));                       // dans le canal du guide
      pts.push(at(32, M.z.arm + 4.6, off));
      pts.push(at(22, M.z.mid  + 1.2, off*1.4));                  // passage sous la médiane
      pts.push(at(13, M.z.mid  + 3.0, off*1.8));                  // pads de l'ESC
      const w = new THREE.Mesh(
        new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 26, .00052, 6),
        new THREE.MeshStandardMaterial({color:PH[k], metalness:.1, roughness:.62}));
      gWires.add(w);
    }
  }
}

/* visserie */
const gScrews = group('screws');
/* Vis moteur : elles montent **par-dessous**, tête sous le bras, filet dans
   l'embase du moteur — le STL a la tête en haut, d'où le demi-tour sur X. */
for (const [sx,sy] of [[1,1],[-1,1],[-1,-1],[1,-1]]){
  for (const [hx,hy] of [[4.5,4.5],[-4.5,4.5],[-4.5,-4.5],[4.5,-4.5]]){
    const a = Math.atan2(sy*M.my, sx*M.mx);
    const x = sx*M.mx + hx*Math.cos(a) - hy*Math.sin(a);
    const y = sy*M.my + hx*Math.sin(a) + hy*Math.cos(a);
    const s = mesh(STLB64.screw, 0xd6d9de, .9, .25);
    s.rotation.x = Math.PI;
    s.position.set(x/1000, y/1000, M.z.arm/1000); gScrews.add(s);
  }
}
for (const [x,y] of M.standoffs.top.concat(M.standoffs.cam)){
  const s = mesh(STLB64.screw, 0xd6d9de, .9, .25);
  s.position.set(x/1000, y/1000, (M.z.total+.6)/1000); gScrews.add(s);
}

/* ─────────────────────────────── catalogue des pièces (liste + assemblage) */
const PARTS = [
  ['bottom',     'Plaque basse',        '×1 · carbone 2,5', 'Carbone', 0x1a1d21,
   "Elle porte les 4 bras et la fenêtre du stack. C'est la première pièce du montage."],
  ['arms',       'Bras',                '×4 · carbone 3,0', 'Carbone', 0x1a1d21,
   "Pris en sandwich entre la plaque basse et la médiane. Patin moteur M2 en 9×9, alésage Ø6,5."],
  ['mid',        'Plaque médiane',      '×1 · carbone 2,5', 'Carbone', 0x1a1d21,
   "Coiffe les bras et referme le sandwich. Elle porte le stack (20×20) et le perçage VTX 25,5."],
  ['deck',       'Pont étroit',         '×1 · carbone 2,5', 'Carbone', 0x1a1d21,
   "Le « splint » : il raidit le corps sur toute sa longueur et reçoit les entretoises."],
  ['cage',       'Flancs de cage caméra', '×2 · carbone 2,5', 'Carbone', 0x1a1d21,
   "Les deux joues qui tiennent la caméra. Écart intérieur 24,7 mm : c'est le berceau TPU qui rentre, pas la caméra nue."],
  ['standoffs',  'Entretoises',         '×6 · alu M3 20 mm', 'Visserie', 0xb9bec7,
   "20 mm posées sur le pont : le roof arrive pile à 32,5 mm, la hauteur du flanc Sub250."],
  ['top',        'Roof',                '×1 · carbone 2,0', 'Carbone', 0x1a1d21,
   "Plaque haute, fentes de sangle et découpe XT30 pour que le fil descende droit."],
  ['motors',     'Moteurs XING2 1404',  '×4 · 4500 KV',     'Motorisation', 0x2b2f36,
   "Le STEP constructeur, tel quel : Ø 19,9 × 18,6 mm, plan de pose à z = −4,25, entraxe M2 9×9. Vissés par-dessous, fils vers le centre. Vérifier qu'aucune vis ne touche le bobinage."],
  ['props',      'Hélices 3″',     '×4 · 76 mm',       'Motorisation', 0xd8721e,
   "Deux CW, deux CCW. Dégagement avant/arrière : 6,7 mm seulement — à monter droit."],
  ['o4cam',      'Caméra DJI O4 Pro',   '×1 · STEP DJI',    'Électronique', 0x1c1f24,
   "Le fichier constructeur, tel quel. Ses deux tourillons Ø 2,1 mm (y = ±10) basculent directement entre les joues carbone : 23,8 mm de large pour 24,7 d'écart. Le curseur RX du panneau « Réglages » change son inclinaison."],
  ['o4air',      'Air unit DJI O4 Pro', '×1 · STEP DJI',    'Électronique', 0x1a1d22,
   "Le fichier constructeur, tel quel. 33,5 mm de côté, 13,1 de haut, fixation 25,5 × 25,5 — exactement le perçage VTX du châssis. Nappe vers l'avant, USB-C sur le côté."],
  ['elec',       'Électronique',        'stack + RX',       'Électronique', 0x11532e,
   "Stock : RedFox A3 45A AIO. Stratos : carte TINYHOOP AIO + LoRa 868 + GPS. La caméra et l'air unit O4 Pro sont des composants à part, communs aux deux variantes."],
  ['cap',        'Condensateur',        '×1 · 35 V',        'Électronique', 0x1b3a8f,
   "Couché contre la médiane, jamais debout : il ne dépasse pas du châssis."],
  ['guards',     'Protège-bras',        '×4 · TPU',         'Imprimé', 0x24272d,
   "Clip sur le bras avec un canal pour les 3 fils de phase : les hélices ne peuvent plus les trancher."],
  ['battpad',    'Patin de batterie',   '×1 · TPU',         'Imprimé', 0x24272d,
   "Nervuré, collé sur le roof : la LiPo ne glisse plus en virage."],
  ['grommet',    'Passe-fil XT30',      '×1 · TPU',         'Imprimé', 0x24272d,
   "S'encliquette dans la découpe du roof et protège le fil du bord carbone."],
  ['bumper',     'Bumper arrière',      '×1 · TPU',         'Imprimé', 0x24272d,
   "Capuchon sur la pointe arrière — encaisse les atterrissages ratés."],
  ['flanc_g',    'Flanc gauche',        '×1 · Sub250',      'Sub250', 0x2ec4b6,
   "99 × 17,7 × 32,5 mm — la pièce Sub250 d'origine, telle quelle. Fichier : cad/stl/flanc_gauche.stl."],
  ['flanc_d',    'Flanc droit',         '×1 · Sub250',      'Sub250', 0x2ec4b6,
   "Le miroir du flanc gauche, dans son propre fichier imprimable : cad/stl/flanc_droit.stl (enroulement des triangles inversé pour garder les normales sortantes)."],
  ['feet',       'Patins de pied',      '×4 · Sub250',      'Sub250', 0x2ec4b6,
   "Pièce d'origine Sub250 : le fichier livré en contient 4 sur une planche."],
  ['rxplate',    'Platine antennes RX', '×1 · Sub250',      'Sub250', 0xd8dce2,
   "Pièce d'origine Sub250 : elle plaque les antennes du récepteur sur le roof."],
  ['tailmount',  'Support antenne queue', '×1 · Sub250',    'Sub250', 0x2ec4b6,
   "Pièce d'origine Sub250 : deux passages d'antenne à l'arrière."],
  ['gpsmount_x', 'Platine GPS',         '×1 · PLA',         'Imprimé', 0x24272d,
   "Uniquement sur la variante Stratos : surélève le GPS pour l'éloigner du VTX."],
  ['ant_vtx',    'Antennes VTX',        '×2 · DJI',         'Électronique', 0x0f1114,
   "Les deux fourreaux DJI, enfilés dans les alésages Ø 3 mm du support de queue — cotes relevées dans le STL Sub250, pas estimées. Rattachées au support : le régler les emmène avec."],
  ['ant_rx',     'Antennes RX',         'ELRS',             'Électronique', 0x141414,
   "Antennes du récepteur, à plat sur leur platine Sub250. Réglables elles aussi."],
  ['battery',    'Batterie 4S',         '660-720 mAh',      'Électronique', 0x14161b,
   "XT30, sanglée sur le roof. Le fil descend par la découpe, avec du mou."],
  ['cables',     'Câbles moteur',       '3 × 4 phases',     'Électronique', 0xc0392b,
   "Trois fils par moteur, passés dans le canal du protège-bras puis rabattus sous la médiane jusqu'aux pads de l'ESC."],
  ['screws',     'Visserie',            'M2 / M3',          'Visserie', 0xd6d9de,
   "16 vis moteur M2 + 6 vis d'entretoise M3. Frein-filet sur les moteurs."],
];
const PART = {}; PARTS.forEach(p => PART[p[0]] = p);

/* ─────────────────────────────── liste des composants */
const partsBox = document.getElementById('parts');
const rowOf = {};
for (const [k, nm, qt, cat, col, note] of PARTS){
  if (!G[k]) continue;
  const row = document.createElement('div'); row.className = 'prow'; row.dataset.k = k;
  const cb = document.createElement('input'); cb.type='checkbox'; cb.checked=true;
  const pk = document.createElement('input'); pk.type='color';
  pk.value = '#' + col.toString(16).padStart(6,'0');
  const nmEl = document.createElement('span'); nmEl.className='nm'; nmEl.textContent = nm;
  const qtEl = document.createElement('span'); qtEl.className='qt'; qtEl.textContent = qt;
  row.append(cb, nmEl, qtEl, pk);
  cb.onclick = e => { e.stopPropagation(); G[k].visible = cb.checked; };
  pk.oninput = e => { e.stopPropagation(); setColor(k, pk.value); };
  pk.onclick = e => e.stopPropagation();
  row.onclick = () => select(k);
  row.ondblclick = () => { if (ASM) ASM.seat(k); };
  partsBox.appendChild(row); rowOf[k] = row;
}
function setColor(k, hex){
  const col = new THREE.Color(hex);
  G[k].traverse(o => { if (o.isMesh && !o.userData.keepColor) o.material.color.copy(col); });
}

/* surbrillance : un clic sélectionne, un clic dans le vide désélectionne */
let selected = null;
const EMIS = 0x2f6fed;
function select(k){
  if (selected && G[selected]) G[selected].traverse(o => {
    if (o.isMesh) o.material.emissive && o.material.emissive.setHex(0x000000); });
  Object.values(rowOf).forEach(r => r.classList.remove('sel'));
  if (k === selected || k == null){ selected = null; hud(''); return; }
  selected = k;
  G[k].traverse(o => { if (o.isMesh && o.material.emissive) o.material.emissive.setHex(EMIS); });
  if (rowOf[k]) rowOf[k].classList.add('sel');
  const p = PART[k];
  hud('<b>' + p[1] + '</b> · ' + p[2] + '<br>' + p[5]);
}
renderer.domElement.addEventListener('pointerdown', e => {
  const r = renderer.domElement.getBoundingClientRect();
  const ndc = new THREE.Vector2(((e.clientX-r.left)/r.width)*2-1,
                                -((e.clientY-r.top)/r.height)*2+1);
  const ray = new THREE.Raycaster(); ray.setFromCamera(ndc, camera);
  const hit = ray.intersectObject(frameRoot, true)[0];
  if (!hit){ select(null); return; }
  let o = hit.object, k = null;
  while (o && o !== frameRoot){ const f = Object.keys(G).find(n => G[n] === o); if (f){ k = f; break; } o = o.parent; }
  if (k) select(k);
});
const hudEl = document.getElementById('hud');
function hud(html){ hudEl.innerHTML = html || defaultHud(); }
function defaultHud(){
  return BUILD ? 'Clic = surligner · double-clic dans la liste = emboîter'
               : 'Entraxe 150 mm · 3″ · hauteur 32,5 mm';
}
hud('');

/* ─────────────────────────────── sélecteur d'électronique */
const elecSel = document.getElementById('elecSel');
const ELEC_NOTE = {
  stock: "Le kit tel qu'il se vend : RedFox A3 45A AIO (F722 · ICM42688-P · BLHeli32) et DJI O4 Pro. Vole sous Betaflight.",
  stratos: "Le châssis OasisFly30 avec le cerveau Stratos : carte TINYHOOP AIO, lien LoRa 868 pour le PC et l'essaim, GPS à l'avant. Firmware du dépôt — jamais volé à ce jour.",
};
function setElec(v){
  ELEC.stock.visible = (v === 'stock');
  ELEC.stratos.visible = (v === 'stratos');
  document.getElementById('elecNote').textContent = ELEC_NOTE[v];
}
elecSel.onchange = () => setElec(elecSel.value);
setElec('stock');

/* ─────────────────────────────── vue éclatée */
const EXPLODE = {
  bottom:[0,0,0], arms:[0,0,-14], mid:[0,0,26], deck:[0,0,38], top:[0,0,74],
  standoffs:[0,0,50], cage:[0,0,58], o4cam:[0,0,66], o4air:[0,0,30], motors:[0,0,-28],
  props:[0,0,96], elec:[0,0,18], cap:[0,0,10], guards:[0,0,-40],
  battpad:[0,0,88], grommet:[0,0,82], bumper:[0,0,-20],
  flanc_g:[-30,0,-8], flanc_d:[30,0,-8],
  feet:[0,0,-46], rxplate:[0,0,92], tailmount:[0,0,30],
  battery:[0,0,112], screws:[0,0,60], cables:[0,0,-34],
  // ant_vtx est un enfant du support de queue : son décalage est donné dans le
  // repère du support, donc +Z le sort des alésages au lieu de le monter.
  ant_vtx:[0,0,40], ant_rx:[0,0,104],
};
Object.keys(G).forEach(k => { G[k].userData.home = G[k].position.clone(); });
const expSlider = document.getElementById('explode');
expSlider.oninput = () => {
  const t = expSlider.value/100;
  for (const k in G){
    if (ASM && ASM.active) break;
    const e = EXPLODE[k] || [0,0,0], h = G[k].userData.home;
    G[k].position.set(h.x + e[0]*t/1000, h.y + e[1]*t/1000, h.z + e[2]*t/1000);
  }
};

/* ─────────────────────────────── réglages fins (position / rotation)
   Les pièces dont le calage reste incertain — cage caméra, berceau, étrier de
   queue, platine RX, antennes — sont des groupes RÉGLABLES : leur origine est
   posée sur la pièce, donc les curseurs de rotation la font pivoter sur place.
   Le bloc de valeurs en bas est sélectionnable et copiable : c'est ce qu'on
   recopie dans `tune.py` / ce générateur une fois le bon réglage trouvé, au
   lieu de deviner une orientation à l'aveugle. */
const ADJ_KEYS = Object.keys(G).filter(k => G[k].userData.pivot);
const ADJ_AX = [['x','X',-60,60,.5,'mm'], ['y','Y',-60,60,.5,'mm'], ['z','Z',-40,60,.5,'mm'],
                ['rx','RX',-180,180,1,'°'], ['ry','RY',-180,180,1,'°'], ['rz','RZ',-180,180,1,'°']];
{
  const sel = document.getElementById('adjSel');
  const rows = document.getElementById('adjRows');
  const out = document.getElementById('adjOut');
  const inp = {}, lab = {};

  for (const k of ADJ_KEYS){
    G[k].userData.adj = {x:0, y:0, z:0, rx:0, ry:0, rz:0};
    const o = document.createElement('option');
    o.value = k; o.textContent = PART[k] ? PART[k][1] : k;
    sel.appendChild(o);
  }
  for (const [key, nm, lo, hi, step] of ADJ_AX){
    const row = document.createElement('div'); row.className = 'adjrow';
    const s = document.createElement('span'); s.textContent = nm;
    const r = document.createElement('input');
    r.type = 'range'; r.min = lo; r.max = hi; r.step = step; r.value = 0;
    const b = document.createElement('b'); b.textContent = '0';
    row.append(s, r, b); rows.appendChild(row);
    inp[key] = r; lab[key] = b;
    r.oninput = apply;
  }

  function apply(){
    const g = G[sel.value], a = g.userData.adj;
    for (const [key,,,,, unit] of ADJ_AX){
      a[key] = +inp[key].value;
      lab[key].textContent = a[key] + (unit === 'mm' ? '' : '°');
    }
    const base = g.userData.base, br = g.userData.baseRot;
    g.position.set(base.x + a.x/1000, base.y + a.y/1000, base.z + a.z/1000);
    g.rotation.set(br.x + a.rx*D, br.y + a.ry*D, br.z + a.rz*D);
    g.userData.home = g.position.clone();   // l'éclatée repart de la nouvelle place
    readout();
  }
  function load(){
    const a = G[sel.value].userData.adj;
    for (const [key,,,,, unit] of ADJ_AX){
      inp[key].value = a[key];
      lab[key].textContent = a[key] + (unit === 'mm' ? '' : '°');
    }
  }
  function readout(){
    const lines = ADJ_KEYS
      .filter(k => ADJ_AX.some(([q]) => G[k].userData.adj[q]))
      .map(k => { const a = G[k].userData.adj;
        return k + ' : xyz ' + a.x + ' ' + a.y + ' ' + a.z +
               ' mm · rot ' + a.rx + ' ' + a.ry + ' ' + a.rz + '°'; });
    out.textContent = lines.length ? lines.join('\n')
      : "Rien de réglé. Bouge un curseur, puis « Copier les valeurs » — c'est cette ligne qui sert à figer la position dans le code.";
  }
  sel.onchange = load;
  document.getElementById('adjReset').onclick = () => {
    const a = G[sel.value].userData.adj;
    for (const [key] of ADJ_AX) a[key] = 0;
    load(); apply();
  };
  document.getElementById('adjCopy').onclick = e => {
    const txt = out.textContent;
    const done = () => { e.target.textContent = 'Copié ✓';
      setTimeout(() => e.target.textContent = 'Copier les valeurs', 1400); };
    if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done, () => {});
    const r = document.createRange(); r.selectNodeContents(out);
    const s = getSelection(); s.removeAllRanges(); s.addRange(r);
  };
  sel.value = ADJ_KEYS[0]; load(); readout();
}

/* ─────────────────────────────── vues, fil de fer, thème, plein écran */
function look(dx,dy,dz,d){
  controls.target.set(0, 0, M.z.total/2000 + M.ground/1000);
  camera.position.set(dx*d, dy*d, dz*d + controls.target.z);
  controls.update();
}
look(.62,-.72,.42, BUILD ? .60 : .34);
document.getElementById('vIso').onclick   = () => look(.62,-.72,.42, BUILD ? .60 : .34);
document.getElementById('vTop').onclick   = () => look(0,-.001,1,.30);
document.getElementById('vSide').onclick  = () => look(1,0,.06,.30);
document.getElementById('vFront').onclick = () => look(0,-1,.06,.30);
let wire = false;
document.getElementById('wire').onclick = e => {
  wire = !wire; e.target.textContent = wire ? 'Rendu plein' : 'Fil de fer';
  frameRoot.traverse(o => { if (o.isMesh) o.material.wireframe = wire; });
};
document.getElementById('theme').onclick = e => {
  const light = document.body.classList.toggle('light');
  e.target.textContent = light ? 'Thème sombre' : 'Thème clair';
  scene.background = new THREE.Color(light ? 0xeef1f5 : 0x0b0e14);
  makeGrid(light);
};
const fsBtn = document.getElementById('fs');
fsBtn.onclick = () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else document.documentElement.requestFullscreen();
};
addEventListener('keydown', e => { if (e.key === 'f' || e.key === 'F') fsBtn.click(); });

/* ─────────────────────────────── modes */
document.querySelectorAll('#modes .mode').forEach(el => {
  el.classList.toggle('on', (el.dataset.mode === 'build') === BUILD);
  el.onclick = () => {
    const want = el.dataset.mode === 'build';
    if (want === BUILD) return;
    const u = new URL(location.href);
    if (__BUILD_DEFAULT__){ if (want) u.searchParams.delete('nobuild'); else u.searchParams.set('nobuild','1'); }
    else { if (want) u.searchParams.set('build','1'); else u.searchParams.delete('build'); }
    location.href = u.toString();
  };
});

/* ─────────────────────────────── fiche technique */
{ const t = document.getElementById('specs');
  for (const [k,v] of M.specs){
    const tr = document.createElement('tr');
    tr.innerHTML = '<td>'+k+'</td><td>'+v+'</td>'; t.appendChild(tr);
  } }

/* ─────────────────────────────── simulateur d'assemblage */
const ASM = (function(){
  if (!BUILD) return null;
  const order = PARTS.map(p => p[0]).filter(k => G[k]);
  const ghosts = [];
  let seated = new Set(), showGhost = true, active = true;

  function spot(i, n){                       // les pièces attendent en cercle
    const a = (i/n)*Math.PI*2, r = .26;
    return new THREE.Vector3(Math.cos(a)*r, Math.sin(a)*r, .03);
  }
  function tidySpot(i){                      // rangées par catégorie
    const cats = [...new Set(PARTS.map(p => p[3]))];
    const p = PART[order[i]], c = cats.indexOf(p[3]);
    const idx = order.filter(k => PART[k][3] === p[3]).indexOf(order[i]);
    return new THREE.Vector3(-.20 + idx*.055, .22 - c*.07, .02);
  }
  function makeGhosts(){
    for (const k of order){
      const g = G[k].clone(true);
      g.traverse(o => { if (o.isMesh){
        o.material = new THREE.MeshBasicMaterial({color:0x2f6fed, transparent:true,
          opacity:.085, depthWrite:false}); } });
      g.position.copy(G[k].userData.home); g.visible = true;
      // dans le repère du PARENT de la pièce — ant_vtx vit dans celui du support
      (G[k].parent || frameRoot).add(g); ghosts.push([k,g]);
    }
  }
  function refreshGhosts(){
    ghosts.forEach(([k,g]) => g.visible = showGhost && !seated.has(k));
  }
  function seat(k){
    if (!G[k]) return;
    G[k].position.copy(G[k].userData.home);
    seated.add(k); rowOf[k] && rowOf[k].classList.add('done');
    refreshGhosts(); progress();
  }
  function scatter(){
    seated.clear();
    order.forEach((k,i) => { G[k].position.copy(spot(i, order.length));
      rowOf[k] && rowOf[k].classList.remove('done'); });
    refreshGhosts(); progress();
  }
  function tidy(){
    seated.clear();
    order.forEach((k,i) => { G[k].position.copy(tidySpot(i));
      rowOf[k] && rowOf[k].classList.remove('done'); });
    refreshGhosts(); progress();
  }
  function all(){ order.forEach(seat); }
  function progress(){
    document.getElementById('asmNote').innerHTML =
      '<b>' + seated.size + ' / ' + order.length + '</b> pièces posées · ' +
      'un clic surligne, un double-clic emboîte.';
  }
  makeGhosts(); scatter();
  document.getElementById('asmAll').onclick = all;
  document.getElementById('asmScatter').onclick = scatter;
  document.getElementById('asmTidy').onclick = tidy;
  document.getElementById('asmGhost').onclick = e => {
    showGhost = !showGhost; e.target.textContent = 'Fantômes : ' + (showGhost?'oui':'non');
    refreshGhosts();
  };
  return { seat, scatter, all, get active(){ return active; } };
})();

/* ─────────────────────────────── boucle */
function resize(){
  const w = view.clientWidth, h = view.clientHeight;
  renderer.setSize(w, h);        // met aussi à jour la taille CSS du canvas
  camera.aspect = w/h; camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();
(function loop(){ requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();
try { window.__ready = true; } catch(_){}
</script>
</body>
</html>
"""


def main():
    html = (TEMPLATE
            .replace("__IMPORTMAP__", importmap())
            .replace("__MODEL__", json.dumps(MODEL, separators=(",", ":")))
            .replace("__STLS__", json.dumps(stls(), separators=(",", ":")))
            .replace("__SUB__", MODEL["sub"]))
    with open(OUT, "w") as f:
        f.write(html.replace("__BUILD_DEFAULT__", "false"))
    print("écrit %s  (%.1f Mo)" % (os.path.relpath(OUT, REPO), os.path.getsize(OUT)/1e6))

    bdir = os.path.join(OASIS, "build")
    os.makedirs(bdir, exist_ok=True)
    bout = os.path.join(bdir, "build.html")
    with open(bout, "w") as f:
        f.write(html.replace("__BUILD_DEFAULT__", "true"))
    print("écrit %s  (%.1f Mo)" % (os.path.relpath(bout, REPO), os.path.getsize(bout)/1e6))


if __name__ == "__main__":
    main()
