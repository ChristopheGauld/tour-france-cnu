from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Tour de France des HU de PEA",
    page_icon="🗺️",
    layout="wide",
)

EXCEL_PATH = Path("Tour090626.xlsx")
PHOTO_DIR = Path("photos")

UNIVERSITES = {
    "Paris Cité": (48.8566, 2.3522),
    "Sorbonne Université": (48.8462, 2.3449),
    "Sorbonne Paris Nord": (48.9060, 2.4500),
    "Paris Saclay": (48.6980, 2.1870),
    "UPEC": (48.7904, 2.4556),
    "Besançon": (47.2378, 6.0241),
    "Dijon": (47.3220, 5.0415),
    "Amiens": (49.8941, 2.2958),
    "Lille": (50.6292, 3.0573),
    "Lyon": (45.7640, 4.8357),
    "Grenoble": (45.1885, 5.7245),
    "Clermont": (45.7772, 3.0870),
    "St Etienne": (45.4397, 4.3872),
    "Saint Etienne": (45.4397, 4.3872),
    "Saint-Étienne": (45.4397, 4.3872),
    "Brest": (48.3904, -4.4861),
    "Rennes": (48.1173, -1.6778),
    "Montpellier": (43.6119, 3.8772),
    "Toulouse": (43.6047, 1.4442),
    "Bordeaux": (44.8378, -0.5792),
    "Limoges": (45.8336, 1.2611),
    "Poitiers": (46.5802, 0.3404),
    "Orléans": (47.9029, 1.9093),
    "Orleans": (47.9029, 1.9093),
    "Tours": (47.3941, 0.6848),
    "Nancy": (48.6921, 6.1844),
    "Reims": (49.2583, 4.0317),
    "Strasbourg": (48.5734, 7.7521),
    "Angers": (47.4784, -0.5632),
    "Nantes": (47.2184, -1.5536),
    "Caen": (49.1829, -0.3707),
    "Rouen": (49.4431, 1.0993),
    "Le Havre": (49.4944, 0.1079),
    "Nice": (43.7102, 7.2620),
    "Marseille": (43.2965, 5.3698),
    "Marseille/Toulon": (43.1242, 5.9280),
    "Réunion": (-20.8789, 55.4481),
    "Reunion": (-20.8789, 55.4481),
    "Antilles Guyane": (14.6161, -61.0588),
}


def normalize_university(value: object) -> str:
    return str(value).replace("\n", " ").strip()


@st.cache_data
def load_data() -> pd.DataFrame:
    if not EXCEL_PATH.exists():
        st.error(f"Le fichier {EXCEL_PATH} est introuvable.")
        st.stop()

    df = pd.read_excel(EXCEL_PATH)

    required_columns = ["Université", "Nom", "Prénom", "Corps", "Ancienneté de grade"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error("Colonnes manquantes dans le fichier Excel : " + ", ".join(missing))
        st.stop()

    df["Université"] = df["Université"].apply(normalize_university)
    df["Nom"] = df["Nom"].astype(str).str.strip()
    df["Prénom"] = df["Prénom"].astype(str).str.strip()
    df["Corps"] = df["Corps"].astype(str).str.strip()

    df["Ancienneté"] = pd.to_datetime(
        df["Ancienneté de grade"],
        errors="coerce",
    ).dt.year

    return df


def find_photo(prenom: str, nom: str) -> Path | None:
    PHOTO_DIR.mkdir(exist_ok=True)
    base = f"{prenom}_{nom}".replace(" ", "_").replace("/", "-")
    for ext in ["jpg", "jpeg", "png", "webp"]:
        path = PHOTO_DIR / f"{base}.{ext}"
        if path.exists():
            return path
    return None


def count_corps(df: pd.DataFrame, pattern: str) -> int:
    return int(df["Corps"].astype(str).str.upper().str.contains(pattern, regex=True, na=False).sum())


st.markdown(
    """
    <style>
    .main-title {
        font-size: 48px;
        font-weight: 800;
        margin-bottom: 0px;
    }
    .subtitle {
        color: #6b7280;
        font-size: 22px;
        margin-bottom: 22px;
    }
    .stats-bar {
        background: linear-gradient(90deg, #8f1d14, #c24124, #d97706);
        color: white;
        padding: 18px 22px;
        border-radius: 18px;
        font-size: 18px;
        margin-bottom: 20px;
        line-height: 1.8;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }
    .photo-placeholder {
        width: 150px;
        height: 150px;
        border: 2px solid #b23a22;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #b23a22;
        font-size: 16px;
        background: rgba(178,58,34,0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">Tour de France CNU</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Carte interactive des universités et des candidats</div>',
    unsafe_allow_html=True,
)

df_original = load_data()
df = df_original.copy()

st.sidebar.header("Filtres")

recherche = st.sidebar.text_input("Rechercher un candidat")

corps_options = sorted(df["Corps"].dropna().unique())
corps_selection = st.sidebar.multiselect(
    "Corps",
    options=corps_options,
    default=corps_options,
)

universites_options = ["Toutes les universités"] + sorted(df["Université"].dropna().unique())
universite_filtre = st.sidebar.selectbox("Université", universites_options)

if corps_selection:
    df = df[df["Corps"].isin(corps_selection)]

if universite_filtre != "Toutes les universités":
    df = df[df["Université"] == universite_filtre]

if recherche:
    mask = (
        df["Nom"].str.contains(recherche, case=False, na=False)
        | df["Prénom"].str.contains(recherche, case=False, na=False)
        | df["Université"].str.contains(recherche, case=False, na=False)
    )
    df = df[mask]

nb_total = len(df)
nb_univ = df["Université"].nunique()
nb_mcuph = count_corps(df, r"MCU\s*-?\s*PH")
nb_puph = count_corps(df, r"PU\s*-?\s*PH")
nb_pat_pa = count_corps(df, r"\bPAT\b|\bPA\b")
nb_phu = count_corps(df, r"\bPHU\b")

st.markdown(
    f"""
    <div class="stats-bar">
        <b>{nb_total}</b> candidats ·
        <b>{nb_univ}</b> universités ·
        <b>{nb_mcuph}</b> MCU-PH ·
        <b>{nb_puph}</b> PU-PH ·
        <b>{nb_pat_pa}</b> PAT/PA ·
        <b>{nb_phu}</b> PHU
    </div>
    """,
    unsafe_allow_html=True,
)

m = folium.Map(
    location=[46.5, 2.2],
    zoom_start=6,
    tiles="CartoDB positron",
)

for univ in sorted(df["Université"].dropna().unique()):
    if univ not in UNIVERSITES:
        continue

    lat, lon = UNIVERSITES[univ]
    n = len(df[df["Université"] == univ])

    folium.CircleMarker(
        location=[lat, lon],
        radius=8 + min(n, 12),
        popup=f"{univ} : {n} candidat(s)",
        tooltip=f"{univ} ({n})",
        color="#7f1d1d",
        fill=True,
        fill_color="#c24124",
        fill_opacity=0.88,
        weight=2,
    ).add_to(m)

st_folium(m, width=None, height=650)

st.markdown("---")

universites_affichage = ["Toutes les universités"] + sorted(df["Université"].dropna().unique())
universite_selectionnee = st.selectbox(
    "Afficher les praticiens de",
    universites_affichage,
)

if universite_selectionnee == "Toutes les universités":
    candidats = df.sort_values(["Université", "Nom", "Prénom"])
    st.header("Toutes les universités")
else:
    candidats = df[df["Université"] == universite_selectionnee].sort_values(["Nom", "Prénom"])
    st.header(universite_selectionnee)

for _, row in candidats.iterrows():
    prenom = str(row["Prénom"]).strip()
    nom = str(row["Nom"]).strip()
    corps = str(row["Corps"]).strip()
    anciennete = row["Ancienneté"]
    universite = str(row["Université"]).strip()

    photo = find_photo(prenom, nom)

    c1, c2 = st.columns([1, 4])

    with c1:
        if photo:
            st.image(str(photo), width=150)
        else:
            st.markdown('<div class="photo-placeholder">Photo</div>', unsafe_allow_html=True)

    with c2:
        st.subheader(f"{prenom} {nom}")
        st.write(f"Université : {universite}")
        st.write(f"Corps : {corps}")

        if pd.notna(anciennete):
            st.write(f"Ancienneté de grade : {int(anciennete)}")
        else:
            st.write("Ancienneté de grade :")

    st.divider()
