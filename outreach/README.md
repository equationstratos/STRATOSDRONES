# Outreach kit — « La science des drones »

Supports de communication pour proposer des **interventions / ateliers** autour du projet
Stratos Drones (écoles, collèges, lycées, fablabs, associations, mairies, clubs RC,
revendeurs et constructeurs de drones).

## Contenu

| Fichier | Usage |
|---|---|
| **`affiche-fr-a4.pdf`** | Affiche FR, A4, thème sombre — la version phare (à imprimer / joindre par e-mail). |
| **`affiche-fr-a3.pdf`** | Affiche FR, **A3** — pour panneaux d'affichage. |
| **`affiche-fr-a4-claire.pdf`** | Affiche FR, A4, **thème clair** — économe en encre. |
| **`affiche-en-a4.pdf`** | Affiche **anglaise**, A4, thème sombre. |
| `affiche-*.png` | Aperçus (mêmes visuels, pour un coup d'œil rapide / le web). |
| **`lettre-type-email-fr.md`** | Lettre type e-mail (FR) : 3 objets, version longue + courte, tableau d'adaptation par destinataire. |
| **`email-template-en.md`** | Version anglaise de la lettre. |

Coordonnées intégrées : **Patrick Ardanny · 07 84 84 99 74 ·
stratosdrone001@gmail.com · Bordeaux / toute la France**.
Le **QR code** de l'affiche pointe vers <https://equationstratos.github.io/STRATOSDRONES/>.

> ⚠️ **Avant impression en série : scannez le QR** pour confirmer qu'il ouvre bien le site.
> S'il n'est pas encore en ligne, activez GitHub Pages (workflow `.github/workflows/pages.yml`)
> ou changez la cible dans `make_affiche.py` (variable `CONTACT["url"]`) puis régénérez.

## Régénérer

```bash
python3 outreach/make_affiche.py     # -> 3 HTML autonomes + manifest.json
node    outreach/render.cjs          # -> 4 PDF (A4/A3) + 4 PNG d'aperçu
```

- `make_affiche.py` — génère les affiches ; **édite `CONTACT` / `TEXT`** pour changer les
  coordonnées ou les textes (FR/EN). Réutilise l'image officielle `site/assets/cad/hero.jpg`
  et la charte du site.
- `render.cjs` — pilote Playwright (Chromium headless) : lit `manifest.json` et sort les
  PDF (taille de page + échelle par affiche) et les PNG.
- `tools/qrcodegen.py` — encodeur QR pur-Python **(MIT, Project Nayuki)** vendorisé : le QR
  est calculé hors-ligne et inséré en **SVG vectoriel** (net à n'importe quelle taille,
  aucun réseau, aucune dépendance à installer).

## Licence

Textes et mises en page : © 2026 Patrick Ardanny — réutilisables pour la promotion du projet.
`tools/qrcodegen.py` : MIT (Project Nayuki), voir l'en-tête du fichier.
