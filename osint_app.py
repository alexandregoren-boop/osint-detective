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

def search_google(query):
    """Recherche Google avec extraction d'informations"""
    results = []
    try:
        # Google Search
        url = f"https://www.google.com/search?q={quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraction des résultats
        for result in soup.find_all('div', class_='g')[:5]:
            title_elem = result.find('h3')
            link_elem = result.find('a')
            snippet_elem = result.find('span', {'data-ved': True})
            
            if title_elem and link_elem:
                title = title_elem.get_text()
                link = link_elem.get('href', '')
                snippet = snippet_elem.get_text() if snippet_elem else ""
                
                # Extraction emails du snippet
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', snippet)
                phones = re.findall(r'\b(?:\+33|0)[1-9](?:[0-9]{8})\b', snippet)
                
                results.append({
                    "source": "Google",
                    "titre": title,
                    "lien": link,
                    "extrait": snippet[:200] + "..." if len(snippet) > 200 else snippet,
                    "emails_trouvés": ", ".join(emails) if emails else "Aucun",
                    "téléphones_trouvés": ", ".join(phones) if phones else "Aucun"
                })
    except Exception as e:
        results.append({"source": "Google", "erreur": f"Erreur: {str(e)}"})
    
    return results

def search_pages_jaunes(query):
    """Recherche Pages Jaunes"""
    results = []
    try:
        url = f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Recherche des résultats PJ
        for result in soup.find_all('div', class_='bi-denomination')[:3]:
            name = result.get_text().strip()
            parent = result.find_parent('div', class_='bi-bloc')
            
            phone = "Non trouvé"
            address = "Non trouvée"
            
            if parent:
                phone_elem = parent.find('span', class_='coord-numero')
                if phone_elem:
                    phone = phone_elem.get_text().strip()
                
                addr_elem = parent.find('div', class_='adresse')
                if addr_elem:
                    address = addr_elem.get_text().strip()
            
            results.append({
                "source": "Pages Jaunes",
                "nom": name,
                "téléphone": phone,
                "adresse": address
            })
            
    except Exception as e:
        results.append({"source": "Pages Jaunes", "erreur": f"Erreur: {str(e)}"})
    
    return results

def search_linkedin_google(query):
    """Recherche profils LinkedIn via Google"""
    results = []
    try:
        search_query = f"site:linkedin.com/in {query}"
        url = f"https://www.google.com/search?q={quote(search_query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for result in soup.find_all('div', class_='g')[:3]:
            title_elem = result.find('h3')
            link_elem = result.find('a')
            
            if title_elem and link_elem and 'linkedin.com' in link_elem.get('href', ''):
                results.append({
                    "source": "LinkedIn",
                    "profil": title_elem.get_text(),
                    "lien": link_elem.get('href', '')
                })
                
    except Exception as e:
        results.append({"source": "LinkedIn", "erreur": f"Erreur: {str(e)}"})
    
    return results

def search_societe_com(query):
    """Recherche sur société.com"""
    results = []
    try:
        url = f"https://www.societe.com/cgi-bin/search?champs={quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraction des résultats entreprise
        for result in soup.find_all('div', class_='result')[:3]:
            company_name = result.find('h2')
            if company_name:
                results.append({
                    "source": "Société.com",
                    "entreprise": company_name.get_text().strip(),
                    "lien": "https://www.societe.com" + result.find('a').get('href', '')
                })
                
    except Exception as e:
        results.append({"source": "Société.com", "erreur": f"Erreur: {str(e)}"})
    
    return results

# Interface utilisateur
st.sidebar.header("🔍 Options de recherche")
search_input = st.sidebar.text_input("Tapez un nom, prénom, email ou numéro:", placeholder="Ex: Jean Dupont")

if search_input:
    search_type = detect_type(search_input)
    st.sidebar.info(f"Type détecté: **{search_type}**")

sources = st.sidebar.multiselect(
    "Sources à interroger :",
    ["Google", "Pages Jaunes", "LinkedIn", "Société.com"],
    default=["Google", "Pages Jaunes"]
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
    
    with st.spinner("Recherche en cours..."):
        if "Google" in sources:
            st.write("🔍 Recherche Google...")
            google_results = search_google(search_input)
            all_results.extend(google_results)
            
        if "Pages Jaunes" in sources:
            st.write("📞 Recherche Pages Jaunes...")
            pj_results = search_pages_jaunes(search_input)
            all_results.extend(pj_results)
            
        if "LinkedIn" in sources:
            st.write("💼 Recherche LinkedIn...")
            linkedin_results = search_linkedin_google(search_input)
            all_results.extend(linkedin_results)
            
        if "Société.com" in sources:
            st.write("🏢 Recherche Société.com...")
            societe_results = search_societe_com(search_input)
            all_results.extend(societe_results)
    
    st.session_state['all_results'] = all_results
    
    # Affichage des résultats
    if all_results:
        st.success(f"✅ {len(all_results)} résultats trouvés!")
        
        # Grouper par source
        for source in sources:
            source_results = [r for r in all_results if r.get('source') == source]
            if source_results:
                st.subheader(f"📋 Résultats {source}")
                df = pd.DataFrame(source_results)
                st.dataframe(df, use_container_width=True)
    else:
        st.warning("Aucun résultat trouvé.")

# Export
if st.session_state.get('all_results'):
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Exporter en Excel"):
            df = pd.DataFrame(st.session_state['all_results'])
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Télécharger Excel",
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
🎯 **Cette version recherche de vraies informations :**
- Google : extrait les emails et téléphones des résultats
- Pages Jaunes : récupère noms, téléphones et adresses  
- LinkedIn : trouve les profils professionnels
- Société.com : trouve les entreprises liées

💡 **Prochaines améliorations :** Facebook, Instagram, bases décès, Google Dorking avancé...
""")
