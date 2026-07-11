#!/usr/bin/env python3
"""Fr4n7-F — mechanisms viewer generator (all printable deploy mechanisms).

One self-contained ``mechanisms_viewer.html``: the seven candidate mechanisms
(worm+crank [★ RETAINED as the V2 drive], scissor, iris cam, rack+pinion,
eccentric cam lever, toggle over-centre, wiper) rendered from their real STLs
(``foldable/cad/stl/mech/p_*.stl``) and ANIMATED with their actual 2-D
kinematics — inspect and compare before printing. Same offline recipe as
the other viewers (Three.js inlined from ``sim/viz/vendor``).

    python3 foldable/viz/gen_mech_viewer.py   # -> foldable/viz/mechanisms_viewer.html
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
VENDOR = os.path.join(REPO, "sim", "viz", "vendor")
STL = os.path.join(REPO, "foldable", "cad", "stl", "mech")
OUT = os.path.join(HERE, "mechanisms_viewer.html")

PARTS = ["p_wc_base","p_wc_worm","p_wc_sector","p_wc_slider",
         "p_sc_base","p_sc_arm","p_sc_link","p_sc_slider",
         "p_ir_base","p_ir_disc","p_ir_pin",
         "p_rp_base","p_rp_pinion","p_rp_rack",
         "p_cl_base","p_cl_cam","p_cl_follower",
         "p_tg_base","p_tg_handle","p_tg_link","p_tg_pad",
         "p_wp_base","p_wp_gs","p_wp_gb","p_wp_rod","p_wp_arm"]
DRONE_STL = os.path.join(REPO, "foldable", "cad", "stl")
DRONE_PARTS = ["body", "arm_fr", "arm_fl", "arm_rr", "arm_rl", "latch", "button"]


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
<title>Fr4n7-F — mécanismes de déploiement (avant impression)</title>
<style>
  :root{--bg:#0b0e14;--panel:#12161d;--line:#262d38;--ink:#e6edf3;--mut:#8b949e;
        --acc:#2f6fed;--acc2:#63a4ff;}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;font:13px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
            background:var(--bg);color:var(--ink);overflow:hidden}
  #app{display:flex;height:100%}
  #side{width:320px;flex:none;background:var(--panel);border-right:1px solid var(--line);
        display:flex;flex-direction:column;overflow-y:auto}
  #view{flex:1;position:relative}
  canvas{display:block}
  header{padding:14px 16px;border-bottom:1px solid var(--line)}
  header h1{margin:0;font-size:15px}
  header h1 b{color:var(--acc)}
  header p{margin:3px 0 0;color:var(--mut);font-size:11px}
  .sec{padding:12px 16px;border-bottom:1px solid var(--line)}
  .sec h2{margin:0 0 9px;font-size:11px;text-transform:uppercase;letter-spacing:.6px;
          color:var(--mut);font-weight:600}
  .btns{display:grid;grid-template-columns:1fr 1fr;gap:6px}
  button{background:#1b212b;color:var(--ink);border:1px solid var(--line);border-radius:6px;
         padding:7px 8px;font-size:12px;cursor:pointer;transition:.12s;text-align:left}
  button:hover{background:#262d38;border-color:#3a4250}
  button.on{background:var(--acc);border-color:var(--acc);color:#fff}
  button.big{font-weight:600;text-align:center}
  input[type=range]{width:100%;accent-color:var(--acc)}
  .val{color:var(--acc);font-variant-numeric:tabular-nums}
  #desc h3{margin:0 0 6px;font-size:13px;color:var(--acc2)}
  #desc p{margin:0 0 8px;color:var(--mut);font-size:12px}
  #desc ul{margin:0 0 8px;padding-left:16px;color:var(--mut);font-size:12px}
  #desc .drone{color:var(--ink);font-size:12px;border-left:3px solid var(--acc);
               padding:4px 8px;background:#1b212b;border-radius:0 6px 6px 0}
  #tip{position:absolute;right:12px;top:12px;background:rgba(11,14,20,.82);
       border:1px solid var(--line);border-radius:8px;padding:8px 11px;font-size:11px;
       color:var(--mut);max-width:230px}
  #tip b{color:var(--ink)}
  @media (max-width:700px){#app{flex-direction:column}
    #side{width:100%;max-height:48%;border-right:0;border-bottom:1px solid var(--line)}#tip{display:none}}
</style>
</head>
<body>
<div id="app">
  <div id="side">
    <header>
      <h1><b>MÉCANISMES</b> — Fr4n7-F</h1>
      <p>7 familles imprimables · ★ vis-sans-fin retenue pour la V2 · à comparer avant impression</p>
    </header>
    <div class="sec">
      <h2>Mécanisme</h2>
      <div class="btns" id="mechBtns"></div>
    </div>
    <div class="sec">
      <h2>Animation</h2>
      <div class="btns">
        <button id="bPlay" class="big on">Lecture</button>
        <button id="bReset" class="big">Repos</button>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:10px">
        <span>Course</span><span class="val" id="tV">0%</span></div>
      <input type="range" id="t" min="0" max="100" value="0"/>
      <div class="btns" style="margin-top:10px">
        <button id="bDrone" class="big" style="grid-column:1/3">🛩 Vue drone : voir l'OUVERTURE</button>
      </div>
      <p id="droneNote" style="display:none;margin:8px 0 0;color:var(--mut);font-size:11px">
        Le Fr4n7-F plié est posé à côté, à l'échelle : la course anime
        <b style="color:var(--ink)">bouton → verrou → ressorts → bras</b> —
        l'ouverture que le mécanisme choisi devra produire.</p>
    </div>
    <div class="sec" id="desc"></div>
    <div class="sec">
      <h2>Affichage</h2>
      <div class="btns">
        <button id="bWire">Fil de fer</button>
        <button id="bGrid" class="on">Grille</button>
      </div>
    </div>
  </div>
  <div id="view">
    <div id="tip"><b>Souris :</b> glisser = orbite · molette = zoom · clic-droit = pan.
      Chaque pièce est le <b>vrai STL</b> exporté du SCAD — ce que tu vois est ce que
      tu imprimes (<b>stl/mech/</b> + plaques <b>_kit</b>).</div>
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

const STLB64 = __STLS__;
const view = document.getElementById('view');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0e14);
const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 2000);
camera.up.set(0, 0, 1);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
view.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.08;
controls.minDistance = 30; controls.maxDistance = 320;

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.add(new THREE.HemisphereLight(0xbfd3ff, 0x202024, 0.6));
const key = new THREE.DirectionalLight(0xffffff, 1.9); key.position.set(40,60,120); scene.add(key);
const rim = new THREE.DirectionalLight(0x88aaff, 0.6); rim.position.set(-60,-50,40); scene.add(rim);
const grid = new THREE.GridHelper(240, 24, 0x262d38, 0x171c24);
grid.rotation.x = Math.PI/2; scene.add(grid);

const loader = new STLLoader();
function geo(b64){ const bin = Uint8Array.from(atob(b64), c=>c.charCodeAt(0));
  const g = loader.parse(bin.buffer); g.computeVertexNormals(); return g; }
const COL = {base:0xcfd4da, drive:0x2f6fed, out:0x23272e, mid:0x8b929c};
function mesh(name, color){ return new THREE.Mesh(geo(STLB64[name]),
  new THREE.MeshStandardMaterial({color, metalness:.3, roughness:.5})); }
const D2R = Math.PI/180;

/* ---------- build the seven mechanisms (mm coordinates, like the SCAD) ---- */
const MECHS = {};
function reg(key, label, build, kin, desc){ MECHS[key] = {label, build, kin, desc, group:null, parts:{}}; }

reg('worm_crank', 'Vis sans fin + manivelle',
  (g,P)=>{
    P.base = mesh('p_wc_base', COL.base); g.add(P.base);
    P.sector = mesh('p_wc_sector', COL.mid); P.sector.position.z = 3.2;
    P.sector.rotation.z = -14*D2R; g.add(P.sector);      // teeth engaged on the worm
    P.wormG = new THREE.Group(); P.wormG.position.set(20.8,-11,8); P.wormG.rotation.x = -Math.PI/2;
    P.worm = mesh('p_wc_worm', COL.drive); P.wormG.add(P.worm); g.add(P.wormG);
    P.slider = mesh('p_wc_slider', COL.out); P.slider.position.set(6.9,-7.6,3.4); g.add(P.slider);
  },
  (P,t)=>{
    const lead = 6, rs = 16, th0 = -14*D2R, sweep = 36*D2R;   // 1.6 worm turns
    const ths = th0 + t*sweep;
    P.worm.rotation.z = -t*sweep*rs/lead;                 // exact worm/sector ratio
    P.sector.rotation.z = ths;
    P.slider.position.y = -7.6 + (9*Math.sin(ths) - 9*Math.sin(th0));  // pin drives Y
  },
  {p:"Une manivelle (ou le nano-servo) tourne une vis sans fin imprimée (1 filet, pas 6 mm) qui fait avancer un secteur denté ; le pion du secteur pousse le MÊME coulisseau que le bouton V1.",
   pts:["énorme réduction : le petit servo 3,7 g force les 4 ressorts","AUTOBLOQUANT — tient les bras repliés à couple ZÉRO, rien ne se rouvre aux vibrations","c'est l'opérateur de fenêtre de ta photo, miniaturisé"],
   drone:"MÉCANISME RETENU pour la V2 « deploy ». Intégré dans frame_foldable.scad (servo_worm + servo_sector) : le servo visse la course du verrou (3,2 mm) via le pion dans le coulisseau, l'autoblocage tient le paquet plié sans courant. Gate collision_drive = 684 (n'entre pas dans les rails/parois/bouton)."}
);

reg('scissor', 'Bras ciseaux',
  (g,P)=>{
    P.base = mesh('p_sc_base', COL.base); g.add(P.base);
    P.slider = mesh('p_sc_slider', COL.out); P.slider.position.set(-4,8,3.2); g.add(P.slider);
    for (const s of [-1,1]){
      const arm = mesh('p_sc_arm', COL.mid); arm.position.set(s*22,0,6.6);
      const link = mesh('p_sc_link', COL.drive); link.position.set(0,15,4.2);
      g.add(arm); g.add(link); P['arm'+s]=arm; P['link'+s]=link;
    }
  },
  (P,t)=>{
    const py = 15 + t*8;                      // slider pin (0, py)
    P.slider.position.y = 8 + t*8;
    for (const s of [-1,1]){
      const dx = 0 - s*22, dy = py - 0;
      const d = Math.hypot(dx,dy), al = Math.atan2(dy,dx);
      const c = Math.min(1, Math.max(-1,(144 + d*d - 225)/(2*12*d)));
      const th = al + s*Math.acos(c);         // arm pin angle (radius 12)
      P['arm'+s].rotation.z = th;
      const ax = s*22 + 12*Math.cos(th), ay = 12*Math.sin(th);
      P['link'+s].position.set(ax, ay, 9.8);              // seated ON the pins
      P['link'+s].rotation.z = Math.atan2(py-ay, 0-ax);
    }
  },
  {p:"Un coulisseau central tire deux biellettes qui déploient deux bras symétriques — les deux bras extensibles de l'opérateur de ta photo.",
   pts:["imprime à plat, pions imprimés Ø3","mouvement symétrique naturel","grande amplitude pour une petite course"],
   drone:"Peut pousser DEUX languettes opposées à la fois depuis le coulisseau existant."}
);

reg('iris_cam', 'Came iris (rotative)',
  (g,P)=>{
    P.base = mesh('p_ir_base', COL.base); g.add(P.base);
    P.disc = mesh('p_ir_disc', COL.drive); P.disc.position.z = 6.8; g.add(P.disc);  // pins IN the slots
    for (let q=0;q<4;q++){
      const pg = new THREE.Group(); pg.rotation.z = q*Math.PI/2;
      const pin = mesh('p_ir_pin', COL.out); pin.position.set(7,-1.8,3.2);
      pg.add(pin); g.add(pg); P['pin'+q]=pin;
    }
  },
  (P,t)=>{
    P.disc.rotation.z = t*70*D2R;
    for (let q=0;q<4;q++) P['pin'+q].position.x = 4.2 + 8*t;   // follower tracks the spiral
  },
  {p:"Un disque à 4 rainures en spirale d'Archimède traduit sa rotation en 4 translations radiales simultanées.",
   pts:["UN quart de tour libère les 4 coins d'un coup","zéro pièce métallique","se pilote au pouce (molette) ou au palonnier du servo"],
   drone:"LE candidat V2 : le servo tourne le disque, les 4 pions remplacent les 4 doigts du verrou."}
);

reg('rack_pinion', 'Pignon + crémaillère',
  (g,P)=>{
    P.base = mesh('p_rp_base', COL.base); g.add(P.base);
    P.rack = mesh('p_rp_rack', COL.out); P.rack.position.set(2,-6,3.2); g.add(P.rack);
    P.pin = mesh('p_rp_pinion', COL.drive); P.pin.position.set(24,8.6,3.6); g.add(P.pin);  // teeth meshed
  },
  (P,t)=>{
    P.rack.position.x = 2 + t*14;
    P.pin.rotation.z = -t*14/8;
  },
  {p:"Le grand classique : un pignon de 8 dents entraîne une crémaillère droite — conversion rotation → translation directe.",
   pts:["le plus SIMPLE à imprimer et à régler","rapport direct : 1 rad ≈ 8 mm","réversible (pas d'autoblocage)"],
   drone:"Monté sur l'axe du servo V2, il pousse directement le verrou — 2 pièces."}
);

reg('cam_lever', 'Came excentrique + levier',
  (g,P)=>{
    P.base = mesh('p_cl_base', COL.base); g.add(P.base);
    P.cam = mesh('p_cl_cam', COL.drive); P.cam.position.z = 3.4; g.add(P.cam);
    P.fol = mesh('p_cl_follower', COL.out); P.fol.position.set(5.56,-3.5,3.2); g.add(P.fol);
  },
  (P,t)=>{
    const th = (160 - 160*t)*D2R;
    P.cam.rotation.z = th;
    P.fol.position.x = 2.6*Math.cos(th) + 8;   // face exactly on the eccentric rim
  },
  {p:"Un levier quart-de-tour porte un disque EXCENTRIQUE : son bord pousse un poussoir plat dans un canal — force qui croît vers la fin de course.",
   pts:["2 pièces mobiles seulement","démultiplication progressive (serrage type came de vélo)","auto-maintien près du point mort"],
   drone:"Alternative au bouton : un petit levier sur le flanc arme/relâche le verrou."}
);

reg('toggle_clamp', 'Genouillère (over-center)',
  (g,P)=>{
    P.base = mesh('p_tg_base', COL.base); g.add(P.base);
    P.handle = mesh('p_tg_handle', COL.drive); P.handle.position.z = 3.4; g.add(P.handle);
    P.link = mesh('p_tg_link', COL.mid); P.link.position.z = 7.2; g.add(P.link);
    P.pad = mesh('p_tg_pad', COL.out); P.pad.position.set(14,-4,3.2); g.add(P.pad);
  },
  (P,t)=>{
    const a=12, b=16, th=(40 - 55*t)*D2R;     // sweeps PAST the dead centre
    P.handle.rotation.z = th;
    const ax=a*Math.cos(th), ay=a*Math.sin(th);
    const xb = ax + Math.sqrt(Math.max(0, b*b - ay*ay));
    P.link.position.set(ax, ay, 7.2);
    P.link.rotation.z = Math.atan2(0-ay, xb-ax);
    P.pad.position.x = xb - 5;
  },
  {p:"Poignée + biellette qui passent le POINT MORT : au-delà, la charge verrouille le mécanisme au lieu de l'ouvrir (pinces de bridage d'atelier).",
   pts:["verrouillage POSITIF sans ressort de maintien","claquement franc, état lisible d'un coup d'œil","imprime à plat, 4 pièces"],
   drone:"Candidat pour tenir les bras PLIÉS avec un vrai verrou mécanique (transport en sac)."}
);

reg('wiper', 'Essuie-glace (4 barres)',
  (g,P)=>{
    P.base = mesh('p_wp_base', COL.base); g.add(P.base);
    P.gs = mesh('p_wp_gs', COL.drive); P.gs.position.set(-14.5,6.15,3.4); g.add(P.gs);
    P.gb = mesh('p_wp_gb', COL.mid); P.gb.position.z = 3.4; g.add(P.gb);
    P.rod = mesh('p_wp_rod', COL.mid); P.rod.position.z = 8.2; g.add(P.rod);
    P.arm = mesh('p_wp_arm', COL.out); P.arm.position.set(-26,-12,3.6); g.add(P.arm);
  },
  (P,t)=>{
    const rc=6.5, ra=8, L=28, B=[-26,-12];
    const thb = t*2*Math.PI;                         // one crank revolution
    P.gb.rotation.z = thb;
    P.gs.rotation.z = 10*D2R - thb*13/8;             // exact gear ratio 13:8
    const px = rc*Math.cos(thb), py = rc*Math.sin(thb);
    const dx = px-B[0], dy = py-B[1];
    const d = Math.hypot(dx,dy), al = Math.atan2(dy,dx);
    const c = Math.min(1, Math.max(-1,(ra*ra + d*d - L*L)/(2*ra*d)));
    const ph = al - Math.acos(c);                    // rocker angle
    P.arm.rotation.z = ph;
    const qx = B[0]+ra*Math.cos(ph), qy = B[1]+ra*Math.sin(ph);
    P.rod.position.set(qx, qy, 8.2);
    P.rod.rotation.z = Math.atan2(py-qy, px-qx);
  },
  {p:"La photo « desk clearing » : une molette entraîne deux engrenages ; le maneton du grand pignon tire une bielle qui fait OSCILLER un long bras balayeur — la barre d'essuie-glace, en 4 barres (manivelle-balancier).",
   pts:["rotation continue → balayage alternatif automatique","engrenages module commun (13:8), pions imprimés","le bras démultiplie la course : petit maneton, grand balayage"],
   drone:"Un servo à rotation continue balaierait les 4 languettes l'une après l'autre — ou anime un « radar » de démo sur le capot."}
);

/* ---------- scene management ---------- */
const root = new THREE.Group(); scene.add(root);
let current = null;
for (const k of Object.keys(MECHS)){
  const m = MECHS[k];
  m.group = new THREE.Group(); m.group.visible = false;
  m.build(m.group, m.parts);
  // centre each mechanism on the grid
  const bb = new THREE.Box3().setFromObject(m.group);
  const c = bb.getCenter(new THREE.Vector3());
  m.group.position.set(-c.x, -c.y, 0);
  root.add(m.group);
}
const RETAINED = 'worm_crank';   // the mechanism integrated into the airframe (V2 drive)
function show(k){
  current = k;
  for (const kk of Object.keys(MECHS)) MECHS[kk].group.visible = (kk===k);
  document.querySelectorAll('#mechBtns button').forEach(b=>
    b.classList.toggle('on', b.dataset.k===k));
  const d = MECHS[k].desc;
  const retBadge = (k===RETAINED)
    ? `<div style="display:inline-block;margin:0 0 6px;padding:3px 9px;border-radius:12px;`
      + `background:#f5b301;color:#1a1a1a;font-weight:700;font-size:12px">★ MÉCANISME RETENU`
      + `</div>` : '';
  document.getElementById('desc').innerHTML =
    retBadge +
    `<h3>${MECHS[k].label}</h3><p>${d.p}</p>` +
    `<ul>${d.pts.map(x=>`<li>${x}</li>`).join('')}</ul>` +
    `<div class="drone">🛩 Sur le drone : ${d.drone}</div>`;
  applyT(tV);
  window.__mech = k;
  startLoop();
}
const btns = document.getElementById('mechBtns');
for (const k of Object.keys(MECHS)){
  const b = document.createElement('button');
  b.textContent = (k===RETAINED ? '★ ' : '') + MECHS[k].label; b.dataset.k = k;
  if (k===RETAINED){ b.style.borderColor = '#f5b301'; b.style.fontWeight = '700'; }
  b.addEventListener('click', ()=>show(k));
  btns.appendChild(b);
}

/* ---------- the drone, folded, at true scale — to SEE the opening ---------- */
const FOLD_A = 1.70859, BTN_Y = -19;
const DSIGN = {fr:+1, fl:-1, rr:-1, rl:+1};
const DPIV  = {fr:[ 24.5,-36], fl:[-24.5,-36], rr:[ 24.5, 36], rl:[-24.5, 36]};
const droneG = new THREE.Group(); droneG.visible = false;
droneG.position.set(105, 0, 8);            // beside the mechanism, feet on the grid
scene.add(droneG);
const dBody = mesh('d_body', COL.base); droneG.add(dBody);
const dLatch = mesh('d_latch', COL.out); droneG.add(dLatch);
const dBtn = mesh('d_button', COL.drive); dBtn.position.set(0, BTN_Y, 0); droneG.add(dBtn);
const dArms = {};
for (const k of Object.keys(DPIV)){
  const ag = new THREE.Group();
  ag.position.set(DPIV[k][0], DPIV[k][1], 0);
  ag.add(mesh('d_arm_'+k, COL.mid));
  ag.rotation.z = DSIGN[k]*FOLD_A;         // starts FOLDED
  droneG.add(ag); dArms[k] = ag;
}
let droneOn = false;
function droneKin(t){
  // t 0..1 = press the button -> latch slides -> springs open the arms -> release
  const press = Math.min(t/0.3, 1) * (t < 0.85 ? 1 : Math.max(0, 1-(t-0.85)/0.15));
  const foldT = Math.min(1, Math.max(0, 1 - (t-0.30)/0.55));
  dBtn.position.z = -press*3.5;
  dLatch.position.y = press*3.2;
  for (const k of Object.keys(dArms)) dArms[k].rotation.z = DSIGN[k]*FOLD_A*foldT;
}
document.getElementById('bDrone').addEventListener('click', e=>{
  droneOn = !droneOn; droneG.visible = droneOn;
  e.target.classList.toggle('on', droneOn);
  document.getElementById('droneNote').style.display = droneOn ? 'block' : 'none';
  if (droneOn){ controls.target.set(55, 0, 10);
    camera.position.set(80, -180, 120); controls.maxDistance = 420; }
  else { controls.target.set(0, 0, 6);
    camera.position.set(70, -95, 75); }
  controls.update(); startLoop();
});
window.__droneOn = () => droneOn;

/* ---------- animation ---------- */
let tV = 0, playing = true, dir = 1;
function applyT(t){
  tV = t;
  document.getElementById('t').value = Math.round(t*100);
  document.getElementById('tV').textContent = Math.round(t*100)+'%';
  if (current) MECHS[current].kin(MECHS[current].parts, t);
  if (droneOn) droneKin(t);
}
window.__t = () => tV;
document.getElementById('t').addEventListener('input', e=>{
  playing = false; document.getElementById('bPlay').classList.remove('on');
  applyT(e.target.value/100); startLoop(); });
document.getElementById('bPlay').addEventListener('click', e=>{
  playing = !playing; e.target.classList.toggle('on', playing); startLoop(); });
document.getElementById('bReset').addEventListener('click', ()=>{
  playing = false; document.getElementById('bPlay').classList.remove('on');
  applyT(0); startLoop(); });

let wire=false;
document.getElementById('bWire').addEventListener('click', e=>{ wire=!wire; e.target.classList.toggle('on',wire);
  root.traverse(o=>{ if(o.isMesh) o.material.wireframe=wire; }); });
document.getElementById('bGrid').addEventListener('click', e=>{ grid.visible=!grid.visible; e.target.classList.toggle('on',grid.visible); });

camera.position.set(70, -95, 75);
controls.target.set(0, 0, 6); controls.update();

function resize(){ const w=view.clientWidth,h=view.clientHeight;
  renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();

let ioVisible=true, looping=false;
window.__vizRendering=()=>looping;
function activeR(){ return ioVisible && !document.hidden; }
function startLoop(){ if(!looping){ looping=true; clock.getDelta(); requestAnimationFrame(loop); } }
try { new IntersectionObserver(es=>{ ioVisible=es[0].isIntersecting;
  if(activeR()) startLoop(); }, {threshold:0.01}).observe(view); } catch(_){}
document.addEventListener('visibilitychange', ()=>{ if(activeR()) startLoop(); });

const clock = new THREE.Clock();
function loop(){
  if(!activeR()){ looping=false; return; }
  requestAnimationFrame(loop);
  const dt = Math.min(clock.getDelta(), 0.1);
  if (playing){
    let t = tV + dir*dt/2.4;                 // full stroke ~2.4 s, ping-pong
    if (t>1){ t=1; dir=-1; } if (t<0){ t=0; dir=1; }
    applyT(t);
  }
  controls.update();
  renderer.render(scene, camera);
}
show('worm_crank');
startLoop();
</script>
</body>
</html>
"""


def main():
    stls = {p: b64(os.path.join(STL, p + ".stl")) for p in PARTS}
    for p in DRONE_PARTS:
        stls["d_" + p] = b64(os.path.join(DRONE_STL, p + ".stl"))
    html = (TEMPLATE
            .replace("__IMPORTMAP__", importmap())
            .replace("__STLS__", json.dumps(stls, separators=(",", ":"))))
    with open(OUT, "w") as f:
        f.write(html)
    print("== Fr4n7-F mechanisms viewer ==")
    print(f"  wrote {os.path.relpath(OUT, REPO)} ({len(html)} B)")


if __name__ == "__main__":
    main()
