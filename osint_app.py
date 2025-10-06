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
        
        # Si pas de résultats directs, faire une recherche web classique
        if not results:
            # Recherche web alternative
            web_url = f"https://duckduckgo.com/html/?q={quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            try:
                response = requests.get(web_url, headers=headers, timeout=10)
                # Extraction basique des emails et téléphones du contenu
                content = response.text
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
                phones = re.findall(r'(?:\+33|0)[1-9](?:[.\s-]?\d{2}){4}', content)
                
                if emails or phones:
                    results.append({
                        "source": "DuckDuckGo Web",
                        "type": "Contacts extraits",
                        "emails": ", ".join(set(emails)[:3]) if emails else "Aucun",
                        "téléphones": ", ".join(set(phones)[:3]) if phones else "Aucun"
                    })
            except:
                pass
        
    except Exception as e:
        results.append({"source": "DuckDuckGo", "erreur": f"Erreur: {str(e)}"})
    
    return results

def search_with_multiple_sources(query):
    """Recherche via plusieurs sources alternatives"""
    results = []
    
    # 1. Recherche via Bing (API moins restrictive)
    try:
        bing_url = f"https://www.bing.com/search?q={quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        response = requests.get(bing_url, headers=headers, timeout=10)
        content = response.text
        
        # Extraction d'informations
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        phones = re.findall(r'(?:\+33|0)[1-9](?:[.\s-]?\d{2}){4}', content)
        
        if emails or phones:
            results.append({
                "source": "Bing Search",
                "type": "Recherche web",
                "emails": ", ".join(set(emails)[:3]) if emails else "Aucun",
                "téléphones": ", ".join(set(phones)[:3]) if phones else "Aucun"
            })
    except:
        pass
    
    # 2. Recherche dans des bases de données publiques
    try:
        # Simulation d'une recherche dans une base locale (à remplacer par vraies données)
        fake_db = {
            "azar cohen": {
                "entreprise": "MONSIEUR AZAR COHEN",
                "siren": "523758092",
                "adresse": "8 RUE DES POMMIERS, 94300 VINCENNES",
                "activité": "Conseil pour les affaires et autres conseils de gestion"
            },
            "jean dupont": {
                "téléphone": "01 23 45 67 89",
                "adresse": "123 rue de la Paix, 75001 Paris"
            }
        }
        
        query_lower = query.lower()
        for name, info in fake_db.items():
            if name in query_lower or any(word in query_lower for word in name.split()):
                results.append({
                    "source": "Base de données locale",
                    "type": "
