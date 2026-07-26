#!/usr/bin/env python3
"""Build build.html — an interactive ASSEMBLY simulator for the TinyHoop MK1.

Same real meshes as the 3-D viewer (`../viz/drone_viewer.html`): the JeNo STEP
plates, the DJI O4 parts, the printed TPU, the Readytosky 1104s, the DOGCOM
pack… Here you pick a part from the bin, drag it, and **snap** it into its true
assembly position; when every part is seated you get the complete drone.

    python3 TinyHoopMK1/build/gen_build.py     # writes build.html

Self-contained (meshes base64-inlined) so it opens by double-click, exactly like
drone_viewer.html. Assembly coordinates are copied from viz/gen_viewer.py, so a
finished build matches the viewer part for part.
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
VENDOR = os.path.join(REPO, "sim", "viz", "vendor")
STL = os.path.join(REPO, "TinyHoopMK1", "cad", "stl")
TPU = os.path.join(REPO, "TinyHoopMK1", "cad", "frame_jeno", "tpu")
PARTS = os.path.join(REPO, "TinyHoopMK1", "cad", "frame_jeno", "parts")
DJI = os.path.join(REPO, "TinyHoopMK1", "cad", "dji_o4")
OUT = os.path.join(HERE, "build.html")

MOTORS = [[46.6, 34.1], [-46.6, 34.1], [-46.6, -34.1], [46.6, -34.1]]
FRAME_STAND = [[0, 25.6], [8.5, -32.2], [-8.5, -32.2]]
BOARD_STAND = [[18, 0], [-18, 0], [0, 18], [0, -18]]

# The build order. Each step = one part (or a set of identical parts) with its
# TRUE seat (mm / deg), the material look, and a fitting note.
# repeat: 'motors' -> one copy per motor arm, 'frame_stand'/'board_stand' -> posts
STEPS = [
    dict(id="frame_bottom", label="Plaque basse (carbone 3 mm)", mesh="frame_bottom",
         mat="carbon", pos=[0, 0, 0],
         note="La base de tout : pose-la à plat, les 4 bras vers l'extérieur."),
    dict(id="motors", label="4× moteurs 1104 7500KV", mesh="motor", mat="alu",
         repeat="motors", pos=[0, 0, 3],
         note="Un par bras, sur les 4 trous à 9 mm. Vis M2 par le dessous."),
    dict(id="standoffs", label="3 entretoises de châssis (alu)", mesh=None,
         mat="alu", repeat="frame_stand", pos=[0, 0, 3],
         note="Elles portent la plaque haute : 1 à l'avant, 2 à l'arrière."),
    dict(id="elec", label="Carte AIO JHEMCU GHF411", mesh="ghf411", mat="pcb",
         pos=[0, 0, 4], rot=[0, 0, 45],
         note="À 45° sur le montage 25,5 mm, connecteurs vers l'arrière."),
    dict(id="board_stand", label="4 entretoises de carte", mesh=None, mat="alu",
         repeat="board_stand", pos=[0, 0, 3],
         note="Elles soulèvent l'air unit au-dessus de la FC (soft-mount)."),
    dict(id="airunit", label="Air unit DJI O4 Lite", mesh="o4airunit", mat="pcb",
         pos=[0, 0, 10], rot=[0, 0, 45],
         note="Empilée sur la FC, même trame de vis."),
    dict(id="camcage", label="Cage caméra (carbone)", mesh="camcage", mat="carbon",
         pos=[0, 0, 0],
         note="Les deux joues carbone qui protègent la caméra."),
    dict(id="cagestd", label="2 entretoises de cage (or)", mesh=None, mat="gold",
         repeat="cage_bars", pos=[0, 0, 0],
         note="Elles relient les joues, la caméra prend place entre les deux."),
    dict(id="cam_mount_bottom", label="Support caméra BAS (TPU)", mesh="cam_mount_bottom",
         mat="tpu", pos=[0, 4.5, -1.5], rot=[-5, 0, 0],
         note="Le berceau inférieur : il reçoit le bas de la caméra."),
    dict(id="camera", label="Caméra DJI O4 Lite", mesh="o4cam", mat="plastic",
         pos=[0, 37, 4], rot=[27, 0, 90],
         note="Inclinée ~27°, l'objectif bien en retrait dans la cage."),
    dict(id="cam_mount_top", label="Support caméra HAUT (TPU)", mesh="cam_mount_top",
         mat="tpu", pos=[0, -2, -1], rot=[-6, 0, 0],
         note="Il referme le berceau et bloque la caméra."),
    dict(id="frame_top", label="Plaque haute (carbone 2 mm)", mesh="frame_top",
         mat="carbon", pos=[0, 0, 0],
         note="Vissée sur les 3 entretoises. La fente arrière = passage XT30."),
    dict(id="rear_bay", label="Baie arrière (TPU imprimé)", mesh="rear_bay",
         mat="tpu", pos=[0, -32, 3], rot=[0, 0, 180],
         note="Elle tient l'antenne VTX et guide l'antenne RX."),
    dict(id="rx_holder", label="Berceau RX (TPU)", mesh="rx_holder", mat="tpu",
         pos=[0, -22, 4], note="Petit bac imprimé pour le récepteur ELRS."),
    dict(id="rx_pcb", label="Récepteur ELRS (PCB)", mesh="rx_pcb", mat="pcb",
         pos=[0, -22, 5.6], note="Clipsé dans son berceau, antenne vers l'arrière."),
    dict(id="rx_antenna", label="Antenne RX (T, horizontale)", mesh="rx", mat="plastic",
         pos=[0, -33, 6], rot=[87, 0, 0],
         note="Horizontale à l'arrière, insérée dans le fourreau TPU."),
    dict(id="vtxant", label="Antenne VTX 5,8 GHz", mesh="dji_pro_ant", mat="plastic",
         pos=[0, -29, 48.5], rot=[-147, 0, 0],
         note="Tête vers le haut dans la baie arrière."),
    dict(id="cap_holder", label="Support condensateur (TPU)", mesh="cap_holder",
         mat="tpu", pos=[17, -24, 9], note="Il évite que le condo touche le carbone."),
    dict(id="cap", label="Condensateur 25 V 22 µF", mesh="cap", mat="plastic",
         pos=[17, -24, 9.6], note="Dans son support, pattes vers les pads VBAT."),
    dict(id="gps", label="GPS / compas", mesh="gps", mat="plastic",
         pos=[-4, -15, 19], note="Posé sur le stack, dans l'empreinte du châssis."),
    dict(id="buzzer", label="Buzzer", mesh="buzzer", mat="plastic",
         pos=[11, -31, 6], note="À l'arrière, orienté vers l'extérieur."),
    dict(id="tpu_bumpers", label="Protections TPU (bumpers)", mesh="arm_bumper",
         mat="tpu", repeat="motors", pos=[0, 0, 0],
         note="Un patin par bras : ils encaissent les crashs."),
    dict(id="props", label="4× hélices Gemfan 2520", mesh="prop", mat="plastic",
         repeat="motors", pos=[0, 0, 13.5],
         note="En dernier ! 2 sens de rotation, écrous serrés."),
    dict(id="battery", label="Batterie DOGCOM 560 mAh 3S", mesh="battery", mat="lipo",
         pos=[0, 4, 24], note="Sanglée sur la plaque haute, XT30 par la fente."),
]

MATERIALS = {                      # look, mirrors the 3-D viewer
    "carbon":  dict(color=0x1a1d21, metal=0.22, rough=0.46),
    "alu":     dict(color=0xc2c5cb, metal=0.92, rough=0.26),
    "gold":    dict(color=0xd8a520, metal=0.88, rough=0.26),
    "tpu":     dict(color=0x2b2f36, metal=0.04, rough=0.86),
    "pcb":     dict(color=0x0b6b39, metal=0.20, rough=0.50),
    "plastic": dict(color=0x141519, metal=0.10, rough=0.55),
    "lipo":    dict(color=0x0d0d10, metal=0.12, rough=0.62),
}

MESHES = {
    "frame_bottom":     os.path.join(PARTS, "frame_bottom.stl"),
    "frame_top":        os.path.join(STL, "jeno_top.stl"),
    "camcage":          os.path.join(PARTS, "cam_cage.stl"),
    "motor":            os.path.join(PARTS, "motor_1104.stl"),
    "prop":             os.path.join(STL, "prop.stl"),
    "ghf411":           os.path.join(DJI, "ghf411_aio.stl"),
    "o4airunit":        os.path.join(DJI, "o4_airunit.stl"),
    "o4cam":            os.path.join(DJI, "o4_cam_head.stl"),
    "cam_mount_top":    os.path.join(TPU, "o4_mount_top.stl"),
    "cam_mount_bottom": os.path.join(TPU, "o4_mount_bottom.stl"),
    "arm_bumper":       os.path.join(TPU, "arm_bumper.stl"),
    "rear_bay":         os.path.join(STL, "rear_bay.stl"),
    "cap_holder":       os.path.join(STL, "cap_holder.stl"),
    "cap":              os.path.join(STL, "capacitor.stl"),
    "rx_pcb":           os.path.join(STL, "rx_pcb.stl"),
    "rx_holder":        os.path.join(STL, "rx_holder.stl"),
    "rx":               os.path.join(STL, "rx_antenna.stl"),
    "dji_pro_ant":      os.path.join(STL, "dji_pro_ant.stl"),
    "gps":              os.path.join(STL, "gps_module.stl"),
    "buzzer":           os.path.join(STL, "buzzer.stl"),
    "battery":          os.path.join(STL, "battery.stl"),
}


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def data_url(path, mime="text/javascript"):
    return f"data:{mime};base64," + b64(path)


def importmap():
    v = lambda *p: data_url(os.path.join(VENDOR, *p))
    return json.dumps({"imports": {
        "three": v("three.module.js"),
        "three/addons/controls/OrbitControls.js": v("addons", "controls", "OrbitControls.js"),
        "three/addons/loaders/STLLoader.js": v("addons", "loaders", "STLLoader.js"),
        "three/addons/environments/RoomEnvironment.js": v("addons", "environments", "RoomEnvironment.js"),
        "three/addons/geometries/RoundedBoxGeometry.js": v("addons", "geometries", "RoundedBoxGeometry.js"),
    }}, separators=(",", ":"))


TEMPLATE = r"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TinyHoop MK1 — simulateur d'assemblage</title>
<style>
 :root{--bg:#0b0e14;--pan:#11151d;--ink:#e8ecf3;--dim:#93a0b4;--line:#1f2735;
   --acc:#5db0ff;--ok:#3ddc91;--warn:#f2b400}
 *{box-sizing:border-box} html,body{margin:0;height:100%;overflow:hidden}
 body{background:var(--bg);color:var(--ink);display:flex;
   font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
 #side{width:330px;flex:0 0 330px;background:var(--pan);border-right:1px solid var(--line);
   overflow:auto;padding:15px}
 #view{flex:1;position:relative} canvas{display:block}
 h1{font-size:16px;margin:0} h2{font-size:11px;letter-spacing:.09em;color:var(--dim);
   text-transform:uppercase;margin:16px 0 8px}
 .sub{color:var(--dim);font-size:12px}
 #bar{height:7px;background:#0d1219;border:1px solid var(--line);border-radius:5px;
   overflow:hidden;margin:9px 0 5px}
 #fill{height:100%;width:0;background:linear-gradient(90deg,var(--acc),var(--ok));transition:width .3s}
 .step{display:flex;gap:9px;align-items:flex-start;padding:7px 8px;border-radius:7px;
   border:1px solid transparent;cursor:pointer;margin-bottom:2px}
 .step:hover{background:#151b26} .step.cur{border-color:var(--acc);background:#141d2b}
 .step.done{opacity:.55} .step .n{flex:0 0 20px;height:20px;border-radius:50%;
   background:#1b2534;color:var(--dim);font-size:11px;display:grid;place-items:center;margin-top:1px}
 .step.done .n{background:var(--ok);color:#05231a} .step.cur .n{background:var(--acc);color:#04203a}
 .step .t{font-size:12.5px;line-height:1.35} .step .h{color:var(--dim);font-size:11px}
 button{background:#182231;color:var(--ink);border:1px solid var(--line);border-radius:7px;
   padding:8px;font-size:12.5px;cursor:pointer;width:100%}
 button:hover{border-color:var(--acc)} button.p{background:#1c3category}
 button.primary{background:#12385c;border-color:#2a6da8}
 .row2{display:flex;gap:6px} .row2 button{flex:1}
 #tip{position:absolute;left:14px;bottom:14px;background:rgba(14,18,26,.9);
   border:1px solid var(--line);border-radius:9px;padding:10px 12px;max-width:430px;font-size:12.5px}
 #tip b{color:var(--acc)}
 #hud{position:absolute;top:12px;right:12px;background:rgba(14,18,26,.9);
   border:1px solid var(--line);border-radius:9px;padding:9px 11px;font-size:11.5px;color:var(--dim);
   max-width:250px}
 #done{position:absolute;inset:0;display:none;place-items:center;pointer-events:none}
 #done div{background:rgba(9,32,24,.93);border:1px solid var(--ok);border-radius:14px;
   padding:20px 26px;text-align:center}
 #done h3{margin:0 0 5px;color:var(--ok);font-size:19px}
 kbd{background:#1b2534;border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:11px}
</style></head><body>
<div id="side">
  <h1>TinyHoop <b style="color:var(--acc)">MK1</b> — assemblage</h1>
  <div class="sub">les vraies pièces du visualisateur 3D</div>
  <div id="bar"><div id="fill"></div></div>
  <div class="sub"><span id="cnt">0</span> / <span id="tot">0</span> pièces posées</div>

  <h2>Commandes</h2>
  <div class="row2">
    <button id="bSnap" class="primary">Emboîter (Entrée)</button>
    <button id="bSkip">Suivante</button>
  </div>
  <div style="height:6px"></div>
  <div class="row2">
    <button id="bAll">Tout assembler</button>
    <button id="bReset">Recommencer</button>
  </div>
  <div style="height:6px"></div>
  <button id="bGhost">Fantômes : oui</button>

  <h2>Gamme de montage</h2>
  <div id="steps"></div>
</div>
<div id="view">
  <div id="hud"><b>Souris :</b> glisser = orbite · molette = zoom<br>
    <b>Pièce :</b> glisse-la à la souris · <kbd>Entrée</kbd> = emboîter ·
    <kbd>R</kbd> = tourner · <kbd>Échap</kbd> = reposer</div>
  <div id="tip"></div>
  <div id="done"><div><h3>Drone assemblé ✔</h3>
    <span class="sub">Toutes les pièces sont à leur place — c'est le TinyHoop MK1 complet.</span></div></div>
</div>

<script type="importmap">__IMPORTMAP__</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const STEPS = __STEPS__, MATS = __MATS__, MESH_B64 = __MESHES__;
const MOTORS = __MOTORS__, FRAME_STAND = __FRAME_STAND__, BOARD_STAND = __BOARD_STAND__;
const D = Math.PI/180, MM = 1/1000;

// ---------- scene ----------
const view = document.getElementById('view');
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0b0e14);
const camera = new THREE.PerspectiveCamera(42, 1, 0.001, 100);
camera.up.set(0,0,1); camera.position.set(.16,.17,.11);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
view.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = .08;
controls.minDistance = .06; controls.maxDistance = .8; controls.target.set(0,0,.018);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), .04).texture;
scene.add(new THREE.HemisphereLight(0xbfd3ff, 0x202024, .55));
const key = new THREE.DirectionalLight(0xffffff, 2.0); key.position.set(.2,.26,.5); scene.add(key);
const rim = new THREE.DirectionalLight(0x88aaff, .7); rim.position.set(-.3,-.28,.16); scene.add(rim);
const grid = new THREE.GridHelper(.4, 32, 0x262d38, 0x171c24);
grid.rotation.x = Math.PI/2; scene.add(grid);

const loader = new STLLoader();
const geoCache = {};
function geo(name){
  if (!geoCache[name]){ const bin = Uint8Array.from(atob(MESH_B64[name]), c=>c.charCodeAt(0));
    const g = loader.parse(bin.buffer); g.computeVertexNormals(); geoCache[name] = g; }
  return geoCache[name];
}
function mat(m){ const p = MATS[m];
  return new THREE.MeshStandardMaterial({color:p.color, metalness:p.metal, roughness:p.rough}); }

// a smooth alu standoff / gold cage bar, built procedurally (no faceted STL)
function post(h, r, m){ const g = new THREE.Mesh(new THREE.CylinderGeometry(r,r,h*MM,32,1), mat(m));
  g.rotation.x = Math.PI/2; return g; }

// ---------- build one THREE.Group per step, at its TRUE seat ----------
const root = new THREE.Group(); scene.add(root);
const items = [];            // {step, grp, seat:{pos,quat}, placed}

function makeStepObject(s){
  const grp = new THREE.Group();
  const add = (obj, x, y, z) => { obj.position.set(x*MM, y*MM, z*MM); grp.add(obj); };
  if (s.repeat === 'motors'){
    for (const [mx,my] of MOTORS){ const m = new THREE.Mesh(geo(s.mesh), mat(s.mat));
      m.scale.setScalar(MM); add(m, mx, my, s.pos[2]); }
  } else if (s.repeat === 'frame_stand'){
    for (const [x,y] of FRAME_STAND){ const p = post(14, .0021, s.mat); add(p, x, y, 3+7); }
  } else if (s.repeat === 'board_stand'){
    for (const [x,y] of BOARD_STAND){ const p = post(3, .0021, s.mat); add(p, x, y, 3+1.5); }
  } else if (s.repeat === 'cage_bars'){
    for (const [y,z] of [[45,29],[55,8]]){
      const b = new THREE.Mesh(new THREE.CylinderGeometry(.0016,.0016,.0168,32,1), mat('gold'));
      b.rotation.z = Math.PI/2; add(b, 0, y, z);
      for (const sx of [-1,1]){ const c = new THREE.Mesh(
          new THREE.CylinderGeometry(.0021,.0021,.0014,20), mat('alu'));
        c.rotation.z = Math.PI/2; add(c, sx*8, y, z); } }
  } else {
    const m = new THREE.Mesh(geo(s.mesh), mat(s.mat)); m.scale.setScalar(MM);
    const r = s.rot || [0,0,0];
    m.rotation.set(r[0]*D, r[1]*D, r[2]*D);
    add(m, s.pos[0], s.pos[1], s.pos[2]);
  }
  return grp;
}

// where a not-yet-placed part waits: laid out on the ground around the drone
function binSpot(i, n){
  const a = (i/n) * Math.PI*2 + .35, R = .135;
  return new THREE.Vector3(Math.cos(a)*R, Math.sin(a)*R, .002);
}

STEPS.forEach((s,i) => {
  const grp = makeStepObject(s);
  root.add(grp);
  const seat = grp.position.clone();                 // groups are built already seated
  const item = {step:s, grp, seat, home:binSpot(i, STEPS.length), placed:false};
  grp.position.copy(item.home);                      // start in the bin
  items.push(item);
});

// translucent "ghost" of each part at its final seat, as a guide
const ghosts = [];
items.forEach(it => {
  const g = it.grp.clone(true);
  g.traverse(o => { if (o.isMesh){ o.material = new THREE.MeshStandardMaterial({
    color:0x5db0ff, transparent:true, opacity:.13, depthWrite:false }); } });
  g.position.copy(it.seat); g.visible = true; root.add(g); ghosts.push(g);
});

// ---------- UI ----------
let cur = 0, ghostOn = true;
const stepsEl = document.getElementById('steps'), tipEl = document.getElementById('tip');
items.forEach((it,i) => {
  const d = document.createElement('div'); d.className = 'step'; d.dataset.i = i;
  d.innerHTML = `<div class="n">${i+1}</div><div class="t">${it.step.label}` +
                `<div class="h">${it.step.note}</div></div>`;
  d.addEventListener('click', () => select(i));
  stepsEl.appendChild(d);
});
document.getElementById('tot').textContent = items.length;

function refresh(){
  const done = items.filter(i => i.placed).length;
  document.getElementById('cnt').textContent = done;
  document.getElementById('fill').style.width = (100*done/items.length) + '%';
  [...stepsEl.children].forEach((el,i) => {
    el.classList.toggle('done', items[i].placed);
    el.classList.toggle('cur', i === cur && !items[i].placed);
  });
  ghosts.forEach((g,i) => { g.visible = ghostOn && !items[i].placed; });
  const it = items[cur];
  tipEl.innerHTML = it
    ? `<b>Étape ${cur+1}/${items.length} — ${it.step.label}</b><br>${it.step.note}`
    : '';
  document.getElementById('done').style.display =
    (done === items.length) ? 'grid' : 'none';
  if (done === items.length) tipEl.innerHTML =
    '<b>Assemblage terminé</b> — le drone est complet et correctement structuré.';
}
function select(i){ cur = i; refresh();
  [...stepsEl.children][i].scrollIntoView({block:'nearest'}); }
function nextPending(){
  for (let k=0;k<items.length;k++){ const i=(cur+k)%items.length; if(!items[i].placed) return i; }
  return -1;
}

// animate a part from wherever it is into its seat = "emboîter"
function snap(i, ms=520){
  const it = items[i]; if (!it || it.placed) return;
  const from = it.grp.position.clone(), to = it.seat.clone(), t0 = performance.now();
  it.placed = true;
  (function tick(){
    const t = Math.min(1, (performance.now()-t0)/ms);
    const e = 1 - Math.pow(1-t, 3);                    // ease-out
    it.grp.position.lerpVectors(from, to, e);
    it.grp.position.z += Math.sin(Math.PI*t) * .012;    // small arc, like a hand
    if (t < 1) requestAnimationFrame(tick);
    else { it.grp.position.copy(to); refresh(); }
  })();
  const n = nextPending(); if (n >= 0) cur = n;
  refresh();
}

document.getElementById('bSnap').onclick = () => snap(cur);
document.getElementById('bSkip').onclick = () => { const n = nextPending(); if(n>=0) select(n); };
document.getElementById('bAll').onclick = () => {
  items.forEach((it,i) => { if(!it.placed) setTimeout(()=>snap(i,420), i*130); }); };
document.getElementById('bReset').onclick = () => {
  items.forEach(it => { it.placed = false; it.grp.position.copy(it.home);
    it.grp.rotation.set(0,0,0); }); cur = 0; refresh(); };
document.getElementById('bGhost').onclick = e => { ghostOn = !ghostOn;
  e.target.textContent = 'Fantômes : ' + (ghostOn ? 'oui' : 'non'); refresh(); };
addEventListener('keydown', e => {
  if (e.key === 'Enter'){ snap(cur); e.preventDefault(); }
  else if (e.key === 'r' || e.key === 'R'){ const it = items[cur];
    if (it && !it.placed) it.grp.rotation.z += 15*D; }
  else if (e.key === 'Escape'){ const it = items[cur];
    if (it && !it.placed) it.grp.position.copy(it.home); }
});

// ---------- drag a part on the ground plane, snap when close ----------
const ray = new THREE.Raycaster(), ptr = new THREE.Vector2();
let dragging = null, dragZ = 0;
function pick(ev){
  const r = renderer.domElement.getBoundingClientRect();
  ptr.x = ((ev.clientX-r.left)/r.width)*2-1; ptr.y = -((ev.clientY-r.top)/r.height)*2+1;
  ray.setFromCamera(ptr, camera);
  const hits = ray.intersectObjects(items.filter(i=>!i.placed).map(i=>i.grp), true);
  if (!hits.length) return null;
  let o = hits[0].object; while (o.parent && o.parent !== root) o = o.parent;
  return items.findIndex(i => i.grp === o);
}
renderer.domElement.addEventListener('pointerdown', ev => {
  const i = pick(ev); if (i < 0 || i === null) return;
  dragging = i; dragZ = items[i].grp.position.z; select(i);
  controls.enabled = false;
});
renderer.domElement.addEventListener('pointermove', ev => {
  if (dragging === null) return;
  const r = renderer.domElement.getBoundingClientRect();
  ptr.x = ((ev.clientX-r.left)/r.width)*2-1; ptr.y = -((ev.clientY-r.top)/r.height)*2+1;
  ray.setFromCamera(ptr, camera);
  const pl = new THREE.Plane(new THREE.Vector3(0,0,1), -dragZ), hit = new THREE.Vector3();
  if (ray.ray.intersectPlane(pl, hit)) items[dragging].grp.position.set(hit.x, hit.y, dragZ);
});
addEventListener('pointerup', () => {
  if (dragging === null) return;
  const it = items[dragging];
  if (it.grp.position.distanceTo(it.seat) < .022) snap(dragging, 260);   // close enough -> click in
  dragging = null; controls.enabled = true;
});

function resize(){ const w = view.clientWidth, h = view.clientHeight;
  renderer.setSize(w,h); camera.aspect = w/h; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize(); refresh();
try { window.__items = items; window.__snap = snap; } catch(_){}
(function loop(){ requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();
</script></body></html>
"""


def main():
    meshes = {k: b64(v) for k, v in MESHES.items() if os.path.exists(v)}
    missing = [k for k, v in MESHES.items() if not os.path.exists(v)]
    steps = [s for s in STEPS if s.get("mesh") is None or s["mesh"] in meshes]
    dropped = [s["id"] for s in STEPS if s not in steps]

    html = (TEMPLATE
            .replace("__IMPORTMAP__", importmap())
            .replace("__STEPS__", json.dumps(steps, separators=(",", ":")))
            .replace("__MATS__", json.dumps(MATERIALS, separators=(",", ":")))
            .replace("__MESHES__", json.dumps(meshes, separators=(",", ":")))
            .replace("__MOTORS__", json.dumps(MOTORS, separators=(",", ":")))
            .replace("__FRAME_STAND__", json.dumps(FRAME_STAND, separators=(",", ":")))
            .replace("__BOARD_STAND__", json.dumps(BOARD_STAND, separators=(",", ":"))))
    with open(OUT, "w") as fh:
        fh.write(html)

    print("== TinyHoop MK1 — simulateur d'assemblage ==")
    print(f"  {len(steps)} étapes · {len(meshes)} maillages réels")
    print(f"  wrote {os.path.relpath(OUT, REPO)} ({len(html)//1024} KB)")
    if missing:
        print(f"  maillages absents: {', '.join(missing)}")
    if dropped:
        print(f"  étapes retirées: {', '.join(dropped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
