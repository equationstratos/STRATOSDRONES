#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère les affiches « science des drones » (Stratos Drones) en HTML autonome.

Produit 3 HTML (FR sombre, FR clair, EN sombre) + un manifest.json décrivant
les rendus PDF/PNG (l'A3 est le FR sombre rendu à l'échelle 1.4142 — cf.
render.cjs). Le QR code (vers le site) est encodé hors-ligne via l'encodeur
pur-Python vendorisé tools/qrcodegen.py (MIT, Project Nayuki) et inséré en SVG
vectoriel — net à n'importe quelle taille, aucun réseau requis.

    python3 outreach/make_affiche.py      # -> outreach/*.html + manifest.json
"""
import base64, json, os, sys
from string import Template

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "tools"))
import qrcodegen  # vendored, MIT

HERO = "/home/user/STRATOSDRONE/site/assets/cad/hero.jpg"

# ---------------------------------------------------------------- coordonnées
CONTACT = {
    "name":  "Patrick Ardanny",
    "phone": "07 84 84 99 74",
    "email": "equationstratos001@gmail.com",
    "zone_fr": "Bordeaux · interventions dans toute la France",
    "zone_en": "Bordeaux · available across France",
    "link":  "equationstratos.github.io/STRATOSDRONES",
    "url":   "https://equationstratos.github.io/STRATOSDRONES/",
}

# ---------------------------------------------------------------- textes
TEXT = {
 "fr": {
  "eyebrow": "ATELIERS &amp; INTERVENTIONS",
  "t1": "La science", "t2": "des drones",
  "sub": "Un seul projet — toutes les matières.<br>On comprend en faisant : "
         "on code, on conçoit, on imprime, on soude… et ça vole.",
  "k_skills": "Ce qu'on apprend en construisant un drone",
  "skills": [
    ("💻","Programmation","Coder les missions de vol — par blocs pour débuter, puis en Python."),
    ("📐","CAO &amp; Design","Dessiner et concevoir les pièces en 3D."),
    ("🖨️","Impression 3D","Fabriquer le châssis et les protections d'hélices."),
    ("🔌","Électronique","Capteurs, cartes, alimentation — comprendre ce qui vole."),
    ("🔥","Soudure","Assembler soi-même ses propres composants."),
    ("🛩️","Physique &amp; pilotage","Portance, stabilité, capteurs… et un simulateur avant le vol."),
    ("🤖","Robotique","Autonomie, capteurs et vol en essaim."),
    ("🧮","Maths &amp; logique","Repères, angles, distances, résolution de problèmes."),
  ],
  "k_for": "Pour qui ?",
  "auds": [("👦","Enfants"),("🧑‍🎓","Ados"),("🧑","Adultes"),("👴","Seniors"),("🔎","Curieux")],
  "note": "<b>Tous les âges, tous les niveaux — débutants bienvenus.</b> Des enfants "
          "aux seniors : éveil scientifique, découverte, transmission et lien social.",
  "k_fmt": "Formats possibles",
  "fmts": ["Séance découverte (1–2 h)","Cycle d'ateliers",
           "Démonstration / événement","Projet « un drone qui vole »"],
  "cta": "Intéressé ? <span>Parlons-en.</span>",
  "qr": "Scanne pour<br>découvrir le projet",
  "zone": CONTACT["zone_fr"],
  "refer": "Pas concerné directement ? <b>Transmettez cette affiche</b> — ou le contact "
           "ci-dessus — à une personne ou une structure de votre entourage que cela "
           "pourrait intéresser. Merci&nbsp;! 🙏",
 },
 "en": {
  "eyebrow": "WORKSHOPS &amp; TALKS",
  "t1": "The science", "t2": "of drones",
  "sub": "One project — every subject.<br>Learn by doing: you code, design, print, "
         "solder… and it flies.",
  "k_skills": "What you learn by building a drone",
  "skills": [
    ("💻","Programming","Code flight missions — blocks to start, then Python."),
    ("📐","CAD &amp; Design","Model and design the parts in 3D."),
    ("🖨️","3D printing","Make the frame and the prop guards."),
    ("🔌","Electronics","Sensors, boards, power — see what makes it fly."),
    ("🔥","Soldering","Assemble your very own components."),
    ("🛩️","Physics &amp; piloting","Lift, stability, sensors… and a simulator before you fly."),
    ("🤖","Robotics","Autonomy, sensors and swarm flight."),
    ("🧮","Maths &amp; logic","Coordinates, angles, distances, problem-solving."),
  ],
  "k_for": "Who is it for?",
  "auds": [("👦","Kids"),("🧑‍🎓","Teens"),("🧑","Adults"),("👴","Seniors"),("🔎","Curious")],
  "note": "<b>All ages, all levels — beginners welcome.</b> From kids to seniors: "
          "scientific discovery, hands-on learning, sharing and connection.",
  "k_fmt": "Possible formats",
  "fmts": ["Taster session (1–2 h)","Workshop series",
           "Demo / event","Project “a drone that flies”"],
  "cta": "Interested? <span>Let's talk.</span>",
  "qr": "Scan to<br>discover the project",
  "zone": CONTACT["zone_en"],
  "refer": "Not for you directly? <b>Pass this poster on</b> — or the contact above — to "
           "someone or an organisation in your network who might be interested. Thank you! 🙏",
 },
}

def b64img(path):
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()

def qr_svg(url, quiet=3, fg="#0b0e14"):
    qr = qrcodegen.QrCode.encode_text(url, qrcodegen.QrCode.Ecc.MEDIUM)
    n = qr.get_size(); tot = n + quiet * 2
    rects = "".join(f'<rect x="{x+quiet}" y="{y+quiet}" width="1" height="1"/>'
                    for y in range(n) for x in range(n) if qr.get_module(x, y))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tot} {tot}" '
            f'shape-rendering="crispEdges" preserveAspectRatio="xMidYMid meet">'
            f'<rect width="{tot}" height="{tot}" fill="#fff"/>'
            f'<g fill="{fg}">{rects}</g></svg>')

HERO_B64 = b64img(HERO)
QR_SVG = qr_svg(CONTACT["url"])

CSS = r"""
  @page { margin: 0; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html,body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body { font-family: "Segoe UI","Helvetica Neue",Arial,sans-serif; color:#12161d; }
  .page { width:210mm; height:297mm; display:flex; flex-direction:column; overflow:hidden; background:var(--pagebg,#f5f8fc); }

  /* hero */
  .hero { position:relative; height:104mm; overflow:hidden; }
  .htext { position:relative; z-index:2; padding:13mm 12mm 0; }
  .browrow { display:flex; align-items:center; gap:4mm; }
  .brand { font-weight:800; letter-spacing:.14em; font-size:11pt; }
  .brand b { color:#4d8bff; }
  .eyebrow { display:inline-block; font-size:8.5pt; font-weight:700; letter-spacing:.18em;
     color:#bcd2ff; border:1px solid #2f6fed; border-radius:20px; padding:1.6mm 4mm; margin-top:2.5mm; }
  .os { font-size:7.5pt; font-weight:800; letter-spacing:.12em; color:#4d8bff; margin-top:2.5mm; }
  h1 { margin-top:9mm; font-size:33pt; line-height:1.02; font-weight:800; letter-spacing:-.5px; max-width:118mm; }
  h1 span { color:#4d8bff; }
  .sub { margin-top:4mm; font-size:12.5pt; color:#d6e2f5; font-weight:500; max-width:112mm; }

  /* body */
  .body { flex:1; padding:8mm 12mm 0; display:flex; flex-direction:column; }
  .kicker { font-size:10pt; font-weight:800; letter-spacing:.12em; color:#2f6fed; text-transform:uppercase; }
  .kicker.mt { margin-top:6.5mm; }
  .grid { margin-top:4mm; display:grid; grid-template-columns:1fr 1fr; gap:3.2mm 5mm; }
  .card { display:flex; gap:3.2mm; align-items:flex-start; }
  .ic { font-size:15pt; line-height:1; width:9mm; text-align:center; flex:none; }
  .ct { font-size:11.5pt; font-weight:700; }
  .cd { font-size:9pt; color:#4a5568; line-height:1.3; margin-top:.6mm; }
  .rows { margin-top:4mm; display:flex; gap:3mm; flex-wrap:wrap; }
  .aud { display:flex; align-items:center; gap:2mm; background:#fff; border:1px solid #dde6f2;
     border-radius:22px; padding:2mm 4.5mm; font-size:10.5pt; font-weight:600; }
  .ae { font-size:13pt; }
  .note { margin-top:3mm; font-size:9.5pt; color:#556; }
  .note b { color:#12161d; }
  .fmts { margin-top:4mm; display:grid; grid-template-columns:1fr 1fr; gap:2.6mm 4mm; }
  .fmt { font-size:10pt; font-weight:600; padding:2.4mm 4mm; background:#eaf1ff; color:#1c3d7a;
     border-radius:7px; border-left:3px solid #2f6fed; }

  /* footer */
  .foot { margin-top:auto; margin-left:-12mm; margin-right:-12mm; padding:6.5mm 12mm; }
  .fmain { display:flex; gap:8mm; align-items:flex-start; }
  .ftxt { flex:1; }
  .cta { font-size:15pt; font-weight:800; }
  .cta span { color:#4d8bff; }
  .contact { margin-top:3mm; display:flex; flex-wrap:wrap; gap:2mm 6mm; font-size:10.5pt; color:#e6eefc; }
  .contact b { color:#fff; }
  .refer { margin-top:4mm; font-size:9.5pt; color:#9fb3d4; border-top:1px solid #232a36; padding-top:3mm; }
  .refer b { color:#cfe0ff; }
  .qr { flex:none; width:30mm; text-align:center; }
  .qrtile { width:30mm; height:30mm; background:#fff; border-radius:4px; padding:1.6mm; }
  .qrtile svg { width:100%; height:100%; display:block; }
  .qrlbl { margin-top:1.6mm; font-size:7.5pt; line-height:1.2; color:#9fb3d4; font-weight:600; }

  /* ---- dark theme ---- */
  .t-dark .hero { background:#0b0e14; color:#fff; }
  .t-dark .hero img { position:absolute; right:-6mm; bottom:-4mm; width:132mm; opacity:.96; }
  .t-dark .hero::after { content:""; position:absolute; inset:0;
     background:linear-gradient(105deg,#0b0e14 33%, rgba(11,14,20,.55) 55%, rgba(11,14,20,0) 74%); }
  .t-dark .foot { background:#0b0e14; color:#fff; }

  /* ---- light theme (moins d'encre) ---- */
  .t-light { --pagebg:#ffffff; }
  .t-light .hero { background:#eef3fb; color:#12161d; }
  .t-light .hero img { position:absolute; right:9mm; bottom:9mm; width:99mm; border-radius:7px;
     border:1px solid #cfdcef; box-shadow:0 3px 14px rgba(20,40,80,.12); }
  .t-light .brand { color:#12161d; }
  .t-light .brand b { color:#2f6fed; }
  .t-light .eyebrow { color:#1c4bb0; }
  .t-light .os { color:#2f6fed; }
  .t-light h1 { max-width:85mm; }
  .t-light h1 span { color:#2f6fed; }
  .t-light .sub { color:#33415c; max-width:83mm; font-size:11.5pt; }
  .t-light .foot { background:#eaf1ff; color:#12161d; border-top:3px solid #2f6fed; }
  .t-light .cta span { color:#2f6fed; }
  .t-light .contact { color:#33415c; }
  .t-light .contact b { color:#12161d; }
  .t-light .refer { color:#5a6b86; border-top-color:#cdddf2; }
  .t-light .refer b { color:#12161d; }
  .t-light .qrlbl { color:#5a6b86; }
"""

TPL = Template(r"""<!doctype html><html lang="$lang"><head><meta charset="utf-8">
<style>$css</style></head><body class="$tcls">
<div class="page">
  <div class="hero">
    <img src="$hero" alt="">
    <div class="htext">
      <div class="browrow"><span class="brand">STRATO<b>S</b> DRONES</span>
        <span class="os">100% OPEN SOURCE</span></div>
      <div class="eyebrow">$eyebrow</div>
      <h1>$t1<br>$t2</h1>
      <div class="sub">$sub</div>
    </div>
  </div>
  <div class="body">
    <div class="kicker">$k_skills</div>
    <div class="grid">$cards</div>
    <div class="kicker mt">$k_for</div>
    <div class="rows">$auds</div>
    <div class="note">$note</div>
    <div class="kicker mt">$k_fmt</div>
    <div class="fmts">$fmts</div>
    <div class="foot">
      <div class="fmain">
        <div class="ftxt">
          <div class="cta">$cta</div>
          <div class="contact">
            <span><b>$name</b></span><span>📞 $phone</span><span>✉️ $email</span>
            <span>📍 $zone</span><span>🔗 $link</span>
          </div>
          <div class="refer">$refer</div>
        </div>
        <div class="qr"><div class="qrtile">$qr_svg</div><div class="qrlbl">$qr_lbl</div></div>
      </div>
    </div>
  </div>
</div></body></html>""")

def build(lang, theme):
    t = TEXT[lang]
    cards = "".join(f'<div class="card"><div class="ic">{e}</div><div>'
                    f'<div class="ct">{ti}</div><div class="cd">{d}</div></div></div>'
                    for e, ti, d in t["skills"])
    auds = "".join(f'<div class="aud"><span class="ae">{e}</span>{l}</div>' for e, l in t["auds"])
    fmts = "".join(f'<div class="fmt">{f}</div>' for f in t["fmts"])
    return TPL.substitute(
        lang=lang, css=CSS, tcls=f"t-{theme}", hero=HERO_B64,
        eyebrow=t["eyebrow"], t1=t["t1"], t2=t["t2"], sub=t["sub"],
        k_skills=t["k_skills"], cards=cards, k_for=t["k_for"], auds=auds, note=t["note"],
        k_fmt=t["k_fmt"], fmts=fmts, cta=t["cta"],
        name=CONTACT["name"], phone=CONTACT["phone"], email=CONTACT["email"],
        zone=t["zone"], link=CONTACT["link"], refer=t["refer"],
        qr_svg=QR_SVG, qr_lbl=t["qr"])

# generate the 3 distinct HTMLs
variants = {"affiche-fr-dark.html": ("fr","dark"),
            "affiche-fr-light.html": ("fr","light"),
            "affiche-en-dark.html": ("en","dark")}
for fn, (lang, theme) in variants.items():
    with open(os.path.join(HERE, fn), "w") as f:
        f.write(build(lang, theme))
    print("wrote", fn)

# render manifest: 4 posters (A3 = fr-dark scaled x sqrt(2))
manifest = [
  {"html":"affiche-fr-dark.html",  "out":"affiche-fr-a4",        "format":"A4", "scale":1.0},
  {"html":"affiche-fr-dark.html",  "out":"affiche-fr-a3",        "format":"A3", "scale":1.41428},
  {"html":"affiche-fr-light.html", "out":"affiche-fr-a4-claire", "format":"A4", "scale":1.0},
  {"html":"affiche-en-dark.html",  "out":"affiche-en-a4",        "format":"A4", "scale":1.0},
]
with open(os.path.join(HERE, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
print("QR encodes:", CONTACT["url"])
print("wrote manifest.json ->", len(manifest), "posters")
