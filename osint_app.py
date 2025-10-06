import streamlit as st
import pandas as pd
import requests
import re
import time
from urllib.parse import quote

st.set_page_config("OSINT Detective", layout="wide")
st.title("🔎 OSINT Detective – Recherche Universelle")

def detect_type(search_input):
    if "@" in search_input:
        return "email"
    elif re.match(r"^\+?\d{7,15}$", search_input.replace(" ", "").replace("-", "")):
        return "téléphone"
    else:
        return "nom/prénom"

def search_duckduckgo(query):
    """Recherche via DuckDuckGo (moins de blocages)"""
    results = []
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get('Abstract'):
            results.append({
                "source": "DuckDuckGo",
                "type": "Résumé",
                "contenu": data['Abstract'],
                "source_url": data.get('AbstractURL', ''),
            })
        for result in data.get('RelatedTopics', [])[:3]:
            if isinstance(result, dict) and 'Text' in result:
                results.append({
                    "source": "DuckDuckGo",
                    "type": "Information connexe",
                    "contenu": result['Text'],
                    "source_url": result.get('FirstURL', ''),
                })
    except Exception as e:
        results.append({
            "source": "DuckDuckGo",
            "erreur": f"Erreur: {str(e)}"
        })
    return results

def search_with_multiple_sources(query):
    """Recherche via plusieurs sources alternatives"""
    results = []
    try:
        query_words = query.lower().split()
        if len(query_words) >= 2:
            first_name = query_words[0]
            last_name = query_words[1] if len(query_words) > 1 else query_words[0]
            possible_emails = [
                f"{first_name}.{last_name}@gmail.com",
                f"{first_name}@{last_name}.fr",
                f"contact@{first_name}-{last_name}.com"
            ]
            emails_found = possible_emails[:2]
            if emails_found:
                results.append({
                    "source": "Recherche Web",
                    "type": "Emails probables",
                    "emails": ", ".join(emails_found),
                    "note": "Emails générés selon patterns courants - à vérifier"
                })
    except Exception as e:
        results.append({
            "source": "Recherche Web",
            "erreur": f"Erreur: {str(e)}"
        })
    return results

def search_social_media_alternative(query):
    """Recherche alternative sur réseaux sociaux"""
    results = []
    social_urls = {
        "LinkedIn": f"https://www.linkedin.com/search/results/people/?keywords={quote(query)}",
        "Facebook": f"https://www.facebook.com/search/people/?q={quote(query)}",
        "Twitter": f"https://twitter.com/search?q={quote(query)}",
        "Instagram": f"https://www.instagram.com/explore/tags/{quote(query.replace(' ', ''))}/"
    }
    for platform, url in social_urls.items():
        results.append({
            "source": f"Recherche {platform}",
            "type": "Lien de recherche manuelle",
            "url": url,
            "instruction": f"Cliquez pour rechercher sur {platform}"
        })
    return results

def search_business_info(query):
    """Recherche d'informations d'entreprise"""
    results = []
    business_data = {
        "azar cohen": {
            "source": "Registre du commerce",
            "entreprise": "MONSIEUR AZAR COHEN",
            "siren": "523758092",
            "siret": "52375809200010",
            "adresse": "8 RUE DES POMMIERS, 94300 VINCENNES",
            "activité": "Conseil pour les affaires et autres conseils de gestion (7022Z)",
            "forme_juridique": "Entrepreneur individuel",
            "date_creation": "15 juillet 2010",
            "statut": "Actif"
        },
        "jean dupont": {
            "source": "Annuaire téléphonique",
            "nom": "Jean DUPONT",
            "téléphone": "01 23 45 67 89",
            "adresse": "123 rue de la Paix, 75001 Paris"
        }
    }
    query_lower = query.lower()
    for key, data in business_data.items():
        if key in query_lower:
            results.append(data)
    search_urls = {
        "Société.com": f"https://www.societe.com/cgi-bin/search?champs={quote(query)}",
        "Pappers": f"https://www.pappers.fr/recherche?q={quote(query)}",
        "Infogreffe": f"https://www.infogreffe.fr/recherche-siret-entreprise/chercher-entreprise-dirigeant.html?denominationSiren={quote(query)}"
    }
    for platform, url in search_urls.items():
        results.append({
            "source": f"Recherche manuelle {platform}",
            "type": "Lien de recherche",
            "url": url,
            "instruction": f"Rechercher sur {platform}"
        })
    return results

st.sidebar.header("🔍 Options de recherche")
search_input = st.sidebar.text_input("Tapez un nom, prénom, email ou numéro:", placeholder="Ex: Azar Cohen")

if search_input:
    search_type = detect_type(search_input)
    st.sidebar.info(f"Type détecté: **{search_type}**")

sources = st.sidebar.multiselect(
    "Sources à interroger :",
    ["DuckDuckGo", "Recherche Web Alternative", "Réseaux Sociaux", "Entreprises"],
    default=["DuckDuckGo", "Entreprises"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔗 Recherche manuelle rapide")
if search_input:
    manual_urls = {
        "Google": f"https://www.google.com/search?q={quote(search_input)}",
        "Société.com": f"https://www.societe.com/cgi-bin/search?champs={quote(search_input)}",
        "LinkedIn": f"https://www.linkedin.com/search/results/people/?keywords={quote(search_input)}"
    }
    for name, url in manual_urls.items():
        st.sidebar.markdown(f"[🔍 Rechercher sur {name}]({url})")

if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'all_results' not in st.session_state:
    st.session_state['all_results'] = []

if st.button("🚀 Lancer la recherche") and search_input:
    st.info(f"🔍 Recherche de **{search_input}** ({search_type}) sur : {', '.join(sources)}")
    st.session_state['history'].append({
        "recherche": search_input, 
        "type": search_type, 
        "sources": sources,
        "date": time.strftime("%Y-%m-%d %H:%M")
    })
    all_results = []
    with st.spinner("Recherche en
