from pathlib import Path
import re
import unicodedata

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(
    page_title="Tour de France des HU de PEA",
    page_icon="🗺️",
    layout="wide",
)

GOOGLE_SHEET_CSV = "https://docs.google.com/spreadsheets/d/17u0RMvtud4-uERfHmyb5N_FGqZSLlIQloUTxPtUg2e0/export?format=csv&gid=0"
PHOTO_DIRS = [Path("photo"), Path("photos")]


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


def clean_name(value: object) -> str:
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def find_photo(prenom: str, nom: str) -> Path | None:
    target_1 = clean_name(f"{prenom}_{nom}")
    target_2 = clean_name(f"{prenom}{nom}")

    for folder in PHOTO_DIRS:
        if not folder.exists():
            continue

        for file in folder.iterdir():
            if not file.is_file():
                continue

            if file.suffix.lower().replace(".", "") not in ["jpg", "jpeg", "png", "webp"]:
                continue

            stem = clean_name(file.stem)

            if stem in [target_1, target_2]:
                return file

    return None


@st.cache_data
def load_data() -> pd.DataFrame:

    df = pd.read_csv(GOOGLE_SHEET_CSV)

    required_columns = ["Université", "Nom", "Prénom", "Corps", "Nomination"]
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        st.error(
            "Colonnes manquantes dans le Google Sheet : "
            + ", ".join(missing)
        )
        st.stop()

    df["Université"] = df["Université"].apply(normalize_university)
    df["Nom"] = df["Nom"].astype(str).str.strip()
    df["Prénom"] = df["Prénom"].astype(str).str.strip()
    df["Corps"] = df["Corps"].astype(str).str.strip()
    df["Nomination_année"] = pd.to_numeric(
        df["Nomination"],
        errors="coerce"
    ).astype("Int64")

    return df


def count_corps(df: pd.DataFrame, pattern: str) -> int:
    return int(
        df["Corps"]
        .astype(str)
        .str.upper()
        .str.contains(pattern, regex=True, na=False)
        .sum()
    )


def practitioner_line(row: pd.Series, with_year: bool = True) -> str:
    prenom = str(row["Prénom"]).strip()
    nom = str(row["Nom"]).strip()
    corps = str(row["Corps"]).strip()
    annee = row["Nomination_année"]

    if with_year and pd.notna(annee):
        return f"{prenom} {nom}, {corps} ({int(annee)})"

    return f"{prenom} {nom}, {corps}"


def popup_html(univ: str, data: pd.DataFrame) -> str:
    lignes = "<br>".join(
        practitioner_line(row, with_year=True)
        for _, row in data.sort_values(["Nom", "Prénom"]).iterrows()
    )

    return f"""
    <div style="font-family: Arial; font-size: 14px; width: 360px;">
        <h4 style="margin:0 0 8px 0;">{univ}</h4>
        <p style="margin:0 0 8px 0;"><b>{len(data)}</b> praticien(s)</p>
        <p style="margin:0;">{lignes}</p>
    </div>
    """


def photo_placeholder():
    st.markdown(
        """
        <div style="
            width:150px;
            height:150px;
            border:2px solid #b23a22;
            border-radius:14px;
            display:flex;
            align-items:center;
            justify-content:center;
            color:#b23a22;
            font-size:16px;
            background:rgba(178,58,34,0.06);
        ">
            Photo
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    .main-title {
        font-size: 46px;
        font-weight: 800;
        margin-bottom: 0px;
    }

    .subtitle {
        color: #6b7280;
        font-size: 21px;
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

    .selected-box {
        background: linear-gradient(
            135deg,
            #7f1d1d,
            #b91c1c,
            #dc2626
        );
        color: white;
        padding: 22px;
        border-radius: 18px;
        margin-top: 18px;
        margin-bottom: 22px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }

    .selected-box h3,
    .selected-box p {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="main-title">Tour de France des HU de PEA</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">Carte interactive des universités et des praticiens</div>',
    unsafe_allow_html=True,
)


df_original = load_data()
st.write("Google Sheet chargé")
df = df_original.copy()


st.sidebar.header("Filtres")

recherche = st.sidebar.text_input("Rechercher un praticien")

corps_options = sorted(df["Corps"].dropna().unique())
corps_selection = st.sidebar.multiselect(
    "Corps",
    options=corps_options,
    default=corps_options,
)

universites_options = ["Toutes les universités"] + sorted(df["Université"].dropna().unique())
universite_filtre = st.sidebar.selectbox(
    "Université",
    universites_options,
)

if corps_selection:
    df = df[df["Corps"].isin(corps_selection)]

if universite_filtre != "Toutes les universités":
    df = df[df["Université"] == universite_filtre]

if recherche:
    mask = (
        df["Nom"].str.contains(recherche, case=False, na=False)
        | df["Prénom"].str.contains(recherche, case=False, na=False)
        | df["Université"].str.contains(recherche, case=False, na=False)
        | df["Corps"].str.contains(recherche, case=False, na=False)
        | df["Nomination_année"].astype(str).str.contains(recherche, case=False, na=False)
    )
    df = df[mask]


total = len(df)
nb_univ = df["Université"].nunique()

nb_mcuph = count_corps(df, r"MCU")
nb_puph = count_corps(df, r"PU-PH|PUPH")
nb_pat_pa = count_corps(df, r"\bPAT\b|\bPA\b")
nb_phu = count_corps(df, r"PHU")

nb_photos = sum(
    find_photo(row["Prénom"], row["Nom"]) is not None
    for _, row in df.iterrows()
)


st.markdown(
    f"""
    <div class="stats-bar">
        <b>{total}</b> praticiens ·
        <b>{nb_univ}</b> universités ·
        <b>{nb_mcuph}</b> MCU-PH ·
        <b>{nb_puph}</b> PU-PH ·
        <b>{nb_pat_pa}</b> PAT/PA ·
        <b>{nb_phu}</b> PHU ·
    </div>
    """,
    unsafe_allow_html=True,
)


m = folium.Map(
    location=[46.6, 2.3],
    zoom_start=6,
    tiles="CartoDB positron",
)

for univ in sorted(df["Université"].dropna().unique()):
    if univ not in UNIVERSITES:
        continue

    data_univ = df[df["Université"] == univ].sort_values(["Nom", "Prénom"])
    lat, lon = UNIVERSITES[univ]
    n = len(data_univ)

    if n <= 2:
        fill_color = "#facc15"
    elif n <= 5:
        fill_color = "#f97316"
    else:
        fill_color = "#dc2626"

    folium.Marker(
        location=[lat, lon],
        tooltip=f"{univ} ({n})",
        popup=folium.Popup(popup_html(univ, data_univ), max_width=440),
        icon=folium.DivIcon(
            html=f"""
            <div style="
                background:{fill_color};
                color:white;
                border:3px solid #7f1d1d;
                border-radius:50%;
                width:44px;
                height:44px;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:15px;
                font-weight:800;
                box-shadow:0 2px 8px rgba(0,0,0,0.35);
            ">
                {n}
            </div>
            """
        ),
    ).add_to(m)


map_data = st_folium(
    m,
    width=None,
    height=650,
    returned_objects=["last_object_clicked_tooltip"],
)


clicked_univ = None
if map_data and map_data.get("last_object_clicked_tooltip"):
    tooltip_value = map_data["last_object_clicked_tooltip"]
    clicked_univ = tooltip_value.split(" (")[0]


st.markdown("---")


if clicked_univ and clicked_univ in sorted(df["Université"].dropna().unique()):
    universite_selectionnee = clicked_univ
else:
    universite_selectionnee = "Toutes les universités"

if universite_selectionnee == "Toutes les universités":
    praticiens = df.sort_values(["Université", "Nom", "Prénom"])
    st.header("Tous les praticiens")

else:
    praticiens = df[df["Université"] == universite_selectionnee].sort_values(["Nom", "Prénom"])

    st.markdown(
        f"""
        <div class="selected-box">
            <h3 style="margin-top:0;">{universite_selectionnee}</h3>
            <p><b>{len(praticiens)}</b> praticien(s)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Répartition par corps")

    for corps, n in praticiens["Corps"].value_counts().items():
        st.write(f"• {corps} : {n}")

    st.subheader("Liste des praticiens")

    for _, row in praticiens.iterrows():
        st.write(practitioner_line(row, with_year=True))



for _, row in praticiens.iterrows():
    prenom = str(row["Prénom"]).strip()
    nom = str(row["Nom"]).strip()
    corps = str(row["Corps"]).strip()
    annee = row["Nomination_année"]

    photo = find_photo(prenom, nom)

    c1, c2 = st.columns([1, 4])

    with c1:
        if photo:
            st.image(str(photo), width=150)
        else:
            photo_placeholder()

    with c2:
        st.subheader(f"{prenom} {nom}")
        st.write(f"Corps : {corps}")

        if pd.notna(annee):
            st.write(f"Année de nomination : {int(annee)}")
        else:
            st.write("Année de nomination :")

        st.write(f"Université : {row['Université']}")

    st.divider()


st.markdown("---")
st.subheader("Répartition des nominations par corps")

chart_data = (
    df.dropna(subset=["Nomination_année"])
    .assign(Nomination_année=lambda x: x["Nomination_année"].astype(int))
    .groupby(["Nomination_année", "Corps"])
    .size()
    .reset_index(name="Nombre")
)

if chart_data.empty:
    st.info("Aucune année de nomination disponible.")
else:
    pivot = chart_data.pivot(
        index="Nomination_année",
        columns="Corps",
        values="Nombre",
    ).fillna(0)

    st.bar_chart(pivot)
