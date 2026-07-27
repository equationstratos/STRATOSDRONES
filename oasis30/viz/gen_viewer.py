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
    z=dict(bottom=T.Z_BOTTOM, arm=T.Z_ARM, mid=T.Z_MID, deck=T.Z_DECK,
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
        "cradle_b": o("cam_cradle_bottom"), "cradle_t": o("cam_cradle_top"),
        "guard": o("arm_guard"), "battpad": o("batt_pad"),
        "grommet": o("xt30_grommet"), "gpsmount": o("gps_mount"),
        "bumper": o("rear_bumper"),
        # ── pièces Sub250 d'origine, telles quelles
        "side_a": o("sub250_side_panel_a"), "side_b": o("sub250_side_panel_b"),
        "footpad": o("sub250_foot_pad"),
        "rxplate": o("sub250_rx_plate"), "tailmount": o("sub250_tail_mount"),
        # ── pièces réutilisées du TinyHoop MK1 (mêmes composants du commerce)
        "prop": t("prop"), "screw": t("screw"), "cap": t("capacitor"),
        "gps": t("gps_module"), "rxpcb": t("rx_pcb"), "rxant": t("rx_antenna"),
        "vtxant": t("dji_pro_ant"), "board": t("board"),
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
const gCage = group('cage');
for (const sx of [1,-1]){
  const m = carbonMesh(STLB64.cage, CARBON);
  m.scale.x = sx*.001;
  gCage.add(m);
}

/* entretoises */
const gStand = group('standoffs');
for (const [x,y] of M.standoffs.top.concat(M.standoffs.cam)){
  const m = mesh(STLB64.standoff, ALU, .85, .28);
  m.position.set(x/1000, y/1000, M.z.standoff/1000);
  gStand.add(m);
}

/* pièces imprimées Stratos */
const gCradle = group('cradle');
{ const cy = M.cage.y - 6;                          // reste dans la cage (nez à y=65)
  const b = mesh(STLB64.cradle_b, TPU, .1, .82);
  b.position.set(0, cy/1000, (M.z.deck+2.5)/1000); gCradle.add(b);   // posé SUR le pont
  const t = mesh(STLB64.cradle_t, TPU, .1, .82);
  t.position.set(0, cy/1000, (M.z.deck+15.5)/1000); gCradle.add(t); }

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
/* Le fichier Sub250 « side panels » contient DEUX pièces distinctes posées
   côte à côte sur une planche d'impression : la coque (72 × 17,7 × 32,5) et la
   grille (43 × 9,3 × 10,8). Elles vont **une de chaque côté** — la coque à
   gauche, la grille à droite — et pas les deux de chaque côté.
   Chaque pièce est un mur dont la face est en X-Z dans le fichier : la rotation
   de -90° autour de Z amène sa longueur d'avant en arrière et son épaisseur
   en travers, avec la concavité tournée vers le châssis. */
const gSide = group('sidepanels');
{ const SIDE_X = 13.0;
  const coque = new THREE.Group();                 // ── côté GAUCHE
  { const m = mesh(STLB64.side_a, SUB250, .06, .78);
    m.rotation.z = -Math.PI/2;
    coque.add(m); }
  coque.scale.x = -1;                              // concavité vers l'intérieur
  coque.position.set(-SIDE_X/1000, -6/1000, 0);
  gSide.add(coque);

  const grille = new THREE.Group();                // ── côté DROIT
  { const m = mesh(STLB64.side_b, SUB250, .06, .78);
    m.rotation.z = -Math.PI/2;
    grille.add(m); }
  grille.position.set(SIDE_X/1000, -6/1000, 19/1000);
  gSide.add(grille);
}
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
const gRxPlate = group('rxplate');
{ const m = mesh(STLB64.rxplate, 0xd8dce2, .06, .7);
  m.position.set(0, -52/1000, M.z.total/1000); gRxPlate.add(m); }
/* Étrier de queue : ses deux oreilles enjambent l'empilage de plaques et ses
   deux tubes d'antenne pointent vers l'arrière. Dans son repère d'origine
   l'axe des tubes est +Z ; on le bascule de 90° pour l'envoyer vers -Y. */
const TAIL_Y = -58, TAIL_Z = M.z.mid + 2;
const gTail = group('tailmount');
{ const m = mesh(STLB64.tailmount, SUB250, .06, .78);
  m.rotation.x = Math.PI/2;                        // +Z local -> -Y (vers l'arrière)
  m.position.set(0, TAIL_Y/1000, TAIL_Z/1000);
  gTail.add(m); }

/* moteurs 1404 — construits en primitives (légers, cotes exactes) */
// Moteur 1404 : embase de fixation, stator bobiné apparent, cloche ventilée,
// chapeau et écrou d'hélice. Cotes réelles d'un 1404 (cloche Ø15,8, H ~17,5).
function motor(){
  const g = new THREE.Group();
  const mat = (c,m,r) => new THREE.MeshStandardMaterial({color:c, metalness:m, roughness:r});
  const cyl = (rt,rb,h,seg,material,z) => { const m = new THREE.Mesh(
      new THREE.CylinderGeometry(rt,rb,h,seg), material);
    m.rotation.x = Math.PI/2; m.position.z = z; g.add(m); return m; };
  cyl(.0058,.0063,.0016, 24, mat(0x24272c,.85,.38), .0008);          // embase
  for (let i=0;i<4;i++){                                              // 4 bossages M2
    const a = i/4*Math.PI*2 + Math.PI/4;
    const b = new THREE.Mesh(new THREE.CylinderGeometry(.0016,.0016,.0016,10),
      mat(0x24272c,.85,.38));
    b.rotation.x = Math.PI/2;
    b.position.set(Math.cos(a)*.0064, Math.sin(a)*.0064, .0008); g.add(b);
  }
  cyl(.0068,.0068,.0044, 24, mat(0x8a6a2f,.65,.52), .0038);           // stator bobiné
  cyl(.0079,.0074,.0074, 30, mat(0x3d4249,.92,.24), .0097);           // cloche
  for (let i=0;i<9;i++){                                              // ouïes de cloche
    const a = i/9*Math.PI*2;
    const v = new THREE.Mesh(new THREE.BoxGeometry(.0013,.0034,.0022), mat(0x101318,.3,.7));
    v.position.set(Math.cos(a)*.0074, Math.sin(a)*.0074, .0104);
    v.rotation.z = a; g.add(v);
  }
  cyl(.0079,.0079,.0011, 30, mat(0x3d4249,.92,.24), .0139);           // chapeau
  cyl(.0026,.0026,.0026,  6, mat(0xc9a227,.95,.2),  .0158);           // écrou d'hélice
  cyl(.0008,.0008,.0040, 12, mat(0xd6d9de,.95,.16), .0165);           // axe
  return g;
}
const gMotors = group('motors');
for (const [sx,sy] of [[1,1],[-1,1],[-1,-1],[1,-1]]){
  const m = motor(); m.position.set(sx*M.mx/1000, sy*M.my/1000, (M.z.arm+3)/1000);
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
  m.position.set(sx*M.mx/1000, sy*M.my/1000, (M.z.arm+18.5)/1000);   // sur le chapeau
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
  const air = pcb(30,24,7.5, 0x11532e); air.position.set(0,(M.stack_y+16)/1000,(M.z.mid+13)/1000); g.add(air);
  const cam = pcb(M.cage.w,20,M.cage.h, 0x1c1f24);
  cam.position.set(0, (M.cage.y-6)/1000, (M.z.deck+11)/1000);
  cam.rotation.x = -M.cage.tilt*D; g.add(cam);
  const lens = new THREE.Mesh(new THREE.CylinderGeometry(.0058,.0062,.008,24),
    new THREE.MeshStandardMaterial({color:0x0a0b0d, metalness:.5, roughness:.18}));
  lens.rotation.x = Math.PI/2 - M.cage.tilt*D;
  lens.position.set(0, (M.cage.y+3)/1000, (M.z.deck+14)/1000); g.add(lens);
  const rx = mesh(STLB64.rxpcb, 0x0f3d0f, .2, .5);
  rx.position.set(0,-38/1000,(M.z.mid+3)/1000); g.add(rx);
  ELEC.stock = g; gElec.add(g);
}
{ // ── variante STRATOS : carte TINYHOOP AIO + SX1262 + GPS
  const g = new THREE.Group();
  const fc = mesh(STLB64.board, 0x0b6b39, .15, .5);
  fc.position.set(0,M.stack_y/1000,(M.z.mid+4)/1000); g.add(fc);
  const lora = pcb(16,24,3.2, 0x14161b); lora.position.set(0,14/1000,(M.z.mid+11)/1000); g.add(lora);
  const air = pcb(30,24,7.5, 0x11532e); air.position.set(0,(M.stack_y+16)/1000,(M.z.mid+18)/1000); g.add(air);
  const cam = pcb(M.cage.w,20,M.cage.h, 0x1c1f24);
  cam.position.set(0, (M.cage.y-6)/1000, (M.z.deck+11)/1000);
  cam.rotation.x = -M.cage.tilt*D; g.add(cam);
  const gpsm = mesh(STLB64.gpsmount, TPU, .1, .84);
  gpsm.position.set(0, 30/1000, M.z.deck/1000); g.add(gpsm);
  const gps = mesh(STLB64.gps, 0x0a0c10, .2, .5);
  gps.position.set(0, 30/1000, (M.z.deck+8)/1000); g.add(gps);
  const rx = mesh(STLB64.rxpcb, 0x0f3d0f, .2, .5);
  rx.position.set(0,-38/1000,(M.z.mid+3)/1000); g.add(rx);
  ELEC.stratos = g; g.visible = false; gElec.add(g);
}
const gCap = group('cap');
{ const c = mesh(STLB64.cap, 0x1b3a8f, .25, .45);
  c.rotation.y = Math.PI/2; c.position.set(0,-26/1000,(M.z.deck+M.z.deck-M.z.mid+3.5)/1000); gCap.add(c); }

/* antennes */
const gAnt = group('antennes');
{ /* L'antenne VTX s'engage dans le tube HAUT de l'étrier de queue et sort vers
     l'arrière, légèrement relevée — elle ne traverse plus le roof. */
  const v = mesh(STLB64.vtxant, 0x0f1114, .2, .5);
  v.rotation.x = 50*D;                             // engagée dans le tube, vers l'arrière ET vers le haut
  v.position.set(0, (TAIL_Y - 13)/1000, (TAIL_Z + 8)/1000);
  gAnt.add(v);
  /* Antennes RX : à plat sous leur platine Sub250, sur le roof. */
  const r = mesh(STLB64.rxant, 0x141414, .25, .5);
  r.position.set(0, -52/1000, (M.z.total+4.5)/1000);
  gAnt.add(r); }

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
for (const [sx,sy] of [[1,1],[-1,1],[-1,-1],[1,-1]]){
  for (const [hx,hy] of [[4.5,4.5],[-4.5,4.5],[-4.5,-4.5],[4.5,-4.5]]){
    const a = Math.atan2(sy*M.my, sx*M.mx);
    const x = sx*M.mx + hx*Math.cos(a) - hy*Math.sin(a);
    const y = sy*M.my + hx*Math.sin(a) + hy*Math.cos(a);
    const s = mesh(STLB64.screw, 0xd6d9de, .9, .25);
    s.position.set(x/1000, y/1000, (M.z.arm+3.2)/1000); gScrews.add(s);
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
  ['motors',     'Moteurs 1404',        '×4 · 4500 KV',     'Motorisation', 0x3a3f47,
   "Vissés par-dessous en M2. Vérifier qu'aucune vis ne touche le bobinage."],
  ['props',      'Hélices 3″',     '×4 · 76 mm',       'Motorisation', 0xd8721e,
   "Deux CW, deux CCW. Dégagement avant/arrière : 6,7 mm seulement — à monter droit."],
  ['elec',       'Électronique',        'stack + caméra',   'Électronique', 0x11532e,
   "Stock : RedFox A3 45A AIO + DJI O4 Pro. Stratos : carte TINYHOOP AIO + LoRa 868 + GPS."],
  ['cap',        'Condensateur',        '×1 · 35 V',        'Électronique', 0x1b3a8f,
   "Couché contre la médiane, jamais debout : il ne dépasse pas du châssis."],
  ['cradle',     'Berceau caméra',      '×2 · TPU',         'Imprimé', 0x24272d,
   "Deux coquilles qui enserrent la caméra à 30°. Pièce Stratos — absente du kit Sub250."],
  ['guards',     'Protège-bras',        '×4 · TPU',         'Imprimé', 0x24272d,
   "Clip sur le bras avec un canal pour les 3 fils de phase : les hélices ne peuvent plus les trancher."],
  ['battpad',    'Patin de batterie',   '×1 · TPU',         'Imprimé', 0x24272d,
   "Nervuré, collé sur le roof : la LiPo ne glisse plus en virage."],
  ['grommet',    'Passe-fil XT30',      '×1 · TPU',         'Imprimé', 0x24272d,
   "S'encliquette dans la découpe du roof et protège le fil du bord carbone."],
  ['bumper',     'Bumper arrière',      '×1 · TPU',         'Imprimé', 0x24272d,
   "Capuchon sur la pointe arrière — encaisse les atterrissages ratés."],
  ['sidepanels', 'Flancs latéraux',     '×2 · Sub250',      'Sub250', 0x2ec4b6,
   "Pièce d'origine Sub250, reprise telle quelle. 99 × 17,7 × 32,5 mm."],
  ['feet',       'Patins de pied',      '×4 · Sub250',      'Sub250', 0x2ec4b6,
   "Pièce d'origine Sub250 : le fichier livré en contient 4 sur une planche."],
  ['rxplate',    'Platine antennes RX', '×1 · Sub250',      'Sub250', 0xd8dce2,
   "Pièce d'origine Sub250 : elle plaque les antennes du récepteur sur le roof."],
  ['tailmount',  'Support antenne queue', '×1 · Sub250',    'Sub250', 0x2ec4b6,
   "Pièce d'origine Sub250 : deux passages d'antenne à l'arrière."],
  ['gpsmount_x', 'Platine GPS',         '×1 · PLA',         'Imprimé', 0x24272d,
   "Uniquement sur la variante Stratos : surélève le GPS pour l'éloigner du VTX."],
  ['antennes',   'Antennes',            'VTX + RX',         'Électronique', 0x0f1114,
   "Antenne VTX inclinée dans le support de queue, antennes RX à plat sous leur platine."],
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
  standoffs:[0,0,50], cage:[0,0,58], cradle:[0,0,66], motors:[0,0,-28],
  props:[0,0,96], elec:[0,0,18], cap:[0,0,10], guards:[0,0,-40],
  battpad:[0,0,88], grommet:[0,0,82], bumper:[0,0,-20], sidepanels:[0,0,-8],
  feet:[0,0,-46], rxplate:[0,0,92], tailmount:[0,0,30], antennes:[0,0,100],
  battery:[0,0,112], screws:[0,0,60], cables:[0,0,-34],
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
      frameRoot.add(g); ghosts.push([k,g]);
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
