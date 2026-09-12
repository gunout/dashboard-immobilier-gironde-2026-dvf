#!/usr/bin/env python3
"""
Convertit dvf_plus_d33.csv en JSON compressé (dvf_data.json.gz).
Version ultra-optimisée pour Python 32 bits + conversion Lambert-93 sans pyproj.
"""

import pandas as pd
import gzip
import json
import os
import sys
import gc
import numpy as np
from datetime import datetime

# ---------- CONFIG ----------
INPUT_CSV = "dvf_plus_d33.csv"
OUTPUT_JSON = "dvf_data.json"
OUTPUT_GZ = "dvf_data.json.gz"
CHUNK_SIZE = 20_000

USECOLS = [
    'datemut', 'valeurfonc', 'sbati', 'l_codinsee',
    'libtypbien', 'geompar_x', 'geompar_y', 'codtypbien'
]


# ============================================================
# CONVERSION LAMBERT-93 → WGS84 (sans pyproj)
# ============================================================
def lambert93_to_wgs84(x, y):
    """
    Conversion Lambert-93 (EPSG:2154) → WGS84 (EPSG:4326).
    Formule officielle IGN. Précision ~1 m.
    """
    n = 0.7256077650532670
    C = 11754255.426096
    xs = 700000.0
    ys = 12655612.049876
    lon0 = 3.0 * np.pi / 180.0

    e = 0.0818191910435

    dx = x - xs
    dy = y - ys
    R = np.sqrt(dx**2 + dy**2)
    gamma = np.arctan(-dx / dy)

    latiso = np.log(C / R) / n

    phi = 2.0 * np.arctan(np.exp(latiso)) - np.pi / 2.0
    for _ in range(6):
        phi = 2.0 * np.arctan(
            ((1 + e * np.sin(phi)) / (1 - e * np.sin(phi)))**(e / 2.0)
            * np.exp(latiso)
        ) - np.pi / 2.0

    lon = lon0 + gamma / n

    return np.degrees(phi), np.degrees(lon)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    if not os.path.exists(INPUT_CSV):
        log(f"❌ Fichier introuvable : {INPUT_CSV}")
        sys.exit(1)

    # ---------- 1. DÉTECTION DES COLONNES ----------
    log(f"🔍 Lecture de l'en-tête de {INPUT_CSV}…")
    with open(INPUT_CSV, 'r', encoding='utf-8', errors='replace') as f:
        header = f.readline().strip()
    colonnes_dispo = [c.strip().strip('"') for c in header.split('|')]
    log(f"   → {len(colonnes_dispo)} colonnes détectées")

    usecols_present = [c for c in USECOLS if c in colonnes_dispo]
    log(f"   → Colonnes utiles trouvées : {usecols_present}")

    if 'datemut' not in usecols_present or 'valeurfonc' not in usecols_present:
        log(f"❌ Colonnes essentielles manquantes. Disponibles : {colonnes_dispo[:20]}")
        sys.exit(1)

    log("✅ Conversion Lambert-93 → WGS84 en Python pur (formule IGN)")

    # ---------- 2. LECTURE EN CHUNKS ----------
    log(f"📖 Lecture en morceaux de {CHUNK_SIZE:,} lignes…")

    total_lignes = 0
    total_gardees = 0
    stats = {
        'invalid': 0,
        'not_house_appart': 0,
        'out_of_price': 0,
        'out_of_gironde': 0,
    }

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f_out:
        f_out.write('[')
        premier = True

        reader = pd.read_csv(
            INPUT_CSV,
            sep='|',
            usecols=usecols_present,
            low_memory=False,
            on_bad_lines='skip',
            encoding='utf-8',
            quotechar='"',
            chunksize=CHUNK_SIZE,
            engine='c',
        )

        for i, chunk in enumerate(reader):
            total_lignes += len(chunk)

            chunk.rename(columns={
                'datemut': 'date_mutation',
                'valeurfonc': 'valeur_fonciere',
                'sbati': 'surface_reelle_bati',
                'l_codinsee': 'code_commune',
                'libtypbien': 'type_libelle',
                'geompar_x': 'x_lambert',
                'geompar_y': 'y_lambert',
                'codtypbien': 'codtypbien',
            }, inplace=True, errors='ignore')

            chunk['date_mutation'] = pd.to_datetime(chunk['date_mutation'], errors='coerce')
            chunk['valeur_fonciere'] = pd.to_numeric(chunk['valeur_fonciere'], errors='coerce')
            chunk['surface_reelle_bati'] = pd.to_numeric(chunk['surface_reelle_bati'], errors='coerce')

            before = len(chunk)
            chunk = chunk.dropna(subset=['valeur_fonciere', 'surface_reelle_bati', 'date_mutation'])
            chunk = chunk[chunk['surface_reelle_bati'] > 0]
            stats['invalid'] += before - len(chunk)

            if len(chunk) == 0:
                del chunk; gc.collect(); continue

            if 'type_libelle' in chunk.columns:
                lib = chunk['type_libelle'].astype(str).str.upper()
                chunk['type_local'] = np.where(
                    lib.str.contains('MAISON', na=False), 'Maison',
                    np.where(lib.str.contains('APPARTEMENT', na=False), 'Appartement', 'Autre')
                )
            elif 'codtypbien' in chunk.columns:
                cod = pd.to_numeric(chunk['codtypbien'], errors='coerce')
                chunk['type_local'] = np.where(
                    cod == 111, 'Maison',
                    np.where(cod == 121, 'Appartement', 'Autre')
                )
            else:
                chunk['type_local'] = 'Inconnu'

            before = len(chunk)
            chunk = chunk[chunk['type_local'].isin(['Maison', 'Appartement'])]
            stats['not_house_appart'] += before - len(chunk)

            if len(chunk) == 0:
                del chunk; gc.collect(); continue

            chunk['prix_m2'] = chunk['valeur_fonciere'] / chunk['surface_reelle_bati']
            before = len(chunk)
            chunk = chunk[(chunk['prix_m2'] > 200) & (chunk['prix_m2'] < 15000)]
            stats['out_of_price'] += before - len(chunk)

            if len(chunk) == 0:
                del chunk; gc.collect(); continue

            chunk['code_commune'] = chunk['code_commune'].astype(str).str.zfill(5)

            # ---------- COORDONNÉES ----------
            lat = np.full(len(chunk), np.nan)
            lon = np.full(len(chunk), np.nan)

            if 'x_lambert' in chunk.columns and 'y_lambert' in chunk.columns:
                x = pd.to_numeric(chunk['x_lambert'], errors='coerce').values
                y = pd.to_numeric(chunk['y_lambert'], errors='coerce').values
                mask = ~np.isnan(x) & ~np.isnan(y)

                if mask.any():
                    lat_v, lon_v = lambert93_to_wgs84(x[mask], y[mask])
                    lat[mask] = lat_v
                    lon[mask] = lon_v

            chunk['latitude'] = lat
            chunk['longitude'] = lon

            before = len(chunk)
            chunk = chunk[
                (chunk['latitude'].between(44.0, 45.7)) &
                (chunk['longitude'].between(-1.4, 0.5))
            ]
            stats['out_of_gironde'] += before - len(chunk)

            if len(chunk) == 0:
                del chunk; gc.collect(); continue

            cols_finales = ['date_mutation', 'valeur_fonciere', 'surface_reelle_bati',
                            'prix_m2', 'code_commune', 'type_local', 'latitude', 'longitude']
            chunk = chunk[[c for c in cols_finales if c in chunk.columns]].copy()

            chunk['date_mutation'] = chunk['date_mutation'].dt.strftime('%Y-%m-%d')
            chunk['valeur_fonciere'] = chunk['valeur_fonciere'].round(0).astype('Int64')
            chunk['surface_reelle_bati'] = chunk['surface_reelle_bati'].round(0).astype('Int64')
            chunk['prix_m2'] = chunk['prix_m2'].round(0).astype('Int64')
            chunk['code_commune'] = chunk['code_commune'].astype(str)
            chunk['type_local'] = chunk['type_local'].astype(str)

            chunk = chunk.where(pd.notna(chunk), None)

            for rec in chunk.to_dict(orient='records'):
                if not premier:
                    f_out.write(',')
                f_out.write(json.dumps(rec, ensure_ascii=False, separators=(',', ':')))
                premier = False

            total_gardees += len(chunk)

            if (i + 1) % 50 == 0:
                log(f"   → {total_lignes:,} lues, {total_gardees:,} gardées…")

            del chunk, lat, lon
            gc.collect()

        f_out.write(']')

    log(f"\n📊 Résumé :")
    log(f"   Total lues            : {total_lignes:,}")
    log(f"   Invalides             : {stats['invalid']:,}")
    log(f"   Non Maison/Appart.    : {stats['not_house_appart']:,}")
    log(f"   Hors plage de prix    : {stats['out_of_price']:,}")
    log(f"   Hors Gironde          : {stats['out_of_gironde']:,}")
    log(f"   ✅ Conservées         : {total_gardees:,}")

    taille_json = os.path.getsize(OUTPUT_JSON) / 1024 / 1024
    log(f"\n💾 JSON brut : {taille_json:.1f} Mo")

    log(f"🗜️  Compression GZIP…")
    with open(OUTPUT_JSON, 'rb') as f_in:
        with gzip.open(OUTPUT_GZ, 'wb', compresslevel=9) as f_out:
            while True:
                bloc = f_in.read(1024 * 1024)
                if not bloc:
                    break
                f_out.write(bloc)

    taille_gz = os.path.getsize(OUTPUT_GZ) / 1024 / 1024
    log(f"   → {taille_gz:.1f} Mo (ratio {taille_json / taille_gz:.1f}x)")

    os.remove(OUTPUT_JSON)
    log(f"\n🧹 {OUTPUT_JSON} supprimé")
    log(f"\n✅ Terminé ! Fichier prêt : {OUTPUT_GZ}")


if __name__ == "__main__":
    main()
