import streamlit as st
import pandas as pd
import requests
import re
import time
import json
from urllib.parse import quote, urljoin

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
        # DuckDuckGo instant answer API
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Résultat principal
        if data.get('Abstract'):
            results.append({
                "source": "DuckDuckGo",
                "type": "Résumé",
                "contenu": data['Abstract'],
                "source_url": data.get('AbstractURL', ''),
            })
        
        # Résultats connexes
        for result in data.get('RelatedTopics', [])[:3]:
            if isinstance(result, dict) and 'Text' in result:
                results.append({
                    "source": "DuckDuckGo",
                    "type": "Information connexe",
                    "contenu": result['Text'],
                    "source_url": result.get('FirstURL', ''),
                })
        
    except Exception as e:
        results.append({"source": "D
