import streamlit as st
import pandas as pd

st.set_page_config("OSINT Detective", layout="wide")
st.title("🔎 OSINT Detective – Recherche Universelle")

# Sidebar
st.sidebar.header("Options de recherche")
search_input = st.sidebar.text_input("Tapez un nom, email ou numéro")
search_type = "Inconnu"
if search_input:
    if "@" in search_input:
        search_type = "email"
    elif search_input.replace("+", "").replace(" ", "").isdigit():
        search_type = "numéro"
    else:
        search_type = "nom/prénom"

sources = st.sidebar.multiselect(
    "Sources à interroger :",
    ["Google", "Pages Jaunes", "LinkedIn", "Facebook", "X (Twitter)", "Pappers", "Societe.com", "Infogreffe", "Décès (avis)", "Google Dorking"],
    default=["Google", "Pages Jaunes"]
)

uploaded_file = st.sidebar.file_uploader("Importer des contacts Excel", type=["xlsx", "csv"])

# Historique simplifié (à remplacer par Storage vrai plus tard)
if 'history' not in st.session_state:
    st.session_state['history'] = []
if st.sidebar.button("Voir l'historique recherches"):
    st.write(pd.DataFrame(st.session_state['history']))

# Lancement recherche
if st.button("Lancer la recherche") and search_input:
    st.info(f"Recherche {search_type} sur : {', '.join(sources)}")
    # Ajout à l'historique
    st.session_state['history'].append({"input": search_input, "type": search_type, "sources": sources})
    # ---- ZONE À REMPLIR ----
    # Ici : pour chaque source, lancer sa recherche dédiée (Google, PJ etc.) et afficher les résultats
    # Exemple factice :
    results = []
    if "Google" in sources:
        results.append({"source": "Google", "trouvé": f"Page {search_input} sur Google (simulé)"})
    if "Pages Jaunes" in sources:
        results.append({"source": "Pages Jaunes", "trouvé": f"Entrée {search_input} sur Pages Jaunes (simulé)"})
    st.dataframe(pd.DataFrame(results))


# Export Excel
if st.button("Exporter les derniers résultats en Excel"):
    if 'results' in locals():
        df = pd.DataFrame(results)
        df.to_excel("résultats_osint.xlsx")
        st.success("Fichier Excel généré : résultats_osint.xlsx (à récupérer dans la version déployée)")
    else:
        st.warning("Lancez une recherche d'abord !")

st.markdown("---")

st.info("""
👆 Ce prototype est prêt à accueillir TOUTES les sources OSINT :
il suffit d'implémenter un module pour chaque API/scraper, et chaque résultat viendra remplir le tableau ci-dessus.
L'import Excel déclenchera la recherche par lot, l'export Excel ou PDF affichera un lien pour téléchargement.
L'historique sera stocké en base dès la version hébergée.
""")
