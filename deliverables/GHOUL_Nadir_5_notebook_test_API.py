import streamlit as st
import requests
import pandas as pd
from os import environ
from pathlib import Path

import matplotlib.pyplot as plt
from requests import get, Response
from hashlib import sha256
from tqdm.notebook import tqdm
from zipfile import ZipFile
from IPython.display import display, Markdown

# Added imports for the new transformer

from utils.image_inverter import save

environ['CUDA_VISIBLE_DEVICES'] = '-1'
# --- Configuration ---
API_URL = "https://p7-ijkx.onrender.com/predict"

_cache_folder = Path('~/.cache/gn_p7').expanduser()
_cache_folder.mkdir(parents=True, exist_ok=True)

_ds_url = 'https://s3-eu-west-1.amazonaws.com/static.oc-static.com/prod/courses/files/Parcours_data_scientist/Projet+-+Impl%C3%A9menter+un+mod%C3%A8le+de+scoring/Projet+Mise+en+prod+-+home-credit-default-risk.zip'

graph_folder: Path = Path("./graphs")
random_state: int = 42


def save_figure(figure: plt.Figure, folder: str, figure_name: str) -> None:
    folder = graph_folder / folder
    folder.mkdir(parents=True, exist_ok=True)
    save(figure, folder / f'{figure_name}.png', close=True)


def download(url: str) -> Path:
    url_id: str = sha256(url.encode('utf-8')).hexdigest()
    local_path: Path = _cache_folder / url_id
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if not local_path.exists():
        tmp_path: Path = _cache_folder / (url_id + '.tmp')
        res: Response = get(url, stream=True)
        with tmp_path.open('wb') as f, tqdm(
                total=int(res.headers.get('content-length')),
                desc=f'Downloading {url}',
                unit_scale=True) as q:
            for chunk in res.iter_content(chunk_size=8192):
                q.update(len(chunk))
                f.write(chunk)
        tmp_path.replace(local_path)
    return local_path


def download_zip_archive(url: str) -> Path:
    """Download a zip archive, extract it then return the folder containing its content"""
    archive_path: Path = download(url)
    archive_folder: Path = Path(archive_path.as_posix() + '.dir')

    if not archive_folder.exists():
        print(f'Extracting archive {url}...', flush=True)
        archive_temp: Path = Path(archive_path.as_posix() + '.tmp')
        archive_temp.mkdir(parents=True, exist_ok=True)
        archive: ZipFile = ZipFile(archive_path)
        archive.extractall(path=archive_temp)
        archive_temp.replace(archive_folder)
        print(f'Extracting archive {url}...done', flush=True)

    return archive_folder


datasets: dict[str, pd.DataFrame] = {}


def get_dataset(name: str) -> pd.DataFrame:
    folder = download_zip_archive(_ds_url)
    if not name.endswith('.csv'):
        name = f'{name}.csv'
    try:
        return datasets[name]
    except KeyError:
        try:
            _df = pd.read_csv(folder / name)
        except FileNotFoundError:
            display(Markdown(f'# ERROR: Dataset {name!r} not found, available datasets are:\n' + '\n'.join(
                f'- {p.name}' for p in sorted(folder.iterdir(), key=(lambda x: x.name.lower())))))
            raise KeyError(name) from None
        else:
            datasets[name] = _df
            return _df.copy()


# --- Fonctions pour charger les données ---
@st.cache_data
def load_test_data(name):
    """
    Charge les données de test à partir d'un fichier CSV.
    """
    try:
        df = get_dataset(name)
        if 'SK_ID_CURR' not in df.columns:
            st.error(f"Erreur: La colonne 'SK_ID_CURR' est introuvable dans le fichier {data_path}.")
            return pd.DataFrame()
        return df
    except FileNotFoundError:
        st.error(f"ERREUR CRITIQUE : Le fichier de données '{data_path}' est introuvable.")
        st.info("Veuillez vous assurer que le fichier `application_test.csv` se trouve dans le même dossier que ce script Streamlit.")
        return pd.DataFrame()

# --- Interface Streamlit ---
st.set_page_config(layout="wide")
st.title("Tableau de Bord - Scoring Crédit")
st.markdown("Cette interface permet d'interroger l'API de scoring pour prédire la probabilité de défaut de paiement d'un client.")

# --- Chargement et validation des données ---
test_df = load_test_data('application_test')

if test_df.empty:
    st.stop()

client_ids = test_df['SK_ID_CURR'].tolist()

# --- Panneau de contrôle utilisateur ---
st.sidebar.header("Sélection du client")
selected_id = st.sidebar.selectbox("Choisissez un ID client pour obtenir une prédiction :", client_ids)

if st.sidebar.button("Obtenir la prédiction"):
    if selected_id:
        st.header(f"Analyse pour le client ID : {selected_id}")

        client_data = test_df[test_df['SK_ID_CURR'] == selected_id]
        
        # --- !! SECTION MASSIVEMENT SIMPLIFIÉE !! ---
        # No more complex cleaning. The API handles it now.
        # We just convert the row to a dictionary and replace Pandas' NaN
        # with None, which is JSON's 'null'. That's it.
        payload = client_data.iloc[0].to_dict()
        payload_cleaned = {k: (None if pd.isna(v) else v) for k, v in payload.items()}
        # --- !! FIN DE LA SECTION SIMPLIFIÉE !! ---

        with st.expander("Voir les données brutes envoyées à l'API (maintenant bien plus simple)"):
            st.json(payload_cleaned)

        with st.spinner("Prédiction en cours..."):
            try:
                response = requests.post(API_URL, json=payload_cleaned)
                response.raise_for_status()

                result = response.json()
                st.subheader("Résultat de la prédiction")

                proba = result['probability_default']
                decision = result['decision']
                threshold = result['threshold']

                if decision == "yes":
                    st.success(f"✅ Crédit Accordé (Décision : {decision.upper()})")
                else:
                    st.error(f"❌ Crédit Refusé (Décision : {decision.upper()})")

                col1, col2 = st.columns(2)
                col1.metric(label="Probabilité de défaut du client", value=f"{proba:.2%}")
                col2.metric(label="Seuil de décision métier", value=f"{threshold:.2%}")

                st.progress(proba)
                st.markdown(f"La probabilité de défaut de ce client est estimée à **{proba:.2%}**. Le crédit est **{'accordé' if decision == 'yes' else 'refusé'}** car cette probabilité est {'inférieure' if decision == 'yes' else 'supérieure ou égale'} au seuil de décision de **{threshold:.2%}**.")

            except requests.exceptions.HTTPError as e:
                st.error(f"Erreur HTTP lors de l'appel à l'API : {e}")
                st.error(f"Détail de l'API : {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de connexion à l'API : {e}")
                st.info("Vérifiez que l'API est bien déployée et accessible à l'adresse : " + API_URL)
            except Exception as e:
                st.error(f"Une erreur inattendue est survenue : {e}")
else:
    st.info("Veuillez sélectionner un ID client et cliquer sur 'Obtenir la prédiction' pour commencer.")

# streamlit run xxx.py