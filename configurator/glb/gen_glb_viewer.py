#!/usr/bin/env python3
"""Build glb_viewer.html — the GLB-loading proof of the configurator pipeline.

Unlike the TinyHoop viewer (one 18 MB HTML with every mesh base64-inlined), this
page is a ~200 KB shell that **fetches the .glb parts on demand** from
`parts/` next to it, using the vendored GLTFLoader. That is the property the
online configurator needs: swapping a SKU loads one small file instead of
rebuilding a monolith.

    python3 configurator/glb/gen_glb_viewer.py

Serve the folder (GLB fetches need HTTP, not file://):

    python3 -m http.server -d configurator/glb 8000   # then open /glb_viewer.html
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
VENDOR = os.path.join(REPO, "sim", "viz", "vendor")
OUT = os.path.join(HERE, "glb_viewer.html")

# where each GLB sits in the assembly (mm) — same coordinates as the 3-D viewer
PLACEMENT = {
    "frame_bottom":  dict(pos=[0, 0, 0]),
    "frame_top":     dict(pos=[0, 0, 0]),
    "cam_cage":      dict(pos=[0, 0, 0]),
    "cam_mount_top": dict(pos=[0, -2, -1], rot=[-6, 0, 0]),
    "cam_mount_bot": dict(pos=[0, 4.5, -1.5], rot=[-5, 0, 0]),
    "o4_cam":        dict(pos=[0, 42, 4], rot=[27, 0, 90]),
    "o4_airunit":    dict(pos=[0, 0, 10], rot=[0, 0, 45]),
    "ghf411":        dict(pos=[0, 0, 4], rot=[0, 0, 45]),
    "battery":       dict(pos=[0, 4, 24]),
    "rear_bay":      dict(pos=[0, -32, 3], rot=[0, 0, 180]),
    "cap_holder":    dict(pos=[17, -24, 9]),
    "capacitor":     dict(pos=[17, -24, 9.6]),
    "rx_holder":     dict(pos=[0, -22, 4]),
    "rx_pcb":        dict(pos=[0, -22, 5.6]),
    "gps_module":    dict(pos=[-4, -15, 19]),
    "buzzer":        dict(pos=[11, -31, 6]),
    "ant_dji":       dict(pos=[0, -30, 7], rot=[28, 0, 0], group="antenna"),
    "ant_rhcp":      dict(pos=[0, -30, 7], rot=[28, 0, 0], group="antenna", hidden=True),
    "ant_foxeer":    dict(pos=[0, -30, 7], rot=[28, 0, 0], group="antenna", hidden=True),
    "ant_matchstick":dict(pos=[0, -30, 7], rot=[28, 0, 0], group="antenna", hidden=True),
    "rx_antenna":    dict(pos=[0, -33, 6], rot=[87, 0, 0]),
}
MOTORS = [[46.6, 34.1], [-46.6, 34.1], [-46.6, -34.1], [46.6, -34.1]]


def data_url(path, mime="text/javascript"):
    with open(path, "rb") as fh:
        return f"data:{mime};base64," + base64.b64encode(fh.read()).decode()


def importmap():
    v = lambda *p: data_url(os.path.join(VENDOR, *p))
    return json.dumps({"imports": {
        "three": v("three.module.js"),
        "three/addons/controls/OrbitControls.js": v("addons", "controls", "OrbitControls.js"),
        "three/addons/loaders/GLTFLoader.js": v("addons", "loaders", "GLTFLoader.js"),
        "three/addons/utils/BufferGeometryUtils.js": v("addons", "utils", "BufferGeometryUtils.js"),
        "three/addons/environments/RoomEnvironment.js": v("addons", "environments", "RoomEnvironment.js"),
    }}, separators=(",", ":"))


TEMPLATE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>STRATOS — configurateur GLB</title>
<style>
 :root{--bg:#0b0e14;--pan:#11151d;--ink:#e8ecf3;--dim:#93a0b4;--line:#1f2735;--acc:#5db0ff}
 *{box-sizing:border-box} html,body{margin:0;height:100%}
 body{background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;display:flex}
 #side{width:300px;flex:0 0 300px;background:var(--pan);border-right:1px solid var(--line);
   overflow:auto;padding:16px}
 #view{flex:1;position:relative} canvas{display:block}
 h1{font-size:16px;margin:0 0 2px} h2{font-size:11px;letter-spacing:.09em;color:var(--dim);
   text-transform:uppercase;margin:18px 0 8px}
 .sub{color:var(--dim);font-size:12px;margin-bottom:4px}
 .tag{display:inline-block;background:#16202e;border:1px solid var(--line);border-radius:5px;
   padding:2px 7px;font-size:11px;color:var(--acc);margin-top:6px}
 label.row{display:flex;align-items:center;gap:8px;padding:3px 0;font-size:12.5px;cursor:pointer}
 label.row input{accent-color:var(--acc)}
 select,button{width:100%;background:#182231;color:var(--ink);border:1px solid var(--line);
   border-radius:6px;padding:7px;font-size:12.5px}
 button{cursor:pointer} button:hover{border-color:var(--acc)}
 #log{font:11px/1.5 ui-monospace,Menlo,monospace;color:var(--dim);white-space:pre-wrap;
   background:#0d1219;border:1px solid var(--line);border-radius:6px;padding:8px;margin-top:8px;
   max-height:190px;overflow:auto}
 table{width:100%;border-collapse:collapse;font-size:12px}
 td{padding:2px 0;color:var(--dim)} td.v{text-align:right;color:var(--ink)}
 #hint{position:absolute;top:12px;right:12px;background:rgba(14,18,26,.86);border:1px solid var(--line);
   border-radius:8px;padding:9px 11px;font-size:11.5px;color:var(--dim);max-width:250px}
</style></head><body>
<div id="side">
  <h1>STRATOS — configurateur <b style="color:var(--acc)">GLB</b></h1>
  <div class="sub">chargement à la demande · glTF 2.0 binaire</div>
  <span class="tag" id="stat">chargement…</span>

  <h2>Antenne VTX</h2>
  <select id="antSel">
    <option value="ant_dji">DJI O4</option>
    <option value="ant_rhcp">RHCP LP A1</option>
    <option value="ant_foxeer">Foxeer Lollipop</option>
    <option value="ant_matchstick">TrueRC Matchstick</option>
  </select>

  <h2>Pièces</h2>
  <div id="parts"></div>

  <h2>Vues</h2>
  <button id="bIso">Isométrique</button>
  <div style="height:6px"></div>
  <button id="bTop">Dessus</button>
  <div style="height:6px"></div>
  <button id="bSide">Côté</button>

  <h2>Poids des données</h2>
  <table id="stats"></table>
  <div id="log"></div>
</div>
<div id="view"><div id="hint"><b>Souris :</b> glisser = orbite · molette = zoom.
  Chaque pièce est un <b>.glb</b> séparé chargé à la demande (voir le journal).</div></div>

<script type="importmap">__IMPORTMAP__</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const PLACEMENT = __PLACEMENT__, MOTORS = __MOTORS__;
const logEl = document.getElementById('log');
const log = m => { logEl.textContent += m + "\\n"; logEl.scrollTop = 1e9; };

const view = document.getElementById('view');
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0b0e14);
const camera = new THREE.PerspectiveCamera(42, 1, 0.001, 100); camera.up.set(0,0,1);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
view.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = .08;
controls.minDistance = .05; controls.maxDistance = .9;
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), .04).texture;   // studio IBL
scene.add(new THREE.HemisphereLight(0xbfd3ff, 0x202024, .5));
const key = new THREE.DirectionalLight(0xffffff, 1.9); key.position.set(.2,.26,.5); scene.add(key);
const grid = new THREE.GridHelper(.4, 32, 0x262d38, 0x171c24);
grid.rotation.x = Math.PI/2; scene.add(grid);

const root = new THREE.Group(); scene.add(root);
const D = Math.PI/180, G = {}, loader = new GLTFLoader();
let bytes = 0, files = 0, t0 = performance.now();

function place(obj, p){
  const pos = p.pos || [0,0,0], rot = p.rot || [0,0,0];
  obj.position.set(pos[0]/1000, pos[1]/1000, pos[2]/1000);
  obj.rotation.set(rot[0]*D, rot[1]*D, rot[2]*D);
  return obj;
}
// load one .glb, place it (and clone it per motor for the motor/prop parts)
async function loadPart(name, spec){
  const url = 'parts/' + name + '.glb';
  const gltf = await loader.loadAsync(url);
  const mesh = gltf.scene;
  const g = new THREE.Group(); G[name] = g; root.add(g);
  if (spec.repeat === 'motors'){
    for (const [mx,my] of MOTORS){ const c = mesh.clone(true);
      c.position.set(mx/1000, my/1000, (spec.z||0)/1000); g.add(c); }
  } else { g.add(place(mesh, spec)); }
  if (spec.hidden) g.visible = false;
  files++;
  log(`+ ${name}.glb`);
  return g;
}

const PLAN = Object.assign({}, PLACEMENT, {
  motor: {repeat:'motors', z:3}, prop: {repeat:'motors', z:13.5},
});

(async () => {
  const names = Object.keys(PLAN);
  const settled = await Promise.allSettled(names.map(n => loadPart(n, PLAN[n])));
  const failed = settled.filter(s => s.status === 'rejected').length;
  // real transfer size, straight from the Resource Timing API
  try { for (const e of performance.getEntriesByType('resource'))
    if (e.name.endsWith('.glb')) bytes += (e.encodedBodySize || e.transferSize || 0); } catch(_){}
  const ms = Math.round(performance.now() - t0);
  document.getElementById('stat').textContent =
    `${files} pièces · ${(bytes/1024/1024).toFixed(2)} Mo · ${ms} ms`;
  document.getElementById('stats').innerHTML =
    `<tr><td>Fichiers .glb</td><td class="v">${files}</td></tr>` +
    `<tr><td>Transféré</td><td class="v">${(bytes/1024).toFixed(0)} Ko</td></tr>` +
    `<tr><td>Chargement</td><td class="v">${ms} ms</td></tr>` +
    `<tr><td>Page (shell)</td><td class="v">~${Math.round(document.documentElement.innerHTML.length/1024)} Ko</td></tr>`;
  if (failed) log(`! ${failed} pièce(s) non chargée(s) — servez le dossier en HTTP`);
  buildToggles(); setView('iso');
})();

function buildToggles(){
  const box = document.getElementById('parts');
  for (const k of Object.keys(G).sort()){
    const l = document.createElement('label'); l.className = 'row';
    l.innerHTML = `<input type="checkbox" ${G[k].visible?'checked':''}><span>${k}</span>`;
    l.querySelector('input').addEventListener('change', e => { G[k].visible = e.target.checked; });
    box.appendChild(l);
  }
}
// antenna selector: show exactly one of the antenna GLBs
document.getElementById('antSel').addEventListener('change', e => {
  for (const n of ['ant_dji','ant_rhcp','ant_foxeer','ant_matchstick'])
    if (G[n]) G[n].visible = (n === e.target.value);
  document.querySelectorAll('#parts label.row').forEach(l => {
    const n = l.querySelector('span').textContent;
    if (n.startsWith('ant_')) l.querySelector('input').checked = G[n] && G[n].visible; });
});

const R = .17;
const VIEWS = {iso:[R*.9,R*.95,R*.6], top:[.0001,0,R*1.25], side:[R*1.35,0,R*.2]};
function setView(v){ const p = VIEWS[v]; camera.position.set(p[0],p[1],p[2]);
  controls.target.set(0,0,.018); controls.update(); }
document.getElementById('bIso').onclick = () => setView('iso');
document.getElementById('bTop').onclick = () => setView('top');
document.getElementById('bSide').onclick = () => setView('side');

function resize(){ const w = view.clientWidth, h = view.clientHeight;
  renderer.setSize(w,h); camera.aspect = w/h; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();
(function loop(){ requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();
</script></body></html>
"""


def main():
    html = (TEMPLATE
            .replace("__IMPORTMAP__", importmap())
            .replace("__PLACEMENT__", json.dumps(PLACEMENT, separators=(",", ":")))
            .replace("__MOTORS__", json.dumps(MOTORS, separators=(",", ":"))))
    with open(OUT, "w") as fh:
        fh.write(html)
    print("== configurateur GLB ==")
    print(f"  wrote {os.path.relpath(OUT, REPO)} ({len(html)//1024} KB shell)")
    print(f"  serve: python3 -m http.server -d {os.path.relpath(HERE, REPO)} 8000")
    return 0


if __name__ == "__main__":
    sys.exit(main())
