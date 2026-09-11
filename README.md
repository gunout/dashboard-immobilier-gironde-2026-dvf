# 🏘️ Dashboard Immobilier Gironde 2026

> Dashboard interactif de visualisation des transactions immobilières en Gironde, basé sur les données DVF (Demandes de Valeurs Foncières) officielles.

[![Made with](https://img.shields.io/badge/Made%20with-HTML%20%2F%20JS-blue)](https://developer.mozilla.org/fr/docs/Web/JavaScript)
[![Data](https://img.shields.io/badge/Data-DVF%20Gironde-green)](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Zone](https://img.shields.io/badge/Zone-Gironde%20(33)-orange)](https://fr.wikipedia.org/wiki/Gironde)
[![Transactions](https://img.shields.io/badge/Transactions-301%20978-blueviolet)](#)

---

## 📖 Description

Ce projet transforme les données ouvertes **DVF** (Demandes de Valeurs Foncières) de la Gironde en un **dashboard web interactif** permettant d'explorer plus de **300 000 transactions immobilières** :

- 🗺️ **Carte interactive** avec clustering des marqueurs
- 📊 **Graphiques dynamiques** (distribution, évolution, comparaison)
- 🔍 **Filtres** par commune, type de bien, prix, période
- 📋 **Tableau des dernières transactions**
- 📤 **Export PNG/JPG** de chaque graphique
- ⚡ **Chargement ultra-rapide** grâce à la compression GZIP

---

## 📸 Aperçu

![Dashboard Immobilier Gironde 2026](https://github.com/user-attachments/assets/55d94980-de87-4982-96de-a92e72641658)

*Vue d'ensemble du dashboard — carte interactive, KPIs, graphiques et tableau des dernières transactions.*

---

## ✨ Fonctionnalités

### 🗺️ Carte interactive
- Marqueurs colorés selon le **prix au m²** (dégradé vert → jaune → rouge)
- **Taille des marqueurs** proportionnelle à la surface du bien
- **Clustering automatique** pour rester fluide avec des milliers de points
- **Popups détaillées** : date, type, prix, surface, prix/m²
- **Échantillonnage intelligent** : plus de points affichés quand une commune est sélectionnée

### 📈 Graphiques

| Graphique | Description |
|---|---|
| **Histogramme** | Distribution des prix au m² (40 bins) |
| **Camembert** | Répartition Maison vs Appartement |
| **Courbe temporelle** | Évolution mensuelle du prix/m² moyen |
| **Barres comparatives** | Prix moyen vs médian par type de bien |

### 🎛️ Filtres
- **Commune** (liste triée par volume de transactions)
- **Type de bien** : Tous / Maison / Appartement
- **Fourchette de prix** : min / max
- **Période** : dates min / max
- **Mode d'affichage carte** : Auto / Tous / 2000 / 5000 points

### 📋 KPIs en temps réel
- Prix/m² moyen
- Prix médian
- Nombre de transactions
- Surface moyenne

---

## 🛠️ Technologies

| Technologie | Usage |
|---|---|
| **HTML / CSS / JS** | Interface (aucun framework) |
| **Leaflet 1.9** | Carte interactive |
| **Leaflet.markercluster** | Clustering des marqueurs |
| **Chart.js 4** | Graphiques |
| **Pako 2** | Décompression GZIP (fallback) |
| **DecompressionStream API** | Décompression GZIP native |
| **Python 3.8+** | Script de conversion |
| **pandas / numpy** | Traitement des données |

**Aucune dépendance npm, aucun build.** Le projet fonctionne tel quel.

---

## 📁 Structure du projet

    Dashboard-Immobilier-Gironde-2026/
    ├── index.html # Dashboard web (fichier unique)
    ├── dvf_data.json.gz # Données compressées (~9.6 Mo)
    ├── convert.py # Script Python de conversion CSV → JSON.GZ
    ├── README.md # Ce fichier
    ├── LICENSE # Licence MIT
    └── docs/
    └── screenshot.png # Capture d'écran

---

## 🚀 Installation

### Prérequis
- **Python 3.8+** (pour servir le dashboard)
- **Navigateur moderne** (Chrome, Firefox, Edge, Safari récents)
- **~2 Go de RAM** libres (si vous régénérez les données)

### 1️⃣ Cloner le dépôt

```bash
git clone https://github.com/VOTRE-USERNAME/Dashboard-Immobilier-Gironde-2026.git
cd Dashboard-Immobilier-Gironde-2026
```
2️⃣ Lancer le dashboard

    ⚠️ Important : le dashboard doit être servi via un serveur HTTP. Le protocole file:// ne permet pas le chargement GZIP.

```bash

python -m http.server 8000
```

Puis ouvrir : 
     
    http://localhost:8000


### 📖 Utilisation

Interface principale

    Sélectionner une commune dans le panneau de gauche (ou laisser "Toutes les communes")

    Ajuster les filtres : type de bien, fourchette de prix, période

    Cliquer sur "Appliquer" (ou changer la commune — le filtre s'applique automatiquement)

    Explorer la carte : zoom, clic sur les marqueurs pour les détails

    Consulter les graphiques qui se mettent à jour en temps réel

Mode d'affichage carte
Mode	Description
Auto (recommandé)	3 000 points en vue globale, 8 000 si une commune est sélectionnée
Tous les points	⚠️ Lent (peut prendre 5-10 sec)
2000 / 5000 points	Échantillonnage fixe
Export des graphiques

Chaque graphique dispose de boutons PNG et JPG pour l'exporter.
🔬 Détails techniques
Format des données

dvf_data.json.gz est un tableau JSON de la forme :
json

[
  {
    "date_mutation": "2023-01-15",
    "valeur_fonciere": 250000,
    "surface_reelle_bati": 85,
    "prix_m2": 2941,
    "code_commune": "33063",
    "type_local": "Appartement",
    "latitude": 44.8378,
    "longitude": -0.5792
  }
]

Compression GZIP : ratio ~6:1 (58.9 Mo → 9.6 Mo)
Conversion Lambert-93 → WGS84

La conversion est faite en Python pur (sans pyproj), avec la formule officielle IGN. Précision ~1 mètre, aucune dépendance externe.
Décompression GZIP côté navigateur

Deux stratégies pour compatibilité maximale :
javascript

if (typeof DecompressionStream !== 'undefined') {
    // API native (Chrome 80+, Firefox 113+, Safari 16.4+)
    const ds = new DecompressionStream('gzip');
    const stream = response.body.pipeThrough(ds);
    text = await new Response(stream).text();
} else if (typeof pako !== 'undefined') {
    // Fallback via pako
    const buffer = await response.arrayBuffer();
    text = pako.ungzip(new Uint8Array(buffer), { to: 'string' });
}

📊 Source des données

Les données proviennent du fichier DVF+ (Demandes de Valeurs Foncières) publié par la DGFiP :

    🔗 Source officielle : data.gouv.fr - DVF

    🔗 Fichier filtré Gironde : GitHub Releases

    📅 Période couverte : 2014 → 2024

    📍 Zone : Gironde (33)

Nettoyage appliqué
Étape	Règle
Dates	Suppression des dates invalides
Valeur foncière	> 0
Surface	> 0 m²
Type de bien	Uniquement Maison (111) et Appartement (121)
Prix/m²	Entre 200 € et 15 000 €
Coordonnées	Dans la fenêtre Gironde [44.0, 45.7] × [-1.4, 0.5]
Statistiques du fichier
Métrique	Valeur
Lignes brutes	465 409
Transactions valides	301 978
Communes	~100
Prix/m² moyen	~3 000 €
Taille JSON.GZ	9.6 Mo
🧪 Tests rapides
Vérifier que le JSON se charge correctement
bash

curl http://localhost:8000/dvf_data.json.gz | gunzip | head -c 500

Vérifier la version de Python
bash

python --version
python -c "import platform; print(platform.architecture())"

🐛 Problèmes connus
Problème	Cause	Solution
HTTP 404 sur dvf_data.json.gz	Fichier manquant	Vérifier qu'il est dans le même dossier que index.html
Aucun décompresseur GZIP	Navigateur ancien	Utiliser Chrome/Firefox/Edge récent
out of memory en conversion	Python 32 bits	Réduire CHUNK_SIZE à 10 000
pip install pyproj échoue	Python 32 bits	Le script n'en a plus besoin (formule IGN intégrée)
Carte vide	Coordonnées invalides	Vérifier la console navigateur (F12)
🗺️ Roadmap

    □

    Croisement avec IRCOM : prix immobilier × revenus fiscaux × votes
    □

    Carte de chaleur : alternative aux marqueurs pour 300k points
    □

    Comparateur de communes côte à côte
    □

    Analyse par IRIS dans Bordeaux (données plus fines)
    □

    Déploiement GitHub Pages automatique
    □

    Tests automatisés (Playwright)
    □

    Mode sombre
    □

    Internationalisation (FR / EN)

🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

    Fork le projet

    Créer une branche (git checkout -b feature/ma-fonctionnalite)

    Commit (git commit -m 'Ajout de ma fonctionnalité')

    Push (git push origin feature/ma-fonctionnalite)

    Ouvrir une Pull Request

Style de code

    JavaScript : ES2020+, pas de framework, commentaires en français

    Python : PEP 8, commentaires en français

    HTML/CSS : classes sémantiques, CSS moderne (grid/flex)

📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

Les données DVF sont publiées sous Licence Ouverte / Open Licence 2.0 par la DGFiP.
👤 Auteur

Votre Nom

    GitHub : @VOTRE-USERNAME

    Email : votre.email@example.com

🙏 Remerciements

    DGFiP pour la publication des données DVF

    data.gouv.fr pour la plateforme open data

    Leaflet pour la bibliothèque cartographique

    Chart.js pour les graphiques

    pako pour la décompression GZIP

    IGN pour la formule officielle Lambert-93

📚 Ressources

    📖 Documentation DVF

    📖 Comprendre les prix immobiliers

    📖 Lambert-93 (EPSG:2154)

    📖 WGS84 (EPSG:4326)
