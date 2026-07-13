# 01 — Projet KiCad + bibliothèques

Objectif : créer le projet, et rendre disponibles **tous** les symboles et
empreintes nécessaires — dont les **3 composants vendored** du repo qui n'existent
pas dans les bibliothèques KiCad standard (ESP32-P4, ESP32-C6-MINI-1, PMW3901).

## 1. Installer KiCad 9 (si nécessaire)

- **Linux** : `sudo add-apt-repository ppa:kicad/kicad-9.0-releases && sudo apt update && sudo apt install kicad`
  (ou le paquet de ta distro / Flatpak `org.kicad.KiCad`).
- **Windows / macOS** : installeur depuis <https://www.kicad.org/download/>.

Vérifie la version dans **Aide → À propos** : il faut **9.x**.

## 2. Créer le projet

Tu as déjà lancé KiCad avec un nouveau projet. Sinon :

1. **Fichier → Nouveau projet…**
2. Nomme-le par ex. `stratosdrone_main` et enregistre-le **dans un dossier à toi**
   (pas dans le repo — le repo contient déjà `stratosdrone.kicad_pcb`).
   > Astuce : garde ce guide + le dossier `../lib/` accessibles à côté.
3. KiCad crée `stratosdrone_main.kicad_pro`, `.kicad_sch`, `.kicad_pcb`.

## 3. Renseigner le cartouche (title block)

Ouvre l'éditeur de schéma (**icône « Schematic Editor »**), puis
**Fichier → Mise en page… (Page Settings)** :

- Format : **A4**
- Titre : `STRATOSDRONE`
- Société : `Equation Stratos`
- Révision : `1.0`

## 4. Ajouter la bibliothèque de **symboles** vendored

Les symboles ESP32-P4 et ESP32-C6-MINI-1 sont dans `../lib/Espressif.kicad_sym`.

1. Éditeur de schéma → **Préférences → Gérer les bibliothèques de symboles**.
2. Onglet **Projet spécifique** (pour ne l'ajouter qu'à ce projet).
3. Clique **+** (Ajouter une ligne existante), puis l'icône dossier, et choisis :
   `…/hardware/pcb/lib/Espressif.kicad_sym`
4. Mets le **Nickname** = `Espressif`. Valide.

Les symboles utiles dans cette lib :
- **`Espressif:ESP32-P4`** → pour U1.
- **`Espressif:ESP32-C6-MINI-1/U`** → pour U3.

> Pour **U9 (PMW3901)**, il n'y a pas de symbole vendored : tu utiliseras un
> symbole générique (ch. 05). Seule son **empreinte** est vendored.

## 5. Ajouter les bibliothèques d'**empreintes** vendored

Deux dossiers `.pretty` dans `../lib/` :

| Dossier | Nickname à donner | Contient |
|---------|-------------------|----------|
| `../lib/Espressif.pretty` | `Espressif` | `ESP32-P4`, `ESP32-C6-MINI-1` |
| `../lib/strat.pretty` | `strat` | `PMW3901MB-TXQT` |

1. Ouvre l'éditeur de PCB (**PCB Editor**) → **Préférences → Gérer les
   bibliothèques d'empreintes**.
2. Onglet **Projet spécifique** → **+** → dossier → choisis
   `…/hardware/pcb/lib/Espressif.pretty`, Nickname = `Espressif`.
3. Recommence pour `…/hardware/pcb/lib/strat.pretty`, Nickname = `strat`.

> ℹ️ Dans `design.py`, ces empreintes sont notées `strat:ESP32-P4`, etc. — c'est
> juste l'étiquette interne du générateur. Physiquement, l'empreinte ESP32-P4 est
> dans `Espressif.pretty`. La fiche **[fiches/empreintes.md](fiches/empreintes.md)**
> donne, pour chaque empreinte, sa bibliothèque et le composant qui l'utilise.

## 6. Empreintes KiCad standard

Toutes les autres empreintes (`Resistor_SMD:R_0402_1005Metric`,
`Capacitor_SMD:C_0402_1005Metric`, `Package_TO_SOT_SMD:SOT-23-5`,
`Package_SO:SOIC-8…`, `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`,
`Sensor_Distance:ST_VL53L1x`, etc.) sont **livrées avec KiCad 9** : rien à
installer, elles apparaîtront dans le sélecteur d'empreintes. La liste complète
est dans **[fiches/empreintes.md](fiches/empreintes.md)**.

## 7. (Optionnel) Modèles 3D

Pour voir les composants en 3D, suis **[`../KICAD9_3D_SETUP.md`](../KICAD9_3D_SETUP.md)**
(configuration des chemins de modèles 3D sous KiCad 9). Ce n'est pas nécessaire
pour router ni fabriquer.

## Récap

- ✅ Projet créé (hors repo), cartouche rempli.
- ✅ Symboles : lib `Espressif` ajoutée (P4 + C6).
- ✅ Empreintes : libs `Espressif` et `strat` ajoutées + standard KiCad dispo.

➡️ On attaque le schéma par l'alimentation :
**[02_schema_alimentation.md](02_schema_alimentation.md)**
