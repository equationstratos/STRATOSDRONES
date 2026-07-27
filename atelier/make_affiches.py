#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère les affiches de l'atelier build FPV et de la Stratos FPV League.

Sorties (HTML autonomes, une page A4 chacune, prêtes à rendre en PDF/PNG) :

    affiche-atelier-dark.html    affiche principale, thème sombre  (A4 + A3)
    affiche-atelier-light.html   même affiche, thème clair (économe en encre)
    affiche-ligue-dark.html      affiche de la ligue FPV
    manifest.json                décrit les rendus pour render.cjs

    python3 atelier/make_affiches.py     # -> HTML + manifest.json
    node    atelier/render.cjs           # -> PDF + PNG

Le QR code est encodé hors-ligne (aucun réseau) par l'encodeur pur-Python
vendorisé dans outreach/tools/qrcodegen.py — MIT, Project Nayuki — et inséré
en SVG vectoriel : net à n'importe quelle taille d'impression.

Pour changer les prix, les horaires ou les coordonnées : tout est dans les
dictionnaires CONTACT / ATELIER / LIGUE ci-dessous.
"""
import base64
import json
import os
import sys
from string import Template

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "outreach", "tools"))
import qrcodegen  # vendorisé, MIT (Project Nayuki)

HERO = os.path.join(REPO, "site", "assets", "cad", "hero.jpg")
SHOT = os.path.join(REPO, "site", "assets", "configurator", "blue.jpg")

# ------------------------------------------------------------------ contact
CONTACT = {
    "name":  "Patrick Ardanny",
    "phone": "07 84 84 99 74",
    "email": "stratosdrones001@gmail.com",
    "zone":  "Bordeaux · déplacements dans toute la France",
    "link":  "equationstratos.github.io/STRATOSDRONES/atelier/",
    "url":   "https://equationstratos.github.io/STRATOSDRONES/atelier/",
}

# ------------------------------------------------------------------ contenus
ATELIER = {
    "eyebrow": "ATELIER BUILD FPV · TOUS NIVEAUX",
    "t1": "Construis ton", "t2": "drone FPV",
    "sub": "Une journée, un fer à souder, un châssis carbone.<br>"
           "À la fin ça vole — et tu <b>repars avec</b>.",
    "k_learn": "Ce que tu fais de tes mains",
    "learn": [
        ("🔥", "Soudure",       "On s'entraîne sur carte d'exercice avant de toucher le stack."),
        ("🔧", "Montage",       "Plaques carbone, moteurs, supports TPU imprimés sur place."),
        ("🎛️", "Configuration", "Betaflight : bind ELRS, sens moteurs, modes, failsafe."),
        ("🕹️", "Vol",           "Simulateur, puis premier décollage en filet. Chacun vole."),
        ("🔋", "Sécurité LiPo", "Charge, stockage, tension par cellule. Ça s'apprend une fois."),
        ("🩺", "Diagnostic",    "Trouver la panne tout seul, plus tard, chez toi."),
    ],
    "k_day": "La journée",
    "day": [
        ("9h30",  "Accueil, on nomme chaque pièce"),
        ("10h30", "Atelier soudure sur carte d'entraînement"),
        ("11h15", "Montage mécanique du châssis"),
        ("13h30", "Soudure du stack, XT30, moteurs"),
        ("15h45", "Betaflight, bind, failsafe"),
        ("16h30", "Premier vol en filet"),
    ],
    "k_price": "Trois façons de venir",
    "plans": [
        ("DÉCOUVERTE",  "49 €",   "3 h — pour voir si c'est pour toi", False),
        ("BUILD COMPLET", "129 €", "1 journée, drone monté de A à Z",  False),
        ("+ TON DRONE", "129 € + kit", "tu repars avec ce que tu as monté", True),
    ],
    "kit_title": "REPARS AVEC TON DRONE",
    "kit_txt": "Réserve ton kit en même temps que ta place : on le prépare à ton nom, "
               "tu le montes, on le teste au banc avec toi — il rentre dans ton sac le soir même.",
    "kits": [("Kit analogique 2,5\"", "189 €"), ("Kit numérique DJI O4 Lite", "389 €")],
    "foot_k": "Places limitées à 6 par session · à partir de 12 ans · aucun prérequis",
    "qr": "Programme complet,<br>dates &amp; réservation",
    "league_teaser": "Et après l'atelier : <b>Stratos FPV League</b> — classement à l'année, "
                     "manches programmées et impromptues, cadeaux en fin de saison. "
                     "<b>Restez à l'écoute.</b>",
}

LIGUE = {
    "eyebrow": "PROJET ANNEXE · SAISON 1 EN PRÉPARATION",
    "t1": "Stratos", "t2": "FPV League",
    "sub": "Un classement à l'année. Des manches annoncées à l'avance…<br>"
           "et d'autres qui tombent <b>sans prévenir</b>.",
    "k_fmt": "Le format",
    "fmts": [
        ("📅", "Manches programmées",
         "Une par mois, date connue des semaines à l'avance. Qualifs chronométrées, finales par 4."),
        ("⚡", "Manches impromptues",
         "Annoncées <b>48 h avant</b> sur la liste de diffusion. Beau temps, un spot libre : on court."),
        ("🏁", "Trois catégories",
         "Débutant (indoor) · Spec Stratos (même matériel pour tous) · Open 2,5″–3″."),
    ],
    "k_pts": "Barème",
    "pts": [("1ᵉʳ", "25"), ("2ᵉ", "18"), ("3ᵉ", "15"), ("4ᵉ→10ᵉ", "12 · 10 · 8 · 6 · 4 · 2 · 1")],
    "bonus": ["+3 meilleur tour", "+2 présence", "+2 coup de main au montage",
              "+1 manche impromptue honorée", "les 2 plus mauvais résultats sont retirés"],
    "k_prize": "Ce qu'il y a à gagner",
    "prizes": [
        ("🥇", "Champion de saison", "Un drone complet monté &amp; réglé, plaque gravée à son nom."),
        ("🥈", "Vice-champion",      "Un kit châssis complet — carbone + TPU à sa couleur."),
        ("🥉", "Troisième",          "Pack batteries 4 × 3S 560 mAh + chargeur."),
    ],
    "extras": [
        ("🎁", "Tirage au sort à chaque manche parmi <b>tous les présents</b> — être là suffit."),
        ("📈", "Prix de la <b>meilleure progression</b> : pour le débutant, pas pour le rapide."),
        ("💥", "Prix du <b>plus beau crash</b>, au vote du public. Pièces de rechange offertes."),
    ],
    "stay": "RESTEZ À L'ÉCOUTE",
    "stay_txt": "Le calendrier, l'ouverture des inscriptions et les manches flash passent "
                "<b>uniquement</b> par la liste de diffusion. Scanne, laisse ton adresse.",
    "qr": "Rejoindre la ligue<br>&amp; le calendrier",
}


# ------------------------------------------------------------------ utilitaires
def b64img(path):
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def qr_svg(url, quiet=3, fg="#0b0e14"):
    qr = qrcodegen.QrCode.encode_text(url, qrcodegen.QrCode.Ecc.MEDIUM)
    n = qr.get_size()
    tot = n + quiet * 2
    rects = "".join(f'<rect x="{x+quiet}" y="{y+quiet}" width="1" height="1"/>'
                    for y in range(n) for x in range(n) if qr.get_module(x, y))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tot} {tot}" '
            f'shape-rendering="crispEdges" preserveAspectRatio="xMidYMid meet">'
            f'<rect width="{tot}" height="{tot}" fill="#fff"/>'
            f'<g fill="{fg}">{rects}</g></svg>')


HERO_B64 = b64img(HERO)
SHOT_B64 = b64img(SHOT)
QR_SVG = qr_svg(CONTACT["url"])

# ------------------------------------------------------------------ CSS commun
CSS = r"""
  @page { margin: 0; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html,body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body { font-family: "Segoe UI","Helvetica Neue",Arial,sans-serif; color:#12161d; }
  .page { width:210mm; height:297mm; display:flex; flex-direction:column;
          overflow:hidden; background:var(--pagebg,#f5f8fc); }

  /* ── bandeau haut */
  .hero { position:relative; height:78mm; overflow:hidden; background:#080a0f; }
  .hero img.bg { position:absolute; inset:0; width:100%; height:100%; object-fit:cover;
                 opacity:.44; filter:saturate(.8) contrast(1.05); }
  .hero .veil { position:absolute; inset:0;
                background:linear-gradient(105deg,#080a0f 34%,rgba(8,10,15,.55) 68%,rgba(8,10,15,.2)); }
  .htext { position:relative; z-index:2; padding:12mm 12mm 0; color:#fff; }
  .brand { font-weight:800; letter-spacing:.15em; font-size:10.5pt; color:#e9ecf1; }
  .brand b { color:#63a4ff; }
  .eyebrow { display:inline-block; font-size:8pt; font-weight:800; letter-spacing:.17em;
             color:#bcd2ff; border:1px solid #2f6fed; border-radius:20px;
             padding:1.5mm 4mm; margin-top:3mm; }
  h1 { margin-top:7mm; font-size:32pt; line-height:1.02; font-weight:800; letter-spacing:-.6px; }
  h1 span { color:#63a4ff; }
  .sub { margin-top:4mm; font-size:12pt; color:#d6e2f5; font-weight:500; max-width:118mm; }
  .sub b { color:#fff; }

  /* ── corps */
  .body { flex:1; padding:7mm 12mm 0; display:flex; flex-direction:column; }
  .kicker { font-size:9.5pt; font-weight:800; letter-spacing:.13em;
            color:#2f6fed; text-transform:uppercase; }
  .kicker.mt { margin-top:6mm; }
  .kicker.au { color:#b8860b; }

  .grid3 { margin-top:3.5mm; display:grid; grid-template-columns:1fr 1fr 1fr; gap:3mm 5mm; }
  .grid2 { margin-top:3.5mm; display:grid; grid-template-columns:1fr 1fr; gap:2.6mm 6mm; }
  .card { display:flex; gap:3mm; align-items:flex-start; }
  .ic { font-size:13.5pt; line-height:1.1; width:8mm; text-align:center; flex:none; }
  .ct { font-size:10.5pt; font-weight:700; }
  .cd { font-size:8.4pt; color:var(--mutedtxt,#4a5568); line-height:1.3; margin-top:.4mm; }

  /* ── journée */
  .day { margin-top:3.5mm; display:grid; grid-template-columns:1fr 1fr; gap:1.6mm 6mm; }
  .drow { display:flex; gap:3mm; align-items:baseline; font-size:9pt;
          border-bottom:1px dotted var(--rule,#c7d2e2); padding-bottom:1.2mm; }
  .drow time { font-weight:800; color:#2f6fed; width:13mm; flex:none; font-size:8.6pt; }
  .drow span { color:var(--mutedtxt,#4a5568); }

  /* ── tarifs */
  .plans { margin-top:3.5mm; display:grid; grid-template-columns:1fr 1fr 1fr; gap:4mm; }
  .plan { border:1px solid var(--rule,#c7d2e2); border-radius:3mm; padding:4mm 4mm 4.5mm;
          background:var(--cardbg,#fff); }
  .plan .pn { font-size:7.6pt; font-weight:800; letter-spacing:.12em; color:var(--mutedtxt,#4a5568); }
  .plan .pp { font-size:19pt; font-weight:800; letter-spacing:-.5px; margin:1mm 0 .6mm; }
  .plan .pd { font-size:8.2pt; color:var(--mutedtxt,#4a5568); line-height:1.28; }
  .plan.hi { border-color:#e0a300; border-width:1.4px; background:var(--goldbg,#fff8e6); }
  .plan.hi .pn, .plan.hi .pp { color:#a97400; }

  /* ── bloc doré */
  .gold { margin-top:5mm; border-radius:3mm; padding:5mm 6mm;
          background:var(--goldband,linear-gradient(100deg,#fff3d0,#ffe7a8));
          border:1.4px solid #e0a300; }
  .gold .gt { font-size:12.5pt; font-weight:800; letter-spacing:.04em; color:#7a5200; }
  .gold .gd { font-size:9pt; color:#6b4a08; margin-top:1.4mm; line-height:1.35; max-width:118mm; }
  .gold .gk { margin-top:3mm; display:flex; gap:5mm; flex-wrap:wrap; }
  .gold .gkit { font-size:9pt; color:#5c3f06; }
  .gold .gkit b { font-size:11pt; color:#7a5200; }

  /* ── pied */
  .foot { margin-top:auto; display:flex; gap:6mm; align-items:flex-end;
          padding:6mm 12mm 8mm; }
  .fc { flex:1; }
  .cta { font-size:15pt; font-weight:800; line-height:1.1; }
  .cta span { color:#2f6fed; }
  .lines { margin-top:2.5mm; font-size:9.4pt; line-height:1.5; }
  .lines b { font-weight:700; }
  .zone { font-size:8.4pt; color:var(--mutedtxt,#4a5568); margin-top:1.5mm; }
  .note { margin-top:3mm; font-size:8pt; color:var(--mutedtxt,#4a5568); line-height:1.35;
          border-left:2px solid #2f6fed; padding-left:3mm; }
  .qr { width:34mm; flex:none; text-align:center; }
  .qrtile { width:34mm; height:34mm; background:#fff; border-radius:2.5mm;
            padding:1.6mm; border:1px solid var(--rule,#c7d2e2); }
  .qrtile svg { width:100%; height:100%; display:block; }
  .qrlbl { font-size:7.4pt; color:var(--mutedtxt,#4a5568); margin-top:1.5mm; line-height:1.25; }

  /* ── thèmes */
  .t-dark { --pagebg:#0b0d12; --mutedtxt:#9aa3af; --rule:#242832; --cardbg:#141821;
            --goldbg:#1c1608; --goldband:linear-gradient(100deg,#241b06,#2e2208); }
  .t-dark, .t-dark .body { color:#e9ecf1; }
  .t-dark .gold { border-color:#8a6a12; }
  .t-dark .gold .gt { color:#f5b942; }
  .t-dark .gold .gd, .t-dark .gold .gkit { color:#d8c08a; }
  .t-dark .gold .gkit b { color:#f5b942; }
  .t-dark .plan.hi { border-color:#8a6a12; }
  .t-dark .plan.hi .pn, .t-dark .plan.hi .pp { color:#f5b942; }
  .t-dark .kicker.au { color:#f5b942; }
  .t-light { --pagebg:#f5f8fc; }
"""

# ------------------------------------------------------------------ gabarits
TPL_ATELIER = Template(r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Atelier build FPV — Stratos Drones</title>
<style>$css</style></head>
<body><div class="page $tcls">

  <div class="hero">
    <img class="bg" src="$hero" alt="">
    <div class="veil"></div>
    <div class="htext">
      <div class="brand">STRATOS<b>DRONES</b></div>
      <div class="eyebrow">$eyebrow</div>
      <h1>$t1<br><span>$t2</span></h1>
      <div class="sub">$sub</div>
    </div>
  </div>

  <div class="body">
    <div class="kicker">$k_learn</div>
    <div class="grid3">$learn</div>

    <div class="kicker mt">$k_day</div>
    <div class="day">$day</div>

    <div class="kicker mt">$k_price</div>
    <div class="plans">$plans</div>

    <div class="gold">
      <div class="gt">🚁 $kit_title</div>
      <div class="gd">$kit_txt</div>
      <div class="gk">$kits</div>
    </div>
  </div>

  <div class="foot">
    <div class="fc">
      <div class="cta">Une place, un fer à souder — <span>et ça vole.</span></div>
      <div class="lines"><b>$name</b> · $phone<br>$email<br>$link</div>
      <div class="zone">$zone · $foot_k</div>
      <div class="note">$league_teaser</div>
    </div>
    <div class="qr"><div class="qrtile">$qr_svg</div><div class="qrlbl">$qr_lbl</div></div>
  </div>

</div></body></html>""")

TPL_LIGUE = Template(r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Stratos FPV League — saison 1</title>
<style>$css
  .pts { margin-top:3.5mm; display:grid; grid-template-columns:repeat(4,1fr); gap:4mm; }
  .pt { border:1px solid var(--rule,#c7d2e2); border-radius:3mm; padding:3.5mm;
        background:var(--cardbg,#fff); text-align:center; }
  .pt .pl { font-size:8pt; font-weight:800; letter-spacing:.1em; color:var(--mutedtxt,#4a5568); }
  .pt .pv { font-size:17pt; font-weight:800; color:#2f6fed; margin-top:.8mm; }
  .pt.small .pv { font-size:10pt; line-height:1.25; margin-top:1.6mm; }
  .bonus { margin-top:3mm; display:flex; gap:2.5mm; flex-wrap:wrap; }
  .bchip { font-size:8pt; padding:1.2mm 3mm; border-radius:20px;
           border:1px solid var(--rule,#c7d2e2); color:var(--mutedtxt,#4a5568); }
  .prz { margin-top:3.5mm; display:grid; grid-template-columns:1fr 1fr 1fr; gap:4mm; }
  .pz { border:1px solid #e0a300; border-radius:3mm; padding:4mm; background:var(--goldbg,#fff8e6); }
  .pz .m { font-size:16pt; line-height:1; }
  .pz .t { font-size:10pt; font-weight:800; margin-top:1.5mm; color:#7a5200; }
  .pz .d { font-size:8.2pt; color:#6b4a08; margin-top:1mm; line-height:1.3; }
  .t-dark .pz { border-color:#8a6a12; }
  .t-dark .pz .t { color:#f5b942; } .t-dark .pz .d { color:#d8c08a; }
  .xtr { margin-top:3.5mm; display:grid; gap:1.8mm; }
  .xr { display:flex; gap:3mm; font-size:8.8pt; color:var(--mutedtxt,#4a5568); align-items:baseline; }
  .xr i { font-style:normal; font-size:11pt; width:6mm; flex:none; text-align:center; }
</style></head>
<body><div class="page $tcls">

  <div class="hero">
    <img class="bg" src="$hero" alt="">
    <div class="veil"></div>
    <div class="htext">
      <div class="brand">STRATOS<b>DRONES</b></div>
      <div class="eyebrow">$eyebrow</div>
      <h1>$t1<br><span>$t2</span></h1>
      <div class="sub">$sub</div>
    </div>
  </div>

  <div class="body">
    <div class="kicker">$k_fmt</div>
    <div class="grid3">$fmts</div>

    <div class="kicker mt">$k_pts</div>
    <div class="pts">$pts</div>
    <div class="bonus">$bonus</div>

    <div class="kicker mt au">$k_prize</div>
    <div class="prz">$prizes</div>
    <div class="xtr">$extras</div>
  </div>

  <div class="foot">
    <div class="fc">
      <div class="cta">📡 $stay</div>
      <div class="note" style="margin-top:2.5mm">$stay_txt</div>
      <div class="lines"><b>$name</b> · $phone<br>$email<br>$link</div>
      <div class="zone">$zone</div>
    </div>
    <div class="qr"><div class="qrtile">$qr_svg</div><div class="qrlbl">$qr_lbl</div></div>
  </div>

</div></body></html>""")


# ------------------------------------------------------------------ rendu
def cards(items):
    return "".join(
        f'<div class="card"><div class="ic">{ic}</div><div>'
        f'<div class="ct">{t}</div><div class="cd">{d}</div></div></div>'
        for ic, t, d in items)


def build_atelier(theme):
    a = ATELIER
    day = "".join(f'<div class="drow"><time>{h}</time><span>{w}</span></div>'
                  for h, w in a["day"])
    plans = "".join(
        f'<div class="plan{" hi" if hi else ""}"><div class="pn">{n}</div>'
        f'<div class="pp">{p}</div><div class="pd">{d}</div></div>'
        for n, p, d, hi in a["plans"])
    kits = "".join(f'<div class="gkit">{n}<br><b>{p}</b></div>' for n, p in a["kits"])
    return TPL_ATELIER.substitute(
        css=CSS, tcls=f"t-{theme}", hero=HERO_B64,
        eyebrow=a["eyebrow"], t1=a["t1"], t2=a["t2"], sub=a["sub"],
        k_learn=a["k_learn"], learn=cards(a["learn"]),
        k_day=a["k_day"], day=day,
        k_price=a["k_price"], plans=plans,
        kit_title=a["kit_title"], kit_txt=a["kit_txt"], kits=kits,
        name=CONTACT["name"], phone=CONTACT["phone"], email=CONTACT["email"],
        link=CONTACT["link"], zone=CONTACT["zone"], foot_k=a["foot_k"],
        league_teaser=a["league_teaser"], qr_svg=QR_SVG, qr_lbl=a["qr"])


def build_ligue(theme):
    g = LIGUE
    pts = "".join(
        f'<div class="pt{" small" if len(v) > 3 else ""}">'
        f'<div class="pl">{k}</div><div class="pv">{v}</div></div>'
        for k, v in g["pts"])
    bonus = "".join(f'<div class="bchip">{b}</div>' for b in g["bonus"])
    prizes = "".join(
        f'<div class="pz"><div class="m">{m}</div><div class="t">{t}</div>'
        f'<div class="d">{d}</div></div>' for m, t, d in g["prizes"])
    extras = "".join(f'<div class="xr"><i>{i}</i><span>{t}</span></div>'
                     for i, t in g["extras"])
    return TPL_LIGUE.substitute(
        css=CSS, tcls=f"t-{theme}", hero=SHOT_B64,
        eyebrow=g["eyebrow"], t1=g["t1"], t2=g["t2"], sub=g["sub"],
        k_fmt=g["k_fmt"], fmts=cards(g["fmts"]),
        k_pts=g["k_pts"], pts=pts, bonus=bonus,
        k_prize=g["k_prize"], prizes=prizes, extras=extras,
        stay=g["stay"], stay_txt=g["stay_txt"],
        name=CONTACT["name"], phone=CONTACT["phone"], email=CONTACT["email"],
        link=CONTACT["link"], zone=CONTACT["zone"],
        qr_svg=QR_SVG, qr_lbl=g["qr"])


OUT = [
    ("affiche-atelier-dark.html",  build_atelier("dark")),
    ("affiche-atelier-light.html", build_atelier("light")),
    ("affiche-ligue-dark.html",    build_ligue("dark")),
]

MANIFEST = [
    {"html": "affiche-atelier-dark.html",  "out": "affiche-atelier-a4",        "format": "A4", "scale": 1.0},
    {"html": "affiche-atelier-dark.html",  "out": "affiche-atelier-a3",        "format": "A3", "scale": 1.41428},
    {"html": "affiche-atelier-light.html", "out": "affiche-atelier-a4-claire", "format": "A4", "scale": 1.0},
    {"html": "affiche-ligue-dark.html",    "out": "affiche-ligue-a4",          "format": "A4", "scale": 1.0},
    {"html": "affiche-ligue-dark.html",    "out": "affiche-ligue-a3",          "format": "A3", "scale": 1.41428},
]

if __name__ == "__main__":
    for name, html in OUT:
        path = os.path.join(HERE, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"wrote {name}  ({len(html)//1024} kB)")
    with open(os.path.join(HERE, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(MANIFEST, f, indent=2, ensure_ascii=False)
    print("wrote manifest.json")
    print("QR encodes:", CONTACT["url"])
