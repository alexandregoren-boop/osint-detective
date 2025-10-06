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
    try:
        # Recherche sur société.com via Google
        search_query = f'site:societe.com "{query}"'
        url = f"https://www.google.com/search?q={quote(search_query)}"
        response = requests.get(url, headers=get_headers())
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for result in soup.find_all('div', class_='g')[:5]:
            title_elem = result.find('h3')
            link_elem = result.find('a')
            snippet_elem = result.find('span', {'data-ved': True})
            
            if title_elem and link_elem and 'societe.com' in link_elem.get('href', ''):
                title = title_elem.get_text()
                link = link_elem.get('href', '')
                snippet = snippet_elem.get_text() if snippet_elem else ""
                
                # Extraction d'informations spécifiques
                siren = re.findall(r'\b\d{9}\b', snippet + title)
                adresses = re.findall(r'\d+[^,]*,\s*\d{5}\s*[A-Z][A-Z\s]+', snippet + title)
                
                results.append({
                    "source": "Société.com",
                    "entreprise": title,
                    "lien": link,
                    "siren": ", ".join(siren) if siren else "Non trouvé",
                    "adresse": ", ".join(adresses) if adresses else "Non trouvée",
                    "extrait": snippet[:200] + "..." if len(snippet) > 200 else snippet
                })
                
    except Exception as e:
        results.append({"source": "Société.com", "erreur": f"Erreur: {str(e)}"})
    
    return results

def search_pages_blanches_advanced(query):
    """Recherche Pages Blanches via Google"""
    results = []
    try:
        search_query = f'site:pagesblanches.fr OR site:pagesjaunes.fr "{query}"'
        url = f"https://www.google.com/search?q={quote(search_query)}"
        response = requests.get(url, headers=get_headers())
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for result in soup.find_all('div', class_='g')[:3]:
            title_elem = result.find('h3')
            link_elem = result.find('a')
            snippet_elem = result.find('span', {'data-ved': True})
            
            if title_elem and link_elem:
                title = title_elem.get_text()
                link = link_elem.get('href', '')
                snippet = snippet_elem.get_text() if snippet_elem else ""
                
                # Extraction téléphone et adresse
                phones = re.findall(r'(?:\+33|0)[1-9](?:[.\s-]?\d{2}){4}', snippet + title)
                adresses = re.findall(r'\d+[^,]*,\s*\d{5}\s*[A-Z][A-Z\s]+', snippet + title)
                
                results.append({
                    "source": "Pages Blanches/Jaunes",
                    "nom": title,
                    "téléphone": ", ".join(set(phones)) if phones else "Non trouvé",
                    "adresse": ", ".join(set(adresses)) if adresses else "Non trouvée",
                    "lien": link
                })
                
    except Exception as e:
        results.append({"source": "Pages Blanches", "erreur": f"Erreur: {str(e)}"})
    
    return results

def search_social_networks(query):
    """Recherche sur réseaux sociaux via Google"""
    results = []
    try:
        social_sites = [
            "site:linkedin.com/in",
            "site:facebook.com",
            "site:twitter.com OR site:x.com",
            "site:instagram.com"
        ]
        
        for site in social_sites[:2]:  # Limite pour éviter blocages
            search_query = f'{site} "{query}"'
            url = f"https://www.google.com/search?q={quote(search_query)}"
            response = requests.get(url, headers=get_headers())
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for result in soup.find_all('div', class_='g')[:2]:
                title_elem = result.find('h3')
                link_elem = result.find('a')
                
                if title_elem and link_elem:
                    platform = "LinkedIn" if "linkedin" in link_elem.get('href', '') else \
                              "Facebook" if "facebook" in link_elem.get('href', '') else \
                              "Twitter/X" if ("twitter" in link_elem.get('href', '') or "x.com" in link_elem.get('href', '')) else \
                              "Instagram" if "instagram" in link_elem.get('href', '') else "Autre"
                    
                    results.append({
                        "source": f"Réseaux sociaux ({platform})",
                        "profil": title_elem.get_text(),
                        "lien": link_elem.get('href', ''),
                        "plateforme": platform
                    })
            
            time.sleep(0.5)
            
    except Exception as e:
        results.append({"source": "Réseaux sociaux", "erreur": f"Erreur: {str(e)}"})
    
    return results

# Interface utilisateur
st.sidebar.header("🔍 Options de recherche")
search_input = st.sidebar.text_input("Tapez un nom, prénom, email ou numéro:", placeholder="Ex: Azar Cohen")

if search_input:
    search_type = detect_type(search_input)
    st.sidebar.info(f"Type détecté: **{search_type}**")

sources = st.sidebar.multiselect(
    "Sources à interroger :",
    ["Google Avancé", "Société.com", "Pages Blanches/Jaunes", "Réseaux Sociaux"],
    default=["Google Avancé", "Société.com"]
)

# Historique
if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'all_results' not in st.session_state:
    st.session_state['all_results'] = []

# Lancement recherche
if st.button("🚀 Lancer la recherche") and search_input:
    st.info(f"🔍 Recherche de **{search_input}** ({search_type}) sur : {', '.join(sources)}")
    
    # Ajout à l'historique
    st.session_state['history'].append({
        "recherche": search_input, 
        "type": search_type, 
        "sources": sources,
        "date": time.strftime("%Y-%m-%d %H:%M")
    })
    
    all_results = []
    
    with st.spinner("Recherche en cours... Cela peut prendre quelques secondes."):
        if "Google Avancé" in sources:
            st.write("🔍 Recherche Google avec dorking...")
            google_results = search_google_advanced(search_input)
            all_results.extend(google_results)
            
        if "Société.com" in sources:
            st.write("🏢 Recherche Société.com...")
            societe_results = search_societe_com_advanced(search_input)
            all_results.extend(societe_results)
            
        if "Pages Blanches/Jaunes" in sources:
            st.write("📞 Recherche Pages Blanches/Jaunes...")
            pages_results = search_pages_blanches_advanced(search_input)
            all_results.extend(pages_results)
            
        if "Réseaux Sociaux" in sources:
            st.write("📱 Recherche Réseaux Sociaux...")
            social_results = search_social_networks(search_input)
            all_results.extend(social_results)
    
    st.session_state['all_results'] = all_results
    
    # Affichage des résultats
    if all_results:
        st.success(f"✅ {len(all_results)} résultats trouvés!")
        
        # Résumé des informations trouvées
        all_emails = []
        all_phones = []
        all_addresses = []
        
        for result in all_results:
            if 'emails' in result and result['emails'] != "Aucun":
                all_emails.extend(result['emails'].split(', '))
            if 'téléphones' in result and result['téléphones'] != "Aucun":
                all_phones.extend(result['téléphones'].split(', '))
            if 'téléphone' in result and result['téléphone'] != "Non trouvé":
                all_phones.append(result['téléphone'])
            if 'adresse' in result and result['adresse'] != "Non trouvée":
                all_addresses.append(result['adresse'])
        
        # Affichage du résumé
        if any([all_emails, all_phones, all_addresses]):
            st.subheader("📋 Résumé des informations trouvées")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if all_emails:
                    st.write("📧 **Emails:**")
                    for email in set(all_emails):
                        st.write(f"• {email}")
            
            with col2:
                if all_phones:
                    st.write("📞 **Téléphones:**")
                    for phone in set(all_phones):
                        st.write(f"• {phone}")
            
            with col3:
                if all_addresses:
                    st.write("📍 **Adresses:**")
                    for address in set(all_addresses):
                        st.write(f"• {address}")
        
        # Affichage détaillé par source
        st.subheader("🔍 Résultats détaillés")
        df = pd.DataFrame(all_results)
        st.dataframe(df, use_container_width=True)
        
    else:
        st.warning("Aucun résultat trouvé.")

# Export et historique
if st.session_state.get('all_results'):
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Exporter en Excel"):
            df = pd.DataFrame(st.session_state['all_results'])
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Télécharger CSV",
                data=csv,
                file_name=f"recherche_{search_input.replace(' ', '_')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📋 Voir l'historique"):
            if st.session_state['history']:
                st.dataframe(pd.DataFrame(st.session_state['history']))
            else:
                st.info("Aucune recherche dans l'historique")

st.markdown("---")
st.info("""
🎯 **Version améliorée avec recherches plus robustes :**
- Google Dorking avancé pour trouver plus d'informations
- Recherche via Google sur société.com, pages blanches, réseaux sociaux
- Extraction automatique d'emails, téléphones, adresses, SIREN
- Résumé des informations de contact trouvées
- Recherche sur LinkedIn, Facebook, Twitter/X, Instagram

💡 **Testez avec "Azar Cohen" pour voir les résultats !**
""")
