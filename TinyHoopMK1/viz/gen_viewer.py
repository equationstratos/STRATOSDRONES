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
S3 = os.path.join(REPO, "Stratos3", "cad", "stl")
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
                       o4cam=[0,42,10], o4airunit=[0,0,10],
                       vtxant=[0,-29.5,5.5], rearbay=[0,-32,3], rxant=[0,-33,6],
                       cap=[-8,-24,9], buzzer=[11,-31,6], gps=[0,25,19.2],
                       rx=[0,-22,4], xt30=[0,-25,11], grommet=[0,0,11]),
             standoffs=dict(frame=_FRAME_STAND, board=_BOARD_STAND),
             # ALL screws: 16 motor-mount + 3 frame-standoff tops + 4 board tops
             screws=_MOTOR_SCREWS + _STACK_SCREWS,
             cammount=[0,0,0], side=[13.6, -1, 3, 0.70],            # O4 mount parts are already in frame coords
             # per-group explode offsets (mm along Z, × slider)
             explode=dict(bottom=[0,0,0], top=[0,0,56], standoffs=[0,0,26],
                          camcage=[0,0,40], camera=[0,0,48],
                          cammount_top=[0,26,60], cammount_bottom=[0,20,52],
                          airunit=[0,0,-18], motors=[0,0,-40], props=[0,0,78],
                          elec=[0,0,-30], battery=[0,0,94], screws=[0,0,66],
                          tpu=[0,0,-26], vtxant=[0,0,88], cap=[0,0,-8],
                          rx=[0,0,-15], gps=[0,0,-10], buzzer=[0,0,-12], cables=[0,0,-18]),
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
        "three/addons/geometries/RoundedBoxGeometry.js": v("addons", "geometries", "RoundedBoxGeometry.js"),
    }}, separators=(",", ":"))


TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>__NAME__-001 · 3D</title>
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
  /* ---- mode navigation (Visualisateur / Assemblage / Playground) ---- */
  #modeName,.tagm{font-size:11px;font-weight:600;letter-spacing:.04em;color:var(--acc);
    background:#12283d;border:1px solid #24506f;border-radius:5px;padding:1px 7px;
    margin-left:6px;vertical-align:middle}
  nav#modes,nav#modes2{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin:11px 0 4px}
  .mode{display:flex;flex-direction:column;align-items:center;gap:3px;padding:8px 4px;
    border:1px solid var(--line);border-radius:8px;background:#141a24;color:var(--dim);
    text-decoration:none;font-size:10.5px;font-weight:600;letter-spacing:.02em;
    transition:border-color .15s,background .15s,color .15s}
  .mode:hover{border-color:#33587d;color:var(--ink);background:#182231}
  .mode.active{border-color:var(--acc);background:#12283d;color:var(--ink)}
  .mode .ic{font-size:15px;line-height:1}
  #modeHelp{margin-top:2px;color:var(--dim)}
  /* fullscreen button, floating over the canvas */
  #fs{position:absolute;top:12px;left:12px;z-index:5;background:rgba(14,18,26,.86);
    border:1px solid var(--line);border-radius:8px;color:var(--dim);cursor:pointer;
    padding:7px 11px;font-size:12px}
  #fs:hover{border-color:var(--acc);color:var(--ink)}
  body:fullscreen #side,body:fullscreen #pg{display:none}
  /* assembly simulator (build.html / ?build=1) */
  .bsec{display:none} body.build .bsec{display:block}
  #asmBar{height:7px;background:#0d1219;border:1px solid var(--line);border-radius:5px;
    overflow:hidden;margin:2px 0 7px}
  #asmFill{height:100%;width:0;background:linear-gradient(90deg,var(--acc),#3ddc91);
    transition:width .3s}
  .asm{display:flex;align-items:flex-start;gap:8px;padding:6px 7px;border-radius:6px;
    border:1px solid transparent;cursor:pointer;font-size:12.5px;user-select:none}
  .asm:hover{background:#151b26} .asm.sel{border-color:var(--acc);background:#141d2b}
  .asm.ok{opacity:.5} .asm .d{flex:0 0 9px;height:9px;border-radius:50%;
    background:#2a3547;margin-top:4px}
  .asm.ok .d{background:#3ddc91}
  .asm .tx{display:block;line-height:1.35}
  .asm .tx i{display:block;font-style:normal;color:var(--dim);font-size:11px;margin-top:1px}
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
      <h1><b>__NAME__</b>-001 <span id="modeName">Visualisateur</span></h1>
      <p>__SUB__</p>
      <nav id="modes">
        <a class="mode" data-mode="view"  href="?">
          <span class="ic">◎</span><span>Visualisateur</span></a>
        <a class="mode" data-mode="build" href="?build=1">
          <span class="ic">⚙</span><span>Assemblage</span></a>
        <a class="mode" data-mode="play"  href="?playground=1">
          <span class="ic">▶</span><span>Playground</span></a>
      </nav>
      <p class="mini" id="modeHelp"></p>
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
      <h2>Caméra</h2>
      <select id="camSel" style="width:100%;background:var(--btn);color:var(--ink);
        border:1px solid var(--line);border-radius:6px;padding:7px;font-size:12px">
        <option value="dji">DJI O4 Lite (STEP réel)</option>
        <option value="nano">Nano analogique (type Caddx/RunCam)</option>
      </select>
      <div class="mini" style="margin-top:5px">Lentille AR + bague métal réalistes,
        joint caoutchouc et berceau TPU calés sur la pièce réelle.</div>
    </div>
    <div class="sec">
      <h2>Flancs latéraux</h2>
      <select id="sideSel" style="width:100%;background:var(--btn);color:var(--ink);
        border:1px solid var(--line);border-radius:6px;padding:7px;font-size:12px">
        <option value="a">A — Nervurée (pleine)</option>
        <option value="b">B — Hexa (treillis)</option>
        <option value="c">C — Fentes aéro (racer)</option>
        <option value="d">D — Squelette (léger)</option>
        <option value="e">E — Demi-hauteur</option>
        <option value="f">F — Rail sculpté (photos)</option>
      </select>
      <div class="mini" style="margin-top:5px">Flancs imprimés du Stratos 3, posés
        ici à titre d'essai (échelle 3" — on ajustera).</div>
    </div>
    <div class="sec">
      <h2>Antenne VTX (5,8 GHz)</h2>
      <select id="vtxSel" style="width:100%;background:var(--btn);color:var(--ink);
        border:1px solid var(--line);border-radius:6px;padding:7px;font-size:12px">
        <option value="dji">DJI O4 Pro (antenne, STEP réel)</option>
        <option value="rhcp">RHCP LP A1 (STEP réel)</option>
        <option value="foxeer">Foxeer Lollipop 5,8 GHz (STEP réel)</option>
        <option value="matchstick">TrueRC Singularity / Matchstick</option>
        <option value="microlp">Micro Lollipop U.FL (dôme plein)</option>
      </select>
      <div class="mini" style="margin-top:5px">Insérée dans le TPU arrière, tête vers le haut.</div>
    </div>
    <div class="sec">
      <h2>Électronique</h2>
      <button id="bElec" class="on" style="width:100%">Électronique : STRATOS TINYHOOP AIO</button>
      <div id="bom" class="mini" style="display:none;margin-top:9px">
        <b>Build « standard » — exactement les pièces affichées dans le
        visualisateur :</b>
        <table style="margin-top:5px">
          <tr><td>Châssis</td><td class="v">JeNo Pocket V2 2,5" (carbone, STEP réel) + top plate STRATOS (fente passe-câble)</td></tr>
          <tr><td>FC / ESC</td><td class="v">JHEMCU GHF411 AIO (STEP réel) · ou STRATOS TINYHOOP AIO</td></tr>
          <tr><td>Moteurs</td><td class="v">4× 1104 7500KV (Readytosky) — 3 fils de phase + garde TPU par bras</td></tr>
          <tr><td>Hélices</td><td class="v">Gemfan 2520 (2,5", tri-pale)</td></tr>
          <tr><td>Caméra</td><td class="v">sélecteur : DJI O4 Lite (STEP réel) · nano analogique — objectif M12 type Flywoo Wylde</td></tr>
          <tr><td>Support caméra</td><td class="v">TPU haut + bas, joint caoutchouc, berceau d'objectif, 2 entretoises de cage (or)</td></tr>
          <tr><td>VTX vidéo</td><td class="v">air unit DJI O4 Lite (ou baie analogique 5,8 GHz)</td></tr>
          <tr><td>Antenne VTX</td><td class="v">sélecteur 5 modèles : DJI O4 · RHCP LP A1 · Foxeer Lollipop · TrueRC Matchstick · Micro Lollipop U.FL</td></tr>
          <tr><td>RX</td><td class="v">ELRS 2,4 GHz — PCB en berceau TPU + antenne T horizontale à l'arrière</td></tr>
          <tr><td>Batterie</td><td class="v">DOGCOM 560 mAh 3S 60C (28×52,5×18,5 mm)</td></tr>
          <tr><td>Alim</td><td class="v">XT30 + paire rouge/noir (boucle de service) + prise d'équilibrage JST-XH</td></tr>
          <tr><td>Condensateur</td><td class="v">25 V 22 µF dans son support TPU</td></tr>
          <tr><td>Divers</td><td class="v">GPS / compas · buzzer · visserie M2 · entretoises alu · bumpers TPU</td></tr>
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
    <div class="sec bsec" id="asmSec">
      <h2>Assemblage</h2>
      <div id="asmBar"><div id="asmFill"></div></div>
      <div class="mini" style="margin-bottom:8px"><span id="asmCnt">0</span> /
        <span id="asmTot">0</span> pièces posées — <b>clic</b> = surligner ·
        <b>double-clic</b> = emboîter · glisse-la à la souris.</div>
      <div style="display:flex;gap:6px">
        <button id="asmAll" style="flex:1">Tout assembler</button>
        <button id="asmReset" style="flex:1">Éparpiller</button>
      </div>
      <div style="height:6px"></div>
      <div style="display:flex;gap:6px">
        <button id="asmGhost" style="flex:1">Fantômes : oui</button>
        <button id="asmTidy" style="flex:1">Ranger les pièces</button>
      </div>
      <div class="mini" id="asmHint" style="margin-top:6px;color:var(--acc)"></div>
      <div id="asmList" style="margin-top:9px"></div>
    </div>
    <div class="sec">
      <h2>Spécifications (cible)</h2>
      <table>__SPECS__</table>
    </div>
  </div>

  <div id="pg" class="sidebar">
    <header>
      <h1><b>__NAME__</b>-001 <span class="tagm">Playground</span></h1>
      <p>pilotez le __SUB__ (SDK Tello + clavier)</p>
      <nav id="modes2">
        <a class="mode" data-mode="view"  href="?">
          <span class="ic">◎</span><span>Visualisateur</span></a>
        <a class="mode" data-mode="build" href="?build=1">
          <span class="ic">⚙</span><span>Assemblage</span></a>
        <a class="mode active" data-mode="play" href="?playground=1">
          <span class="ic">▶</span><span>Playground</span></a>
      </nav>
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
    <button id="fs" title="Plein écran (F)">⛶ Plein écran</button>
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
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const STLB64 = __STLS__;   // {frame, canopy, prop, motor}
const M = __MODEL__;       // geometry constants (metres)
const PARAMS = new URLSearchParams(location.search);
const EMBED = PARAMS.has('embed');
const PLAY  = PARAMS.has('playground');
// assembly simulator: on by default in build.html (__BUILD_DEFAULT__), or ?build=1
const BUILD = __BUILD_DEFAULT__ ? !PARAMS.has('nobuild') : PARAMS.has('build');
if (EMBED) document.body.classList.add('embed');
if (PLAY)  document.body.classList.add('play');
if (BUILD) document.body.classList.add('build');

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
try { window.__cam = camera; window.__ctr = controls; } catch(_){}   // for deterministic test views
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
// ---- procedural PBR textures (canvas, NO external files) --------------------
// Real 2x2 twill carbon weave baked into a normal map + a roughness map.
function carbonMaps(){
  const S=256, N=8;                    // N tows across -> repeats every UV unit
  const cn=document.createElement('canvas'); cn.width=cn.height=S;
  const cr=document.createElement('canvas'); cr.width=cr.height=S;
  const n=cn.getContext('2d'), r=cr.getContext('2d');
  n.fillStyle='#8080ff'; n.fillRect(0,0,S,S);            // flat normal base
  r.fillStyle='#6f6f6f'; r.fillRect(0,0,S,S);            // mid roughness base
  const t=S/N;
  for(let j=0;j<N;j++){ for(let i=0;i<N;i++){
    const horiz = (((i+j)>>1) & 1)===0;                  // 2x2 twill float direction
    const x0=i*t, y0=j*t;
    const g = horiz ? n.createLinearGradient(x0,y0, x0, y0+t)
                    : n.createLinearGradient(x0,y0, x0+t, y0);
    g.addColorStop(0,'#8f8fff'); g.addColorStop(.5,'#8080ff'); g.addColorStop(1,'#7373ff');
    n.fillStyle=g; n.fillRect(x0,y0,t,t);                // per-tow micro-tilt
    const rg = horiz ? r.createLinearGradient(x0,y0, x0, y0+t)
                     : r.createLinearGradient(x0,y0, x0+t, y0);
    rg.addColorStop(0,'#8a8a8a'); rg.addColorStop(.5,'#5f5f5f'); rg.addColorStop(1,'#828282');
    r.fillStyle=rg; r.fillRect(x0,y0,t,t);               // woven sheen bands
  }}
  const mk=(cv,lin)=>{ const tx=new THREE.CanvasTexture(cv);
    tx.wrapS=tx.wrapT=THREE.RepeatWrapping; if(lin) tx.colorSpace=THREE.NoColorSpace; return tx; };
  return { normal: mk(cn,true), rough: mk(cr,true) };
}
const CARBON_TEX = carbonMaps();
// planar top-down UVs (mm) so the weave tiles at a real ~5.5 mm pitch on plates
function planarUV(g, pitch){ g.computeBoundingBox();
  const p=g.attributes.position, uv=new Float32Array(p.count*2);
  for(let i=0;i<p.count;i++){ uv[i*2]=p.getX(i)/pitch; uv[i*2+1]=p.getY(i)/pitch; }
  g.setAttribute('uv', new THREE.BufferAttribute(uv,2)); }
// woven-carbon mesh for the flat plates (real weave, subtle gloss)
function carbonMesh(b64, color){
  const g=geo(b64); planarUV(g, 5.5);
  const mat=new THREE.MeshStandardMaterial({color, metalness:.22, roughness:.46,
    normalMap:CARBON_TEX.normal, normalScale:new THREE.Vector2(.4,.4),
    roughnessMap:CARBON_TEX.rough});
  const m=new THREE.Mesh(g, mat); m.scale.setScalar(0.001); return m;
}

// ---- the drone: ONE group whose origin is the ground under its centre ----
// (the playground moves/clones this group; feet touch z=0)
const frameRoot = new THREE.Group(); scene.add(frameRoot);
const G = {}; try { window.G = G; window.THREE = THREE; } catch(_){}   // exposed for measurement/debug
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
const gBottom = group('bottom'); { const m=carbonMesh(STLB64.frame_bottom, CARBON);
  m.position.z=M.frame_z; gBottom.add(m); }
const gTop = group('top'); { const m=carbonMesh(STLB64.frame_top, CARBON);
  m.position.z=M.frame_z; gTop.add(m); }        // STRATOS top plate
// clean aluminium standoffs — SMOOTH turned posts (procedural, 40 segments)
// instead of the faceted STL: 3 tall frame posts (z3→17) + 4 short board posts.
const gStand = group('standoffs');
const aluMat = new THREE.MeshStandardMaterial({color:0xc2c5cb, metalness:.92, roughness:.26});
function standoff(x,y,base,h,r){
  const m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h/1000,40,1), aluMat);
  m.rotation.x=Math.PI/2; m.position.set(x/1000, y/1000, (base+h/2)/1000);   // vertical
  gStand.add(m); return m; }
for (const [x,y] of M.standoffs.frame) standoff(x,y, 3, 14, 0.0021);   // tall frame posts
for (const [x,y] of M.standoffs.board) standoff(x,y, 3,  3, 0.0021);   // short board posts
const gCage = group('camcage'); { const m=carbonMesh(STLB64.camcage, CARBON);
  m.position.z=M.frame_z; gCage.add(m); }
// camera-cage cross standoffs — the 2 GOLD anodized bars (top + bottom) that tie
// the two carbon cage plates together, behind the TPU camera mounts (real JeNo
// detail: visible once the TPU supports are hidden). Own toggle group.
const gCageStd = group('cagestd');
{ const gold=new THREE.MeshStandardMaterial({color:0xd8a520, metalness:.88, roughness:.26});
  const bar=(y,z)=>{ const m=new THREE.Mesh(new THREE.CylinderGeometry(0.0016,0.0016,0.0168,32,1), gold);
    m.rotation.z=Math.PI/2;                                   // axis along X (plate to plate)
    m.position.set(0, y/1000, z/1000); gCageStd.add(m);
    for (const s of [-1,1]){ const cap=new THREE.Mesh(                 // steel screw heads (inside the cage)
        new THREE.CylinderGeometry(0.0021,0.0021,0.0014,20), aluMat);
      cap.rotation.z=Math.PI/2; cap.position.set(s*8.0/1000, y/1000, z/1000); gCageStd.add(cap); } };
  bar(45, 29);                                                // top bar (replaces the cropped STL bar)
  bar(55, 8);                                                 // bottom bar (replaces the cropped STL bar)
}
// ---- realistic FPV lens assembly (shared): a Flywoo-Wylde-style M12 THREADED
// BARREL with a CONVEX AR-coated dome (as on a DJI O4 with an aftermarket lens).
// Lens axis = +Y (nose); the barrel base (y<0) plugs into the camera body. ----
function buildLens(){
  const grp=new THREE.Group();
  const blk=new THREE.MeshStandardMaterial({color:0x0c0c0f, metalness:.4, roughness:.42});
  // main threaded barrel (M12) protruding forward
  const barrel=new THREE.Mesh(new THREE.CylinderGeometry(0.0056,0.0059,0.0110,48), blk);
  barrel.position.y=-0.0030; grp.add(barrel);
  const thr=new THREE.MeshStandardMaterial({color:0x18181b, metalness:.45, roughness:.5});
  for(let i=0;i<7;i++){ const gr=new THREE.Mesh(new THREE.TorusGeometry(0.00585,0.00042,10,48), thr);
    gr.rotation.x=Math.PI/2; gr.position.y=-0.0078+i*0.0015; grp.add(gr); }   // thread grooves
  // dark metallic front rim holding the glass
  const rim=new THREE.Mesh(new THREE.CylinderGeometry(0.0061,0.0059,0.0020,48),
    new THREE.MeshStandardMaterial({color:0x2b2e33, metalness:.75, roughness:.32}));
  rim.position.y=0.0026; grp.add(rim);
  // CONVEX domed glass (fisheye), AR-coated with iridescent sheen
  const glass=new THREE.Mesh(new THREE.SphereGeometry(0.0052,48,30,0,Math.PI*2,0,Math.PI*0.46),
    new THREE.MeshPhysicalMaterial({color:0x0a0a12, metalness:.15, roughness:.03,
      clearcoat:1, clearcoatRoughness:.03, iridescence:1, iridescenceIOR:1.9,
      iridescenceThicknessRange:[130,420]}));
  glass.scale.set(1,0.32,1); glass.position.y=0.0026; grp.add(glass);         // nearly-flat glass
  return grp;
}
// procedural NANO analog camera body (à la Caddx/RunCam nano) — a small dark
// housing + sensor board sitting BEHIND the shared lens; front faces +Y.
function buildNanoCam(){
  const grp=new THREE.Group();
  const body=new THREE.Mesh(new THREE.BoxGeometry(0.0140,0.0120,0.0140),
    new THREE.MeshStandardMaterial({color:0x141519, metalness:.35, roughness:.55}));
  grp.add(body);
  const pcb=new THREE.Mesh(new THREE.BoxGeometry(0.0132,0.0012,0.0132),
    new THREE.MeshStandardMaterial({color:0x11532e, metalness:.2, roughness:.6}));
  pcb.position.y=-0.0068; grp.add(pcb);                       // sensor board at the back
  return grp;
}
// Camera at the nose — SELECTABLE (DJI O4 Lite STEP or nano analog), with the
// realistic shared lens + the adjustable rubber gasket.
const camModels = {}; let camCur = 'dji';
const gCam = (()=>{ const g = group('camera');
  g.position.set(0, 42/1000, 20/1000);               // pivot at camera centre
  g.userData.base = g.position.clone();
  // DJI O4 Lite STEP body (dark, closer to the real black housing)
  const dji=mesh(STLB64.o4cam, 0x24272c,.5,.4); dji.rotation.z=Math.PI/2;
  dji.position.set(0, 0, -10/1000);                  // = o4cam world minus pivot
  const djiG=new THREE.Group(); djiG.add(dji); camModels.dji=djiG; g.add(djiG);
  // nano analog body, seated just behind the shared lens
  const nanoG=buildNanoCam(); nanoG.position.set(0, 3.5/1000, -1/1000);
  nanoG.visible=false; camModels.nano=nanoG; g.add(nanoG);
  // shared realistic lens at the lens centre (in front of whichever body)
  const lens=buildLens(); lens.position.set(0, 11.4/1000, -1/1000); g.add(lens);
  // rubber seal — a FLAT ring that fills the whole gap between the camera and
  // the top/bottom TPU supports (no empty space), yet stays inside the cage
  // (outer < 9.1 mm). Adjustable (own group 'gasket').
  const gInner=0.0062, gOuter=0.0090, gThick=0.0007;
  const shp=new THREE.Shape(); shp.absarc(0,0,gOuter,0,Math.PI*2,false);
  const gh=new THREE.Path(); gh.absarc(0,0,gInner,0,Math.PI*2,true); shp.holes.push(gh);
  const rub=new THREE.Mesh(new THREE.ExtrudeGeometry(shp,{depth:gThick,bevelEnabled:true,
    bevelThickness:0.00014,bevelSize:0.00014,bevelSegments:1,curveSegments:56}),
    new THREE.MeshStandardMaterial({color:0x0b0b0d, metalness:0.0, roughness:0.97}));
  rub.rotation.x = -Math.PI/2;
  const gsk = new THREE.Group();
  gsk.add(rub); gsk.position.set(0, 10.6/1000, -1/1000);
  gsk.userData.base = gsk.position.clone(); G['gasket'] = gsk; g.add(gsk);
  // TPU CRADLE — a slim closed tube that just WRAPS the lens barrel (compact,
  // like the printed Flywoo-Wylde mount); sized to stay INSIDE the carbon cage
  // (no side overhang). Adjustable ('bezel').
  const bInner=0.0063, bOuter=0.0078, bDepth=0.0090;
  const bsh=new THREE.Shape(); bsh.absarc(0,0,bOuter,0,Math.PI*2,false);
  const bhl=new THREE.Path(); bhl.absarc(0,0,bInner,0,Math.PI*2,true); bsh.holes.push(bhl);
  const bezM=new THREE.Mesh(new THREE.ExtrudeGeometry(bsh,{depth:bDepth,bevelEnabled:true,
    bevelThickness:0.0005,bevelSize:0.0005,bevelSegments:2,curveSegments:64}),
    new THREE.MeshStandardMaterial({color:0x24272d, metalness:0.04, roughness:0.86}));
  bezM.rotation.x = -Math.PI/2;
  const bez = new THREE.Group();
  bez.add(bezM); bez.position.set(0, 2.2/1000, -1/1000);   // wraps the barrel length
  bez.userData.base = bez.position.clone(); G['bezel'] = bez; g.add(bez);
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
// NEW integrated rear TPU bay (replaces the crossing vtx_antenna_mount): holds
// the VTX antenna angled-up + the RX antenna out the back, all in the footprint
{ const rb = mesh(STLB64.rear_bay, 0x2b2f36, .1, .85);
  rb.rotation.z = Math.PI;                                        // its rear faces the drone rear (-Y)
  rb.position.set(M.elec.rearbay[0]/1000, M.elec.rearbay[1]/1000, M.elec.rearbay[2]/1000);
  gTpu.add(rb); }
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
// DOGCOM 560 mAh 3S pack — a clean procedural box with a printed label texture
// (silver foil top, black band, gold DOGCOM + yellow specs). No moulded text
// spilling off the block. Sized/placed on the real STL envelope (28x52.5x18.5).
{ const W=600,H=320, cv=document.createElement('canvas'); cv.width=W; cv.height=H;
  const x=cv.getContext('2d');
  x.fillStyle='#0c0c0e'; x.fillRect(0,0,W,H);                      // all-black wrap label
  x.textBaseline='middle';
  x.fillStyle='#e6b53c'; x.font='italic bold 104px Arial';
  x.fillText('DOGCOM', W*0.16, H*0.42);                            // gold brand
  x.fillStyle='#f4d64a'; x.font='bold 60px Arial'; x.fillText('560', W*0.20, H*0.72);
  x.font='bold 34px Arial'; x.fillText('MAH', W*0.36, H*0.73);
  x.fillStyle='#dcdcde'; x.font='bold 27px Arial'; x.fillText('11.1V 3S  ·  60C', W*0.55, H*0.72);
  x.fillStyle='#8d8d90'; x.font='17px Arial'; x.fillText('www.titltop.com', W*0.62, H*0.90);
  x.fillStyle='#e6b53c'; x.beginPath(); x.ellipse(W*0.075,H*0.40,34,29,0,0,Math.PI*2); x.fill();
  x.fillStyle='#0c0c0e'; x.font='bold 26px Arial'; x.fillText('DC', W*0.043, H*0.43);   // bee badge
  const lab=new THREE.CanvasTexture(cv); lab.colorSpace=THREE.SRGBColorSpace; lab.anisotropy=8;
  const bw=0.028, bl=0.0525, bh=0.0185, cx=0, cy=3.75/1000, cz=33.2/1000, eps=0.00025;
  // black shrink-wrap body with ROUNDED corners (matte, wraps the whole block)
  const black=new THREE.MeshStandardMaterial({color:0x0d0d10, metalness:.12, roughness:.62});
  const body=new THREE.Mesh(new RoundedBoxGeometry(bw,bl,bh, 5, 0.0022), black);
  body.position.set(cx,cy,cz); gBatt.add(body);
  // printed DOGCOM label on the TOP face only (dessus) — sides stay plain black
  const labMat=new THREE.MeshStandardMaterial({map:lab, metalness:.15, roughness:.5});
  { const p=new THREE.Mesh(new THREE.PlaneGeometry(bl-0.003, bw-0.003), labMat);
    p.position.set(cx, cy, cz + bh/2 + eps);      // flat on top, facing +Z
    p.rotation.z = Math.PI/2;                     // text reads along the pack length
    gBatt.add(p); }
  // silver foil exposed at the 2 ends (±Y) — the wrap doesn't cover them
  const silver=new THREE.MeshStandardMaterial({color:0xc4c6ca, metalness:.55, roughness:.32});
  for (const sy of [-1,1]){ const e=new THREE.Mesh(new THREE.PlaneGeometry(bw-0.004, bh-0.003), silver);
    e.position.set(cx, cy+sy*(bl/2+eps), cz); e.rotation.set(sy>0?-Math.PI/2:Math.PI/2, 0, 0);
    gBatt.add(e); } }
// M2 screws on the real standoffs + camera plates
const gScrew = group('screws');
for (const s of M.screws){ const sc = place(STLB64.screw, 0xd6d9de, .9, .25, s);
  gScrew.add(sc); }
// 4 stack screws capping the VTX-on-FC soft-mount at the board corners
for (const [x,y] of M.standoffs.board){
  const sc = place(STLB64.screw, 0xd6d9de, .9, .25, [x, y, M.elec.o4airunit[2]+3]);
  gScrew.add(sc); }
// 5.8 GHz VTX antenna in the rear TPU mount — SELECTABLE among 3 real models,
// HEAD UP (only the chosen one is visible; dropdown in the sidebar).
const gVtxAnt = group('vtxant');                         // parent: toggle + colour
// Each model gets its OWN pivot group at the antenna base so the fine-adjust
// panel can translate/rotate them ONE BY ONE (moving the DJI must not move the
// RHCP, which is already well seated). Only one group is visible at a time.
// mark a mesh so the colour picker leaves it alone (coax, gold plugs, …)
function keep(m){ m.userData.keepColor = true; return m; }
function vtxPivot(key, m){
  const g = new THREE.Group();
  g.position.set(M.elec.vtxant[0]/1000, M.elec.vtxant[1]/1000,
                 M.frame_z + M.elec.vtxant[2]/1000);     // origin = antenna base
  g.add(m);                                              // mesh sits at group origin
  g.userData.base = g.position.clone();
  g.visible = false; G['vtx_'+key] = g; gVtxAnt.add(g);
  return g;
}
// ---- real lollipop-style FPV antenna, built to the photos -------------------
// A COLOURED CAPSULE HEAD (cylinder with a rounded top and a small lip) on a
// black flexible coax stem, a thicker heatshrink sleeve, and a gold connector.
// Only the head takes the colour picker: every other mesh is flagged keepColor.
// Base at z=0, head up (+Z), metres.
function buildLollipopAnt(o){
  const headR = o.headR, headH = o.headH, stem = o.stem, shrink = o.shrink;
  const grp = new THREE.Group();
  const capMat  = new THREE.MeshStandardMaterial({color:o.color, metalness:.18, roughness:.34});
  const blkMat  = new THREE.MeshStandardMaterial({color:0x0b0b0d, metalness:.15, roughness:.62});
  const shrMat  = new THREE.MeshStandardMaterial({color:0x141416, metalness:.10, roughness:.78});
  const goldMat = new THREE.MeshStandardMaterial({color:0xc9a227, metalness:.95, roughness:.24});
  const fixed = m => { m.userData.keepColor = true; return m; };   // colour picker skips these
  const tube = (r, h, z, m) => { const k = new THREE.Mesh(
      new THREE.CylinderGeometry(r, r, h, 24), m);
    k.rotation.x = Math.PI/2; k.position.z = z; grp.add(k); return k; };

  // gold connector (SMA barrel or the small U.FL plug)
  if (o.conn === 'sma'){
    fixed(tube(0.0032, 0.0075, 0.0037, goldMat));
    fixed(tube(0.0021, 0.0030, 0.0090, goldMat));
  } else {
    fixed(tube(0.0018, 0.0032, 0.0016, goldMat));
  }
  const z0 = (o.conn === 'sma') ? 0.0105 : 0.0032;
  fixed(tube(0.0016, shrink, z0 + shrink/2, shrMat));          // heatshrink sleeve
  const zs = z0 + shrink;
  fixed(tube(0.00092, stem, zs + stem/2, blkMat));             // flexible coax stem
  // the capsule head: lathe profile = flat bottom, straight wall, rounded top
  const pts = [], zTop = headH, rr = headR*0.62;               // rr = top round-over
  pts.push(new THREE.Vector2(0, 0));
  pts.push(new THREE.Vector2(headR, 0));
  pts.push(new THREE.Vector2(headR, zTop - rr));
  for (let i = 1; i <= 8; i++){ const a = (i/8) * Math.PI/2;   // quarter-round top
    pts.push(new THREE.Vector2((headR-rr) + Math.cos(a)*rr, (zTop-rr) + Math.sin(a)*rr)); }
  const head = new THREE.Mesh(new THREE.LatheGeometry(pts, 40), capMat);
  head.rotation.x = Math.PI/2;            // LatheGeometry spins about Y -> stand it up on Z
  head.position.z = zs + stem; grp.add(head);                  // colourable head
  // thin dark lip at the base of the cap, as on the real part
  fixed(tube(headR*1.02, 0.0009, zs + stem + 0.00045, shrMat));
  return grp;
}
const vtxModels = {
  dji:        vtxPivot('dji',        mesh(STLB64.dji_pro_ant, 0x0f1114, .2, .5)),  // DJI O4 Pro antenna
  // REAL Foxeer Lollipop 5.8 SMA (owner's STEP), split into head / stem / connector
  // so the colour picker only repaints the HEAD, like the real red cap.
  foxeer:     vtxPivot('foxeer',     (()=>{ const g = new THREE.Group();
                g.add(mesh(STLB64.foxeer_head, 0xc4161c, .18, .34));            // red cap
                g.add(keep(mesh(STLB64.foxeer_stem, 0x0b0b0d, .15, .62)));      // coax stem
                g.add(keep(mesh(STLB64.foxeer_conn, 0xc9a227, .95, .24)));      // gold SMA
                return g; })()),
  rhcp:       vtxPivot('rhcp',       mesh(STLB64.rhcp_lp,     0x141414, .2, .5)),  // RHCP LP A1 (STEP)
  matchstick: vtxPivot('matchstick', mesh(STLB64.matchstick,  0x181818, .2, .5)),  // TrueRC Singularity
  microlp:    vtxPivot('microlp',    buildLollipopAnt({headR:0.0050, headH:0.0120,
                stem:0.018, shrink:0.007, conn:'ufl', color:0xc4161c})),   // micro lollipop U.FL
};
let vtxCur='dji'; vtxModels[vtxCur].visible=true;         // default: the DJI antenna
// (the 28° seating tilt is carried by the fine-adjust DEF below, applied at load)
// Show ONE VTX model and keep BOTH dropdowns (model + fine-adjust) in step, so
// picking an antenna to adjust always makes that same antenna visible.
function showVtxModel(key){
  if (!vtxModels[key]) return;
  if (vtxModels[vtxCur]) vtxModels[vtxCur].visible = false;
  vtxCur = key; vtxModels[key].visible = true;
  const s = document.getElementById('vtxSel'); if (s) s.value = key;
}
// LiPo capacitor (25 V 22 µF, Ø6×12) SEATED IN ITS PRINTED TPU HOLDER
// Capacitor LAID DOWN (axis along Y) so the Ø6x18.4 can fits BETWEEN the plates
// instead of standing proud of the frame. Holder rotated with it.
// ---- side panels (flancs imprimés, 5 variantes) --------------------------
// Two mirrored copies flanking the body, seated between the plates. The picker
// swaps which variant is visible; only one pair is shown at a time.
const gSide = group('side');
const sideModels = {};
{ const src = {a:STLB64.sp_a, b:STLB64.sp_b, c:STLB64.sp_c, d:STLB64.sp_d, e:STLB64.sp_e, f:STLB64.sp_f};
  for (const k in src){
    const g = new THREE.Group();
    for (const sx of [-1,1]){
      const m = mesh(src[k], 0x2b2f36, .06, .82);
      m.rotation.z = Math.PI/2;                       // panel runs along the body (Y)
      m.scale.multiplyScalar(M.side[3]);              // 3" part previewed at 2.5" scale
      m.position.set(sx*(M.side[0])/1000, M.side[1]/1000, M.frame_z + M.side[2]/1000);
      g.add(m);
    }
    g.visible = false; sideModels[k] = g; gSide.add(g);
  }
}
let sideCur = 'a'; sideModels[sideCur].visible = true;
const gCap = group('cap');
{ const c = M.elec.cap;
  const holder = place(STLB64.cap_holder, TPU, .1, .85, c);
  holder.rotation.x = -Math.PI/2; gCap.add(holder);                 // TPU clip, on its side
  const can = place(STLB64.cap, 0x1b3a8f, .25, .45, [c[0], c[1], c[2]+0.6]);
  can.rotation.x = -Math.PI/2; gCap.add(can); }                     // the can, lying flat
// ---- a swept round tube between two points (mm) — for wires ----
function wireTube(p0, p1, r, col){
  const pts=[new THREE.Vector3(p0[0]/1000,p0[1]/1000,p0[2]/1000),
             new THREE.Vector3((p0[0]+p1[0])/2000,(p0[1]+p1[1])/2000,(Math.max(p0[2],p1[2])+4)/1000),
             new THREE.Vector3(p1[0]/1000,p1[1]/1000,p1[2]/1000)];
  const c=new THREE.CatmullRomCurve3(pts);
  return new THREE.Mesh(new THREE.TubeGeometry(c,20,r/1000,8,false),
    new THREE.MeshStandardMaterial({color:col, metalness:.1, roughness:.55}));
}
// each accessory is its OWN group now, so it can be shown/hidden one by one.
const gBuz = group('buzzer');
gBuz.add(place(STLB64.buzzer, 0x141519, .3, .5, M.elec.buzzer));    // Ø8 buzzer
const gGps = group('gps');
gGps.add(place(STLB64.gps, 0x0a0c10, .2, .5, M.elec.gps));          // GPS/compass
// ELRS RX: the PCB centred in the footprint + the antenna out the rear-bay sleeve
const gRx = group('rx');
gRx.add(place(STLB64.rx_holder, TPU, .1, .85, M.elec.rx));          // TPU tray
gRx.add(place(STLB64.rx_pcb, 0x0f3d0f, .2, .5,
  [M.elec.rx[0], M.elec.rx[1], M.elec.rx[2]+1.6]));                 // RX board
// RX antenna in its OWN pivot group (base = sleeve exit) so it too is fine-
// adjustable one-by-one; the ~87° tilt (horizontal, out the back) is the DEF.
{ const g = group('rxant');
  g.add(mesh(STLB64.rx, 0x141414, .25, .5));                       // mesh at group origin
  g.position.set(M.elec.rxant[0]/1000, M.elec.rxant[1]/1000,
                 M.frame_z + M.elec.rxant[2]/1000);
  g.userData.base = g.position.clone(); gRx.add(g); }              // reparent under RX toggle
// BATTERY HARNESS — added to the BATTERY group so it shows/hides WITH the pack.
// Clean DOGCOM-style leads: a red+black pair to an XT30 + a white JST-XH balance
// plug, rooted right at the (cropped) rear face of the pack so they connect.
{ const xt = M.elec.xt30, bt = M.elec.battery;
  const RED=0xcf2128, BLK=0x121214;
  const lead=(p0,p1,r,col,sag)=>{
    const m=[(p0[0]+p1[0])/2,(p0[1]+p1[1])/2,Math.max(p0[2],p1[2])+(sag||0)];
    const c=new THREE.CatmullRomCurve3([new THREE.Vector3(p0[0]/1000,p0[1]/1000,p0[2]/1000),
      new THREE.Vector3(m[0]/1000,m[1]/1000,m[2]/1000),
      new THREE.Vector3(p1[0]/1000,p1[1]/1000,p1[2]/1000)]);
    return new THREE.Mesh(new THREE.TubeGeometry(c,28,r/1000,12,false),
      new THREE.MeshStandardMaterial({color:col,metalness:.05,roughness:.5})); };
  const root=[0, bt[1]-26, bt[2]+4];              // pack rear face (after crop)
  const body=new THREE.Mesh(new THREE.BoxGeometry(0.0090,0.0080,0.0070),
    new THREE.MeshStandardMaterial({color:0xf2b400, metalness:.15, roughness:.45}));
  body.position.set(xt[0]/1000, xt[1]/1000, xt[2]/1000); gBatt.add(body);   // XT30
  for (const s of [-1,1]){ const cup=new THREE.Mesh(new THREE.CylinderGeometry(0.0012,0.0012,0.0042,16),
      new THREE.MeshStandardMaterial({color:0xcaa63a, metalness:.9, roughness:.25}));
    cup.rotation.x=Math.PI/2; cup.position.set((xt[0]+s*2.2)/1000,(xt[1]-4.4)/1000,xt[2]/1000); gBatt.add(cup); }
  // main power pair — a REALISTIC service loop: thick silicone leads are stiff,
  // so they can't hug the pack; they bow rearward on a large radius, crest, then
  // drop back down through the plate slot into the XT30.
  const bend=(pts,r,col)=>new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(
      pts.map(p=>new THREE.Vector3(p[0]/1000,p[1]/1000,p[2]/1000))), 44, r/1000, 12, false),
    new THREE.MeshStandardMaterial({color:col, metalness:.05, roughness:.5}));
  const mains=(x,col)=>bend([
    [x,        bt[1]-26, bt[2]+3],   // exit the pack rear face
    [x*1.25,   bt[1]-33, bt[2]+6],   // bow rearward + up (wire stiffness arc)
    [x*1.25,   bt[1]-35, bt[2]-3],   // crest of the loop, clear of the pack
    [x,        bt[1]-30, xt[2]+4],   // come back in, dropping toward the slot
    [x,        xt[1]+1,  xt[2]+1]    // into the XT30
  ], 1.35, col);
  gBatt.add(mains( 2.4, RED));
  gBatt.add(mains(-2.4, BLK));
  // white JST-XH balance plug (3S = 4-pin) + 4 thin balance wires
  const bal=new THREE.Mesh(new THREE.BoxGeometry(0.0075,0.0032,0.0040),
    new THREE.MeshStandardMaterial({color:0xededf0, metalness:.0, roughness:.7}));
  bal.position.set(6.5/1000,(bt[1]-23)/1000,(bt[2]+3)/1000); gBatt.add(bal);
  const bcol=[BLK,RED,0xe0a828,0x2b8a2b];         // black, red, yellow, green
  for (let i=0;i<4;i++) gBatt.add(lead([3.2, root[1], root[2]],
    [4.7+i*1.2, bt[1]-23, bt[2]+3], 0.42, bcol[i], 1.2+i*0.3));
}
// motor phase cables — their OWN toggle group ('cables'): 3 phase wires per
// motor routed along the arm to the FC, each arm capped by a TPU guard so the
// prop can't slice them.
const gCbl = group('cables');
{ const armTube=(p0,p1,r,col)=>{
    const c=new THREE.CatmullRomCurve3([new THREE.Vector3(p0[0]/1000,p0[1]/1000,p0[2]/1000),
      new THREE.Vector3((p0[0]+p1[0])/2000,(p0[1]+p1[1])/2000,((p0[2]+p1[2])/2+0.8)/1000),
      new THREE.Vector3(p1[0]/1000,p1[1]/1000,p1[2]/1000)]);
    return new THREE.Mesh(new THREE.TubeGeometry(c,20,r/1000,8,false),
      new THREE.MeshStandardMaterial({color:col,metalness:.12,roughness:.5})); };
  for (const [mx,my] of M.motors){
    const L=Math.hypot(mx,my), px=-my/L, py=mx/L;            // perp to the arm
    const mb=[mx-mx/L*7, my-my/L*7, 5];                      // just inboard of the bell
    const fc=[mx*0.30, my*0.30, 6];                          // FC solder pads
    for (let i=-1;i<=1;i++){                                 // 3 phase wires
      const s=[mb[0]+px*i*1.4, mb[1]+py*i*1.4, mb[2]];
      const e=[fc[0]+px*i*1.4, fc[1]+py*i*1.4, fc[2]];
      gCbl.add(armTube(s,e,0.65, 0x17181b)); }
    const gx=mx*0.62, gy=my*0.62;                            // TPU cable guard, mid-arm
    const guard=new THREE.Mesh(new THREE.BoxGeometry(0.0075,0.0052,0.0034),
      new THREE.MeshStandardMaterial({color:0x2b2f36,metalness:.05,roughness:.85}));
    guard.position.set(gx/1000, gy/1000, 6.2/1000); guard.rotation.z=Math.atan2(my,mx);
    gCbl.add(guard); }
}

// ---- part toggles + per-part colour pickers ----
const GROUPS = {
  bottom:   {label:'Plaque basse (carbone réel)', color:'#1a1d21'},
  top:      {label:'Plaque haute (JeNo, sans texte)', color:'#1a1d21'},
  standoffs:{label:'Entretoises', color:'#b9bcc2'},
  camcage:  {label:'Cage caméra (carbone)', color:'#1a1d21'},
  cagestd:  {label:'Entretoises cage caméra (or)', color:'#d8a520'},
  camera:   {label:'Caméra DJI O4 Lite', color:'#121316'},
  airunit:  {label:'Air unit DJI O4 Lite (PCB nue)', color:'#11532e'},
  cammount_top:    {label:'Support caméra HAUT (TPU)', color:'#2b2f36'},
  cammount_bottom: {label:'Support caméra BAS (TPU)', color:'#2b2f36'},
  tpu:      {label:'Protections TPU (bumpers)', color:'#2b2f36'},
  motors:   {label:'Moteurs 1104 (Readytosky)', color:'#3a3d43'},
  props:    {label:'Hélices 2,5" (2520)',  color:'#d8721e'},
  elec:     {label:'Carte AIO (STRATOS / GHF411)', color:'#0b6b39'},
  battery:  {label:'Batterie 3S 560 mAh (DOGCOM)', color:'#83868c'},
  screws:   {label:'Visserie M2 (moteurs + stack)', color:'#d6d9de'},
  vtxant:   {label:'Antenne VTX 5,8 GHz (sélecteur)', color:'#1c1c1e'},
  side:     {label:'Flancs latéraux (sélecteur)', color:'#2b2f36'},
  cap:      {label:'Condensateur 25 V 22 µF (support TPU)', color:'#1b3a8f'},
  rx:       {label:'Récepteur RX (PCB + antenne)', color:'#0f3d0f'},
  gps:      {label:'GPS / compas', color:'#0a0c10'},
  buzzer:   {label:'Buzzer', color:'#141519'},
  cables:   {label:'Câbles moteurs (phases)', color:'#2a2c30'},
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
// recolour a group — meshes flagged keepColor (coax, heatshrink, gold plugs,
// gold cage bars…) keep their real colour, so e.g. only an antenna's HEAD changes.
function setColor(g, hex){ if(!hex||!G[g]) return; const col=new THREE.Color(hex);
  G[g].traverse(o=>{ if(o.isMesh && !o.userData.keepColor) o.material.color.copy(col); }); }
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
// VTX antenna model selector — swap which mesh is visible AND point the
// fine-adjust panel at the same antenna (so its sliders act on what you see).
{ const sel=document.getElementById('vtxSel'); if(sel){ sel.value=vtxCur;
  sel.addEventListener('change',e=>{ showVtxModel(e.target.value);
    if (window.__pickAntenna) window.__pickAntenna('vtx_'+e.target.value); }); } }
// side-panel variant selector
{ const sel=document.getElementById('sideSel'); if(sel){ sel.value=sideCur;
  sel.addEventListener('change',e=>{ if(sideModels[sideCur])sideModels[sideCur].visible=false;
    sideCur=e.target.value; if(sideModels[sideCur])sideModels[sideCur].visible=true; }); } }
// camera model selector — swap DJI STEP body vs nano analog body
{ const sel=document.getElementById('camSel'); if(sel){ sel.value=camCur;
  sel.addEventListener('change',e=>{ if(camModels[camCur])camModels[camCur].visible=false;
    camCur=e.target.value; if(camModels[camCur])camModels[camCur].visible=true; }); } }
document.getElementById('bElec').addEventListener('click', ()=>{
  stdElec=!stdElec; applyElec(stdElec);
});
// ---- per-part fine-adjust: translate + rotate the chosen part about its pivot ----
// DEF = the alignment the owner dialled in; it is applied at load and is the
// "reset" target, so the nose is correctly seated out of the box.
// The camera + mounts keep their dialled-in seating (applied at load, not
// user-editable here anymore); the panel now drives the antennas one-by-one.
(function(){ const DEF = { camera:  {x:0, y:-5,  z:-6,   rx:27, ry:0, rz:0},
                cammount_top:   {x:0, y:-2,  z:-1,   rx:-6, ry:0, rz:0},
                cammount_bottom:{x:0, y:4.5, z:-1.5, rx:-5, ry:0, rz:0},
                vtx_dji:        {x:0, y:-29,   z:48.5, rx:-147, ry:0, rz:0},
                vtx_rhcp:       {x:0, y:0,     z:0,    rx:28,   ry:0, rz:0},
                vtx_foxeer:     {x:0, y:0,     z:0,    rx:28,   ry:0, rz:0},
                vtx_matchstick: {x:0, y:0,   z:0,    rx:28, ry:0, rz:0},
                vtx_microlp:    {x:0, y:0,   z:0,    rx:28, ry:0, rz:0},
                rxant:          {x:0, y:0,   z:0,    rx:87, ry:0, rz:0, s:62},
                gasket:         {x:0, y:-1,  z:1,    rx:-27, ry:0, rz:0, s:100},
                bezel:          {x:0, y:0,   z:0,    rx:0,  ry:0, rz:0, s:100} };
  const cp = o => Object.assign({}, o);
  const off = {}; for (const k in DEF) off[k] = cp(DEF[k]);
  const SEAT = ['camera','cammount_top','cammount_bottom'];   // applied, not in the dropdown
  const el = id => document.getElementById(id);
  const D = Math.PI/180;
  const applyTarget = (t)=>{ const o=off[t]; const g=G[t];
    if (g){ const b = g.userData.base || new THREE.Vector3();
      g.position.set(b.x + o.x/1000, b.y + o.y/1000, b.z + o.z/1000);
      g.rotation.set(o.rx*D, o.ry*D, o.rz*D);
      g.scale.setScalar((o.s==null?100:o.s)/100);      // size slider
      g.userData.home = g.position.clone(); } };
  // the sliders panel was removed from the UI; the DEF values below are still
  // what SEATS the camera, mounts, gasket and antennas at load.
  if (!el('camTarget')){ Object.keys(DEF).forEach(applyTarget); return; }
  const applyCam = ()=>{
    const t = el('camTarget').value; const o = off[t]; applyTarget(t);
    const s = (o.s==null?100:o.s);
    el('camXV').textContent = o.x.toFixed(1)+' mm';
    el('camYV').textContent = o.y.toFixed(1)+' mm';
    el('camZV').textContent = o.z.toFixed(1)+' mm';
    el('camRXV').textContent = o.rx+'°';
    el('camRYV').textContent = o.ry+'°';
    el('camRZV').textContent = o.rz+'°';
    el('camSV').textContent = s+'%';
    el('camDelta').textContent = t+' : X '+o.x+' · Y '+o.y+' · Z '+o.z
      +' · RX '+o.rx+' · RY '+o.ry+' · RZ '+o.rz+' · S '+s;
  };
  const bind = (id, k)=> el(id).addEventListener('input', e=>{
    off[el('camTarget').value][k] = +e.target.value; applyCam(); });
  bind('camX','x'); bind('camY','y'); bind('camZ','z');
  bind('camRX','rx'); bind('camRY','ry'); bind('camRZ','rz'); bind('camS','s');
  const sync = ()=>{ const o=off[el('camTarget').value];
    el('camX').value=o.x; el('camY').value=o.y; el('camZ').value=o.z;
    el('camRX').value=o.rx; el('camRY').value=o.ry; el('camRZ').value=o.rz;
    el('camS').value=(o.s==null?100:o.s); applyCam(); };
  // changing the fine-adjust target also DISPLAYS that antenna (VTX targets),
  // so you always see the one your sliders are moving.
  const onPick = ()=>{ const t = el('camTarget').value;
    if (t.indexOf('vtx_')===0 && typeof showVtxModel==='function') showVtxModel(t.slice(4));
    sync(); };
  el('camTarget').addEventListener('change', onPick);
  // let the model dropdown drive this panel too (see vtxSel handler above)
  window.__pickAntenna = (t)=>{ const s=el('camTarget'); if(s){ s.value=t; sync(); } };
  el('camReset').addEventListener('click', ()=>{ off[el('camTarget').value]=cp(DEF[el('camTarget').value]); sync(); });
  Object.keys(DEF).forEach(applyTarget);   // seat camera/mounts + tilt every antenna at load
  sync();                                  // reflect the current dropdown target in the UI
})();
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

// ---- mode navigation + fullscreen -----------------------------------------
{ const cur = PLAY ? 'play' : (BUILD ? 'build' : 'view');
  const HELP = {
    view:  'Explore le drone : vues, éclaté, sélecteurs de pièces et couleurs.',
    build: 'Monte le drone pièce par pièce : clic = surligner, double-clic = emboîter.',
    play:  'Pilote le drone au clavier ou par script SDK.',
  };
  const NAME = {view:'Visualisateur', build:'Assemblage', play:'Playground'};
  document.querySelectorAll('nav#modes .mode, nav#modes2 .mode').forEach(a=>{
    a.classList.toggle('active', a.dataset.mode === cur); });
  const mn = document.getElementById('modeName');
  if (mn) mn.textContent = NAME[cur];
  const mh = document.getElementById('modeHelp');
  if (mh) mh.textContent = HELP[cur];
  // build.html defaults to assembly: its "Visualisateur" link must switch it off
  if (__BUILD_DEFAULT__){
    const q = {view:'?nobuild=1', build:'?', play:'?playground=1&nobuild=1'};
    document.querySelectorAll('nav#modes .mode, nav#modes2 .mode').forEach(a=>{
      a.setAttribute('href', q[a.dataset.mode]); });
  }
  const fs = document.getElementById('fs');
  const toggleFS = ()=>{ if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen().catch(()=>{}); };
  if (fs) fs.onclick = toggleFS;
  addEventListener('keydown', e=>{ if ((e.key==='f'||e.key==='F') &&
    !/^(INPUT|TEXTAREA|SELECT)$/.test((e.target.tagName||''))) toggleFS(); });
  addEventListener('fullscreenchange', ()=>{ if (fs) fs.textContent =
    document.fullscreenElement ? '⛶ Quitter' : '⛶ Plein écran'; setTimeout(resize, 60); });
}

// ===========================================================================
//  Assembly simulator (build.html / ?build=1)
//  Reuses the groups THIS FILE already built, so every part keeps the exact
//  geometry, seat, material and colour of the 3-D viewer — nothing is re-typed.
// ===========================================================================
const ASM = (function(){
  if (!BUILD) return null;
  const $ = id => document.getElementById(id);
  // one entry per toggle-able group, in a sensible build order
  const ORDER = ['bottom','motors','standoffs','elec','airunit','camcage','cagestd',
    'cammount_bottom','camera','cammount_top','top','tpu','rx','vtxant','cap',
    'gps','buzzer','cables','screws','props','battery'];
  // what each part is / how it seats — shown under its name in the list
  const NOTE = {
    bottom:"La base de tout : plaque carbone 3 mm, les 4 bras vers l'extérieur.",
    motors:"4× 1104 7500KV, un par bras sur les trous à 9 mm, vissés par-dessous.",
    standoffs:"Entretoises alu : 1 à l'avant, 2 à l'arrière — elles portent la plaque haute.",
    elec:"Carte AIO (FC + 4 ESC) à 45° sur le montage 25,5 mm, connecteurs vers l'arrière.",
    airunit:"Air unit DJI O4 Lite, empilée au-dessus de la FC sur silent-blocs.",
    camcage:"Les deux joues carbone qui encaissent les chocs devant la caméra.",
    cagestd:"Les 2 barres dorées qui relient les joues ; la caméra se loge entre elles.",
    cammount_bottom:"Berceau TPU inférieur : il reçoit le bas de la caméra.",
    camera:"Caméra inclinée ~27°, objectif bien en retrait dans la cage.",
    cammount_top:"Berceau TPU supérieur : il referme et bloque la caméra.",
    top:"Plaque haute 2 mm, vissée sur les 3 entretoises. La fente arrière = passage XT30.",
    tpu:"Bumpers imprimés : patins de bras + pare-chocs arrière, ils absorbent les crashs.",
    rx:"Récepteur ELRS dans son berceau TPU, antenne T horizontale vers l'arrière.",
    vtxant:"Antenne vidéo 5,8 GHz, tête vers le haut dans la baie arrière.",
    cap:"Condensateur 25 V 22 µF dans son support TPU — il lisse les pics de courant.",
    gps:"GPS / compas posé sur le stack, dans l'empreinte du châssis (vols extérieurs).",
    buzzer:"Buzzer de repérage, à l'arrière, orienté vers l'extérieur.",
    cables:"3 fils de phase par moteur le long des bras, sous leur garde TPU.",
    screws:"Visserie M2 : moteurs, entretoises et stack.",
    props:"Hélices Gemfan 2520 — en dernier, 2 sens de rotation, écrous serrés.",
    battery:"Pack DOGCOM 560 mAh 3S sanglé sur la plaque haute, XT30 par la fente.",
  };
  // for the "Ranger les pièces" layout
  const CAT = {
    bottom:0, top:0, camcage:0, standoffs:0, cagestd:0, screws:0,       // structure
    motors:1, props:1,                                                  // propulsion
    elec:2, airunit:2, rx:2, gps:2, buzzer:2, cap:2, cables:2, battery:2,// électronique
    tpu:3, cammount_top:3, cammount_bottom:3, camera:3, vtxant:3,       // TPU / caméra
  };
  const CATNAME = ['structure carbone','propulsion','électronique','TPU & caméra'];
  const list = ORDER.filter(k => G[k]);
  const items = list.map((k,i) => {
    const g = G[k];
    const seat = (g.userData.home || g.position).clone();   // its true assembled seat
    const a = (i/list.length)*Math.PI*2 + 0.4, R = 0.145;
    return {key:k, g, seat, cat:(CAT[k]||0),
            bin:new THREE.Vector3(Math.cos(a)*R, Math.sin(a)*R, 0.004),
            placed:true};
  });
  // default layout: parts waiting in a ring around the build area
  function circleSpots(){
    items.forEach((it,i) => { const a = (i/items.length)*Math.PI*2 + 0.4, R = 0.145;
      it.bin.set(Math.cos(a)*R, Math.sin(a)*R, 0.004); });
  }
  // tidy: parts lined up in rows, one row per category, around the build area
  function tidySpots(){
    const rows = [[],[],[],[]];
    items.forEach(it => rows[it.cat].push(it));
    rows.forEach((row, c) => {
      const y = 0.115 - c*0.075;                            // one row per category
      row.forEach((it, j) => {
        const x = (j - (row.length-1)/2) * 0.055;
        it.bin.set(x, y, 0.004);
      });
    });
  }
  let sel = 0, ghostOn = true, ghosts = [];

  // translucent guide at each empty seat
  function makeGhosts(){
    ghosts.forEach(x => { frameRoot.remove(x); });
    ghosts = items.map(it => { const c = it.g.clone(true);
      c.traverse(o => { if (o.isMesh) o.material = new THREE.MeshStandardMaterial({
        color:0x5db0ff, transparent:true, opacity:0.13, depthWrite:false}); });
      c.position.copy(it.seat); c.visible = false; frameRoot.add(c); return c; });
  }
  // highlight = emissive tint on the real meshes (kept out of the colour pickers)
  function setHighlight(it, on){
    it.g.traverse(o => { if (o.isMesh && o.material && o.material.emissive){
      if (on){ if (!o.userData._em) o.userData._em = o.material.emissive.getHex();
               o.material.emissive.setHex(0x1d4e7a); }
      else if (o.userData._em !== undefined){ o.material.emissive.setHex(o.userData._em); } } });
  }
  function refresh(){
    const done = items.filter(i => i.placed).length;
    $('asmCnt').textContent = done; $('asmTot').textContent = items.length;
    $('asmFill').style.width = (100*done/items.length) + '%';
    [...$('asmList').children].forEach((el,i) => {
      el.classList.toggle('ok', items[i].placed);
      el.classList.toggle('sel', i === sel); });
    ghosts.forEach((gh,i) => { gh.visible = ghostOn && !items[i].placed; });
  }
  function select(i){                       // i < 0 clears the selection
    if (items[sel]) setHighlight(items[sel], false);
    sel = i;
    if (items[sel]) setHighlight(items[sel], true);
    refresh();
  }
  function snap(i, ms){
    const it = items[i]; if (!it || it.placed) return;
    const from = it.g.position.clone(), to = it.seat.clone(), t0 = performance.now();
    it.placed = true; ms = ms || 480;
    (function tick(){
      const t = Math.min(1, (performance.now()-t0)/ms), e = 1-Math.pow(1-t,3);
      it.g.position.lerpVectors(from, to, e);
      it.g.position.z += Math.sin(Math.PI*t)*0.010;          // small arc, like a hand
      if (t < 1) requestAnimationFrame(tick); else { it.g.position.copy(to); refresh(); }
    })();
    refresh();
  }
  function scatter(){
    items.forEach(it => { it.placed = false; it.g.position.copy(it.bin); });
    sel = 0; refresh();
  }
  // sidebar list: click = highlight, double-click = assemble
  const box = $('asmList');
  items.forEach((it,i) => {
    const el = document.createElement('div'); el.className = 'asm';
    el.innerHTML = `<span class="d"></span><span class="tx">` +
      `<b>${(GROUPS[it.key]||{}).label || it.key}</b>` +
      (NOTE[it.key] ? `<i>${NOTE[it.key]}</i>` : '') + `</span>`;
    el.addEventListener('click', () => select(i));
    el.addEventListener('dblclick', () => { select(i); snap(i, 380); });
    box.appendChild(el);
  });
  $('asmAll').onclick = () => items.forEach((it,i) => {
    if (!it.placed) setTimeout(() => snap(i, 420), i*110); });
  $('asmReset').onclick = scatter;
  $('asmGhost').onclick = e => { ghostOn = !ghostOn;
    e.target.textContent = 'Fantômes : ' + (ghostOn?'oui':'non'); refresh(); };
  // "Ranger les pièces": lay the loose parts out in tidy rows, one per category
  let tidy = false;
  $('asmTidy').onclick = e => {
    tidy = !tidy;
    if (tidy) tidySpots(); else circleSpots();
    items.forEach(it => { if (!it.placed) it.g.position.copy(it.bin); });
    e.target.textContent = tidy ? 'Éparpiller autour' : 'Ranger les pièces';
    $('asmHint').textContent = tidy
      ? 'Rangé par catégorie : ' + CATNAME.join(' · ') : '';
  };

  // drag a loose part on its own height plane; release near the seat -> clicks in
  const ray = new THREE.Raycaster(), ptr = new THREE.Vector2();
  let drag = null, dragZ = 0;
  const hit = ev => { const r = renderer.domElement.getBoundingClientRect();
    ptr.x = ((ev.clientX-r.left)/r.width)*2-1; ptr.y = -((ev.clientY-r.top)/r.height)*2+1;
    ray.setFromCamera(ptr, camera);
    const loose = items.filter(i => !i.placed);
    const hits = ray.intersectObjects(loose.map(i => i.g), true);
    if (!hits.length) return -1;
    let o = hits[0].object; while (o.parent && o.parent !== frameRoot) o = o.parent;
    return items.findIndex(i => i.g === o); };
  renderer.domElement.addEventListener('pointerdown', ev => {
    const i = hit(ev);
    if (i < 0){ select(-1); return; }        // clic dans le vide = on désélectionne
    drag = i; dragZ = items[i].g.position.z; select(i); controls.enabled = false; });
  renderer.domElement.addEventListener('pointermove', ev => {
    if (drag === null) return;
    const r = renderer.domElement.getBoundingClientRect();
    ptr.x = ((ev.clientX-r.left)/r.width)*2-1; ptr.y = -((ev.clientY-r.top)/r.height)*2+1;
    ray.setFromCamera(ptr, camera);
    const pl = new THREE.Plane(new THREE.Vector3(0,0,1), -dragZ), p = new THREE.Vector3();
    if (ray.ray.intersectPlane(pl, p)) items[drag].g.position.set(p.x, p.y, dragZ); });
  addEventListener('pointerup', () => {
    if (drag === null) return;
    const it = items[drag];
    if (it.g.position.distanceTo(it.seat) < 0.024) snap(drag, 240);
    drag = null; controls.enabled = true; });

  makeGhosts(); scatter(); select(0);
  return {items, snap, scatter, select};
})();

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
    import datetime
    build = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    html = (TEMPLATE
            .replace("__IMPORTMAP__", importmap())
            .replace("__BUILD__", build)
            .replace("__NAME__", MODEL["name"])
            .replace("__SUB__", MODEL["sub"])
            .replace("__SPECS__", specs)
            .replace("__MODEL__", json.dumps(
                {k: MODEL[k] for k in ("motors", "prop_z", "motor_z", "frame_z",
                                       "elec", "screws", "standoffs",
                                       "cammount", "side", "explode")},
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
                "dji_pro_ant": b64(os.path.join(STL, "dji_pro_ant.stl")),
                "matchstick": b64(os.path.join(STL, "ant_singularity.stl")),
                "rhcp_lp": b64(os.path.join(STL, "rhcp_lp.stl")),
                "foxeer_lp": b64(os.path.join(STL, "foxeer_lp.stl")),
                # real Foxeer Lollipop SMA (owner's STEP), split for head-only colour
                "foxeer_head": b64(os.path.join(STL, "foxeer_head.stl")),
                "foxeer_stem": b64(os.path.join(STL, "foxeer_stem.stl")),
                "foxeer_conn": b64(os.path.join(STL, "foxeer_conn.stl")),
                "rear_bay": b64(os.path.join(STL, "rear_bay.stl")),
                # Stratos 3 side panels (flancs imprimés) — 5 variantes
                "sp_a": b64(os.path.join(S3, "side_panel_a.stl")),
                "sp_b": b64(os.path.join(S3, "side_panel_b.stl")),
                "sp_c": b64(os.path.join(S3, "side_panel_c.stl")),
                "sp_d": b64(os.path.join(S3, "side_panel_d.stl")),
                "sp_e": b64(os.path.join(S3, "side_panel_e.stl")),
                "sp_f": b64(os.path.join(S3, "side_panel_f.stl")),
                "cable": b64(os.path.join(STL, "motor_cable.stl")),
            }, separators=(",", ":"))))
    # the viewer: assembly panel available on demand (?build=1)
    with open(OUT, "w") as f:
        f.write(html.replace("__BUILD_DEFAULT__", "false"))
    print(f"== {MODEL['name']}-001 3D viewer + playground ==")
    print(f"  wrote {os.path.relpath(OUT, REPO)} ({len(html)} B)")

    # the assembly simulator: SAME page, same parts/materials/colours, but the
    # assembly panel is on by default. Generated from this file so build.html can
    # never drift from the viewer.
    build_out = os.path.join(REPO, "TinyHoopMK1", "build", "build.html")
    os.makedirs(os.path.dirname(build_out), exist_ok=True)
    with open(build_out, "w") as f:
        f.write(html.replace("__BUILD_DEFAULT__", "true"))
    print(f"  wrote {os.path.relpath(build_out, REPO)} (simulateur d'assemblage)")


if __name__ == "__main__":
    main()
