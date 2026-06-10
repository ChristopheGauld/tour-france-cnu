from pathlib import Path
import re
import math

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Tour de France CNU", page_icon="🗺️", layout="wide")

DATA_PATH = Path("data/Tour090626.xlsx")
PHOTOS_DIR = Path("photos")

UNIVERSITES = {
    "Paris Cité": {"city": "Paris", "lat": 48.8566, "lon": 2.3522},
    "Sorbonne Université": {"city": "Paris", "lat": 48.8462, "lon": 2.3449},
    "Sorbonne Paris Nord": {"city": "Bobigny", "lat": 48.9060, "lon": 2.4500},
    "Paris Saclay": {"city": "Orsay", "lat": 48.6980, "lon": 2.1870},
    "UPEC": {"city": "Créteil", "lat": 48.7904, "lon": 2.4556},
    "Besançon": {"city": "Besançon", "lat": 47.2378, "lon": 6.0241},
    "Dijon": {"city": "Dijon", "lat": 47.3220, "lon": 5.0415},
    "Amiens": {"city": "Amiens", "lat": 49.8941, "lon": 2.2958},
    "Lille": {"city": "Lille", "lat": 50.6292, "lon": 3.0573},
    "Lyon": {"city": "Lyon", "lat": 45.7640, "lon": 4.8357},
    "Grenoble": {"city": "Grenoble", "lat": 45.1885, "lon": 5.7245},
    "Clermont": {"city": "Clermont-Ferrand", "lat": 45.7772, "lon": 3.0870},
    "St Etienne": {"city": "Saint-Étienne", "lat": 45.4397, "lon": 4.3872},
    "Brest": {"city": "Brest", "lat": 48.3904, "lon": -4.4861},
    "Rennes": {"city": "Rennes", "lat": 48.1173, "lon": -1.6778},
    "Montpellier": {"city": "Montpellier", "lat": 43.6119, "lon": 3.8772},
    "Toulouse": {"city": "Toulouse", "lat": 43.6047, "lon": 1.4442},
    "Bordeaux": {"city": "Bordeaux", "lat": 44.8378, "lon": -0.5792},
    "Limoges": {"city": "Limoges", "lat": 45.8336, "lon": 1.2611},
    "Poitiers": {"city": "Poitiers", "lat": 46.5802, "lon": 0.3404},
    "Orléans": {"city": "Orléans", "lat": 47.9029, "lon": 1.9093},
    "Tours": {"city": "Tours", "lat": 47.3941, "lon": 0.6848},
    "Nancy": {"city": "Nancy", "lat": 48.6921, "lon": 6.1844},
    "Reims": {"city": "Reims", "lat": 49.2583, "lon": 4.0317},
    "Strasbourg": {"city": "Strasbourg", "lat": 48.5734, "lon": 7.7521},
    "Angers": {"city": "Angers", "lat": 47.4784, "lon": -0.5632},
    "Nantes": {"city": "Nantes", "lat": 47.2184, "lon": -1.5536},
    "Caen": {"city": "Caen", "lat": 49.1829, "lon": -0.3707},
    "Rouen": {"city": "Rouen", "lat": 49.4431, "lon": 1.0993},
    "Le Havre": {"city": "Le Havre", "lat": 49.4944, "lon": 0.1079},
    "Nice": {"city": "Nice", "lat": 43.7102, "lon": 7.2620},
    "Marseille": {"city": "Marseille", "lat": 43.2965, "lon": 5.3698},
    "Marseille/Toulon": {"city": "Toulon", "lat": 43.1242, "lon": 5.9280},
    "Réunion": {"city": "Saint-Denis", "lat": -20.8789, "lon": 55.4481},
    "Antilles Guyane": {"city": "Fort-de-France", "lat": 14.6161, "lon": -61.0588},
}


def clean_text(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).replace('"', "")).strip()


def normalize_name(value):
    value = clean_text(value)
    replacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a", "ä": "a",
        "î": "i", "ï": "i",
        "ô": "o", "ö": "o",
        "ù": "u", "û": "u", "ü": "u",
        "ç": "c",
        "É": "E", "È": "E", "Ê": "E", "Ë": "E",
        "À": "A", "Â": "A", "Ä": "A",
        "Î": "I", "Ï": "I",
        "Ô": "O", "Ö": "O",
        "Ù": "U", "Û": "U", "Ü": "U",
        "Ç": "C",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"[^A-Za-z0-9]+", "_", value)
    return value.strip("_")


def photo_path(prenom, nom):
    base = f"{normalize_name(prenom)}_{normalize_name(nom)}"
    for ext in ["jpg", "jpeg", "png", "webp"]:
        p = PHOTOS_DIR / f"{base}.{ext}"
        if p.exists():
            return p
    return None


@st.cache_data(show_spinner=False)
def load_data(path: str):
    df = pd.read_excel(path)
    required = ["Université", "Nom", "Prénom", "Corps", "Ancienneté de grade"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes : {', '.join(missing)}")

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].map(clean_text)

    df["Université"] = df["Université"].map(clean_text)
    df["Nom"] = df["Nom"].map(clean_text)
    df["Prénom"] = df["Prénom"].map(clean_text)
    df["Corps"] = df["Corps"].map(clean_text)

    df["Ancienneté"] = pd.to_datetime(df["Ancienneté de grade"], errors="coerce").dt.year
    df["Ville"] = df["Université"].map(lambda u: UNIVERSITES.get(u, {}).get("city", ""))
    df["lat"] = df["Université"].map(lambda u: UNIVERSITES.get(u, {}).get("lat"))
    df["lon"] = df["Université"].map(lambda u: UNIVERSITES.get(u, {}).get("lon"))
    return df


def distance(a, b, c, d):
    return math.sqrt((a - c) ** 2 + (b - d) ** 2)


def candidate_card(row):
    prenom = row.get("Prénom", "")
    nom = row.get("Nom", "")
    corps = row.get("Corps", "")
    anciennete = row.get("Ancienneté", "")
    p = photo_path(prenom, nom)

    left, right = st.columns([1, 3.5], vertical_alignment="top")
    with left:
        if p:
            st.image(str(p), width=155)
        else:
            st.markdown(
                """
                <div class="photo-placeholder">Photo</div>
                """,
                unsafe_allow_html=True,
            )
    with right:
        st.markdown(f"<div class='candidate-name'>{prenom} {nom}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='candidate-meta'>Corps : {corps}</div>", unsafe_allow_html=True)
        if pd.notna(anciennete) and anciennete != "":
            st.markdown(f"<div class='candidate-meta'>Ancienneté de grade : {int(anciennete)}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='candidate-meta'>Ancienneté de grade : non renseignée</div>", unsafe_allow_html=True)


st.markdown(
    """
    <style>
    .main .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
    .title {font-size: 2.1rem; font-weight: 750; letter-spacing: -0.02em; margin-bottom: .1rem;}
    .subtitle {color: #6B7280; font-size: 1rem; margin-bottom: 1.2rem;}
    .metric-card {background: #F7F7FB; border: 1px solid #E5E7EB; border-radius: 18px; padding: 16px 18px;}
    .metric-number {font-size: 1.7rem; font-weight: 750;}
    .metric-label {font-size: .86rem; color:#6B7280;}
    .candidate-name {font-size: 1.15rem; font-weight: 750; margin-bottom: .35rem;}
    .candidate-meta {font-size: .98rem; color: #374151; line-height: 1.65;}
    .photo-placeholder {width:150px; height:150px; border:1.5px dashed #B8BDC7; border-radius:14px; display:flex; align-items:center; justify-content:center; color:#9CA3AF; background:#FAFAFA;}
    .univ-header {font-size: 1.55rem; font-weight: 760; margin-top: .3rem;}
    .univ-city {color:#6B7280; margin-bottom: 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='title'>Tour de France CNU</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Carte interactive des universités et des candidats</div>", unsafe_allow_html=True)

if not DATA_PATH.exists():
    st.error("Le fichier data/Tour090626.xlsx est introuvable.")
    st.stop()

try:
    data = load_data(str(DATA_PATH))
except Exception as e:
    st.error(str(e))
    st.stop()

with st.sidebar:
    st.header("Filtres")
    search = st.text_input("Rechercher un candidat", placeholder="Nom ou prénom")
    corps_values = sorted([x for x in data["Corps"].dropna().unique() if x])
    selected_corps = st.multiselect("Corps", corps_values, default=corps_values)
    universite_values = sorted([x for x in data["Université"].dropna().unique() if x])
    selected_univs = st.multiselect("Universités", universite_values, default=universite_values)

filtered = data.copy()
if selected_corps:
    filtered = filtered[filtered["Corps"].isin(selected_corps)]
if selected_univs:
    filtered = filtered[filtered["Université"].isin(selected_univs)]
if search:
    s = search.strip()
    filtered = filtered[
        filtered["Nom"].str.contains(s, case=False, na=False)
        | filtered["Prénom"].str.contains(s, case=False, na=False)
        | filtered["Université"].str.contains(s, case=False, na=False)
    ]

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f"<div class='metric-card'><div class='metric-number'>{len(filtered)}</div><div class='metric-label'>candidats</div></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='metric-card'><div class='metric-number'>{filtered['Université'].nunique()}</div><div class='metric-label'>universités</div></div>", unsafe_allow_html=True)
with k3:
    missing_geo = filtered[filtered["lat"].isna()]["Université"].nunique()
    st.markdown(f"<div class='metric-card'><div class='metric-number'>{missing_geo}</div><div class='metric-label'>universités sans coordonnées</div></div>", unsafe_allow_html=True)

map_col, info_col = st.columns([1.35, 1], gap="large")

with map_col:
    france = folium.Map(location=[46.7, 2.3], zoom_start=5.7, tiles="CartoDB positron")
    grouped = filtered.dropna(subset=["lat", "lon"]).groupby("Université", sort=True)
    for univ, group in grouped:
        lat = float(group["lat"].iloc[0])
        lon = float(group["lon"].iloc[0])
        city = group["Ville"].iloc[0]
        n = len(group)
        popup = f"<b>{univ}</b><br>{city}<br>{n} candidat{'s' if n > 1 else ''}"
        folium.CircleMarker(
            location=[lat, lon],
            radius=min(24, 8 + n * 1.8),
            tooltip=f"{univ} · {n} candidat{'s' if n > 1 else ''}",
            popup=folium.Popup(popup, max_width=260),
            color="#4F46E5",
            fill=True,
            fill_color="#4F46E5",
            fill_opacity=0.72,
            weight=2,
        ).add_to(france)

    clicked = st_folium(france, height=690, width=None, returned_objects=["last_object_clicked"])

clicked_univ = None
if clicked and clicked.get("last_object_clicked"):
    lat = clicked["last_object_clicked"].get("lat")
    lon = clicked["last_object_clicked"].get("lng")
    if lat is not None and lon is not None:
        coords = filtered.dropna(subset=["lat", "lon"])[["Université", "lat", "lon"]].drop_duplicates()
        if not coords.empty:
            coords["d"] = coords.apply(lambda r: distance(lat, lon, r["lat"], r["lon"]), axis=1)
            clicked_univ = coords.sort_values("d").iloc[0]["Université"]

with info_col:
    available = sorted(filtered["Université"].dropna().unique())
    if not available:
        st.info("Aucun résultat avec ces filtres.")
        st.stop()

    default_index = available.index(clicked_univ) if clicked_univ in available else 0
    selected_univ = st.selectbox("Université affichée", available, index=default_index)

    univ_df = filtered[filtered["Université"] == selected_univ].sort_values(["Corps", "Nom", "Prénom"])
    city = UNIVERSITES.get(selected_univ, {}).get("city", "")
    st.markdown(f"<div class='univ-header'>{selected_univ}</div>", unsafe_allow_html=True)
    if city:
        st.markdown(f"<div class='univ-city'>📍 {city}</div>", unsafe_allow_html=True)
    st.caption(f"{len(univ_df)} candidat{'s' if len(univ_df) > 1 else ''}")

    for _, row in univ_df.iterrows():
        candidate_card(row)
        st.divider()

with st.expander("Universités sans coordonnées", expanded=False):
    missing = sorted(data[data["lat"].isna()]["Université"].dropna().unique())
    if missing:
        st.write("Ajoutez ces universités dans le dictionnaire `UNIVERSITES` du fichier `app.py` :")
        st.write(missing)
    else:
        st.write("Toutes les universités présentes dans le fichier sont géolocalisées.")
