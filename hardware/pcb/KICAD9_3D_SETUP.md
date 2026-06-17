# KiCad 9 — Configuration des modèles 3D

## Problème
Les composants 3D n'apparaissent pas dans KiCad 9, alors qu'ils étaient visibles précédemment.

## Solution: Configurer les chemins des modèles 3D

### Étape 1: Ouvrir les paramètres du projet
```
File → Project Settings
```

### Étape 2: Configurer les chemins
```
Configure Paths (ou "Manage Paths")
```

### Étape 3: Ajouter/Vérifier KICAD6_3DMODEL_DIR

**Linux (KiCad nightly/9):**
```
${HOME}/.kicad_nightly/3dmodels
ou
${HOME}/.local/share/kicad/9.0/3dmodels
```

**macOS:**
```
~/Library/Application Support/kicad/9.0/3dmodels
```

**Windows:**
```
%APPDATA%\kicad\9.0\3dmodels
ou
C:\Users\<YourUsername>\AppData\Roaming\kicad\9.0\3dmodels
```

### Étape 4: Télécharger les modèles (si absent)

**Option A: Via KiCad GUI**
```
Preferences → Manage 3D Models → Download Missing
```

**Option B: Via terminal (Linux/macOS)**
```bash
# KiCad 7/8
mkdir -p ~/.kicad_nightly/3dmodels

# Ou pour KiCad 9
mkdir -p ~/.local/share/kicad/9.0/3dmodels

# Cloner la bibliothèque officielle
git clone https://github.com/KiCad/kicad-3d-models.git \
  ~/.local/share/kicad/9.0/3dmodels/
```

### Étape 5: Vérifier les empreintes

Certains composants utilisent des empreintes **génériques** sans modèle 3D officiel:
- **U9 (PMW3901)**: Empreinte custom (lib/strat.pretty/) → pas de modèle 3D
- **U6 (ICM-42688)**: DHVQFN-14 générique → modèle basique uniquement

### Étape 6: Afficher les modèles 3D dans KiCad

Une fois configuré:
```
View → 3D Viewer
ou
Alt + 3
```

Puis:
```
Preferences (dans le 3D Viewer) → 
Render settings → Check "Show Models" ✓
```

## Modèles 3D fournis dans ce projet

Les composants avec modèles officiels incluent:
- ESP32-P4 (U1)
- VL53L1X (U8) — officiel ST
- SPL06-001 (U7) — officiel Bosch
- Connecteurs USB-C, FFC
- Cristal 40 MHz
- Inductances communes
- Résistances/Capacités standard SMD

## Dépannage

| Problème | Solution |
|----------|----------|
| Aucun modèle ne s'affiche | Vérifier le chemin KICAD6_3DMODEL_DIR dans Project Settings |
| Modèle partiel | Télécharger les modèles manquants (voir Étape 4) |
| "Model not found" | L'empreinte n'a pas de modèle → normal pour composants custom |
| KiCad 9 plante au 3D | Réduire la qualité de rendu: Preferences → Render → Lower quality |

## Pour ce projet (STRATOSDRONE)

**Fichiers créés:**
- `stratosdrone.kicad_sch` — Schématique (111 composants)
- `stratosdrone.kicad_pcb` — PCB avec placement/zones
- `stratosdrone.kicad_pro` — Projet (ajuste les chemins ici)

**Prochaine étape:**
```
1. Ouvrir stratosdrone.kicad_pro dans KiCad 9
2. Configurer chemin 3D (voir Étape 1-3 ci-dessus)
3. Alt + 3 pour voir les modèles 3D
4. Terminer le routage des signaux
5. Re-exporter les gerbers
```

---

**Note:** KiCad 9 a changé la structure des chemins par rapport à KiCad 8. Si tu utilises KiCad 8, remplace `9.0` par `8.0` dans les chemins ci-dessus.
