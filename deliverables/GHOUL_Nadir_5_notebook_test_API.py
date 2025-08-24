import streamlit as st
import requests
import pandas as pd
from pathlib import Path

# URL de ton API déployée sur Render
API_URL = "https://p7-ijkx.onrender.com/predict" 

# --- Fonctions pour charger les données (similaire à ton notebook) ---
@st.cache_data
def load_test_data():
    archive_folder = Path('~/.cache/gn_p7/1ea8215587f859b1f7d54483ca794f576307374092b715694c65a251b3a3250e.dir')
    df = pd.read_csv(archive_folder / 'application_test.csv')
    return df

st.title("Interface de Test - Scoring Crédit")

# --- Chargement des données ---
test_df = load_test_data()
client_ids = test_df['SK_ID_CURR'].tolist()

# --- Interface utilisateur ---
st.header("Sélection du client")
selected_id = st.selectbox("Choisissez un ID client pour obtenir une prédiction :", client_ids)

if st.button("Obtenir la prédiction"):
    if selected_id:
        # Récupérer les données du client
        client_data = test_df[test_df['SK_ID_CURR'] == selected_id]

        # Convertir en dictionnaire et gérer les NaN pour JSON
        payload = client_data.iloc[0].to_dict()
        payload_cleaned = {k: (None if pd.isna(v) else v) for k, v in payload.items()}

        st.write("Données envoyées à l'API :")
        st.json(payload_cleaned, expanded=False)

        try:
            # Appel à l'API
            response = requests.post(API_URL, json=payload_cleaned)
            response.raise_for_status()  # Lève une exception pour les erreurs HTTP

            # Affichage des résultats
            result = response.json()
            st.header("Résultat de la prédiction")

            proba = result['probability_default']
            decision = result['decision']
            threshold = result['threshold']

            if decision == "yes":
                st.success(f"Crédit Accordé (décision: {decision.upper()})")
            else:
                st.error(f"Crédit Refusé (décision: {decision.upper()})")

            st.metric(label="Probabilité de défaut", value=f"{proba:.2%}")
            st.write(f"Le seuil de décision métier est à {threshold:.2%}.")

        except requests.exceptions.RequestException as e:
            st.error(f"Erreur lors de l'appel à l'API : {e}")
        except Exception as e:
            st.error(f"Une erreur inattendue est survenue : {e}")

if __name__ == '__main__':
    pass