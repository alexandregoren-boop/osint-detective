import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
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

def get_headers():
    """Headers pour éviter les blocages"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

def search_google_advanced(query):
    """Recherche Google avec Google Dorking"""
    results = []
    try:
        # Recherche normale
        searches = [
            f'"{query}"',  # Recherche exacte
            f'{query} email',  # Recherche avec email
            f'{query} téléphone OR phone',  # Recherche avec téléphone
            f'{query} site:linkedin.com',  # LinkedIn
            f'{query} site:facebook.com',  # Facebook
            f'{query} site:pagesjaunes.fr OR site:pagesblanches.fr',  # Annuaires
        ]
        
        for search_query in searches[:3]:  # Limite pour éviter les blocages
            url = f"https://www.google.com/search?q={quote(search_query)}&num=10"
            response = requests.get(url, headers=get_headers())
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraction améliorée
            for result in soup.find_all('div', class_='g')[:3]:
                title_elem = result.find('h3')
                link_elem = result.find('a')
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    link = link_elem.get('href', '')
                    
                    # Recherche du snippet
                    snippet = ""
                    snippet_elems = result.find_all('span')
                    for elem in snippet_elems:
                        text = elem.get_text()
                        if len(text) > 50:  # Prendre le texte le plus long
                            snippet = text
                            break
                    
                    # Extraction d'informations du snippet
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', snippet + title)
                    phones = re.findall(r'(?:\+33|0)[1-9](?:[.\s-]?\d{2}){4}', snippet + title)
                    
                    results.append({
                        "source": f"Google ({search_query})",
                        "titre": title,
                        "lien": link,
                        "extrait": snippet[:300] + "..." if len(snippet) > 300 else snippet,
                        "emails": ", ".join(set(emails)) if emails else "Aucun",
                        "téléphones": ", ".join(set(phones)) if phones else "Aucun"
                    })
            
            time.sleep(1)  # Pause pour éviter les blocages
            
    except Exception as e:
        results.append({"source": "Google", "erreur": f"Erreur: {str(e)}"})
    
    return results

def search_societe_com_advanced(query):
    """Recherche société.com via Google (plus efficace)"""
    results = []
