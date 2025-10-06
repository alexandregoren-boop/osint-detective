import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import quote, urljoin
import random
from fake_useragent import UserAgent
import json

st.set_page_config("OSINT Detective", layout="wide")
st.title("🔎 OSINT Detective – Recherche Automatisée")

# Configuration pour éviter les blocages
def get_session():
    session = requests.Session()
    ua = UserAgent()
    session.headers.update({
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def detect_type(search_input):
    if "@" in search_input:
        return "email"
    elif re.match(r"^\+?\d{7,15}$", search_input.replace(" ", "").replace("-", "")):
        return "téléphone"
    else:
        return "nom/prénom"

def scrape_google_search(query, session):
    """Scraping Google avec rotation User-Agent"""
    results = []
    try:
        search_url = f"https://www.google.com/search?q={quote(query)}&num=10"
        response = session.get(search_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for i, result in enumerate(soup.find_all('div', class_='g')[:5]):
            try:
                title_elem = result.find('h3')
                link_elem = result.find('a')
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    link = link_elem.get('href', '')
                    
                    # Extraction du snippet
                    snippet = ""
                    for span in result.find_all('span'):
                        text = span.get_text()
                        if len(text) > 50:
                            snippet = text
                            break
                    
                    # Extraction d'informations
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', snippet + title)
                    phones = re.findall(r'(?:\+33|0)[1-9](?:[.\s-]?\d{2}){4}', snippet + title)
                    
                    results.append({
                        "source": "Google",
                        "titre": title,
                        "lien": link,
                        "extrait": snippet[:200],
                        "emails": ", ".join(set(emails)) if emails else "Aucun",
                        "téléphones": ", ".join(set(phones)) if phones else "Aucun"
                    })
                    
            except Exception as e:
                continue
                
        time.sleep(random.uniform(1, 3))  # Pause aléatoire
        
    except Exception as e:
        results.append({"source": "Google", "erreur": f"Erreur: {str(e)}"})
    
    return results

def scrape_societe_com(query, session):
    """Scraping direct de société.com"""
    results = []
    try:
        # URL de recherche société.com
        search_url = f"https://www.societe.com/cgi-bin/search?champs={quote(query)}"
        response = session.get(search_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Recherche des résultats d'entreprises
        for result in soup.find_all('div', class_='result')[:5]:
            try:
                # Nom de l'entreprise
                name_elem = result.find('h2') or result.find('a', class_='denomination')
                if name_elem:
                    company_name = name_elem.get_text().strip()
                    
                    # Lien vers la fiche
                    link_elem = result.find('a')
                    company_link = ""
                    if link_elem and link_elem.get('href'):
                        company_link = urljoin("https://www.societe.com", link_elem.get('href'))
                    
                    # Informations supplémentaires
                    info_text = result.get_text()
                    siren = re.findall(r'\b\d{9}\b', info_text)
                    siret = re.findall(r'\b\d{14}\b', info_text)
                    
                    results.append({
                        "source": "Société.com",
                        "entreprise": company_name,
                        "lien": company_link,
                        "siren": siren[0] if siren else "Non trouvé",
                        "siret": siret[0] if siret else "Non trouvé",
                        "info_brute": info_text[:300]
                    })
                    
            except Exception as e:
                continue
        
        # Si pas de résultats directs, essayer une autre approche
        if not results:
            # Recherche alternative dans le contenu
            page_text = soup.get_text()
            if query.lower() in page_text.lower():
                siren_matches = re.findall(r'\b\d{9}\b', page_text)
                if siren_matches:
                    results.append({
                        "source": "Société.com",
                        "note": f"Mentions trouvées pour {query}",
                        "siren_possibles": ", ".join(siren_matches[:3])
                    })
        
        time.sleep(random.uniform(1, 2))
        
    except Exception as e:
        results.append({"source": "Société.com", "erreur": f"Erreur: {str(e)}"})
    
    return results

def scrape_pappers(query, session):
    """Scraping Pappers"""
    results = []
    try:
        search_url = f"https://www.pappers.fr/recherche?q={quote(query)}"
        response = session.get(search_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Recherche des cartes d'entreprises
        for card in soup.find_all('div', class_='entreprise-card')[:3]:
            try:
                name_elem = card.find('h3') or card.find('h2')
                if name_elem:
                    company_name = name_elem.get_text().strip()
                    
                    # Extraction d'informations
                    card_text = card.get_text()
                    siren = re.findall(r'\b\d{9}\b', card_text)
                    
                    # Recherche adresse
                    address_pattern = r'\d+[^,]*,\s*\d{5}\s*[A-Z][A-Z\s]+'
                    addresses = re.findall(address_pattern, card_text)
                    
                    results.append({
                        "source": "Pappers",
                        "entreprise": company_name,
                        "siren": siren[0] if siren else "Non trouvé",
                        "adresse": addresses[0] if addresses else "Non trouvée",
                        "info_brute": card_text[:200]
                    })
                    
            except Exception as e:
                continue
        
        time.sleep(random.uniform(1, 2))
        
    except Exception as e:
        results.append({"source": "Pappers", "erreur": f"Erreur: {str(e)}"})
    
    return results

def scrape_pages_jaunes(query, session):
    """Scraping Pages Jaunes"""
    results = []
    try:
        search_url = f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={quote(query)}"
        response = session.get(search_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Recherche des résultats
        for result in soup.find_all('article', class_='bi-bloc')[:5]:
            try:
                # Nom
                name_elem = result.find('h3') or result.find('a', class_='denomination')
                if name_elem:
                    name = name_elem.get_text().strip()
                    
                    # Téléphone
                    phone_elem = result.find('span', class_='coord-numero')
                    phone = phone_elem.get_text().strip() if phone_elem else "Non trouvé"
                    
                    # Adresse
                    addr_elem = result.find('div', class_='adresse')
                    address = addr_elem.get_text().strip() if addr_elem else "Non trouvée"
                    
                    results.append({
                        "source": "Pages Jaunes",
                        "nom": name,
                        "téléphone": phone,
                        "adresse": address
                    })
                    
            except Exception as e:
                continue
        
        time.sleep(random.uniform(1, 2))
        
    except Exception as e:
        results.append({"source": "Pages Jaunes", "erreur": f"Erreur: {str(e)}"})
    
    return results

def scrape_infogreffe(query, session):
    """Scraping Infogreffe"""
    results = []
    try:
        search_url = f"https://www.infogreffe.fr/recherche-siret-entreprise/chercher-entreprise-dirigeant.html?denominationSiren={quote(query)}"
        response = session.get(search_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Recherche des résultats
        for result in soup.find_all('div', class_='result-item')[:3]:
            try:
                name_elem = result.find('h4') or result.find('strong')
                if name_elem:
                    company_name = name_elem.get_text().strip()
                    
                    result_text = result.get_text()
                    siren = re.findall(r'\b\d{9}\b', result_text)
                    
                    results.append({
                        "source": "Infogreffe",
                        "entreprise": company_name,
                        "siren": siren[0] if siren else "Non trouvé",
                        "info": result_text[:200]
                    })
                    
            except Exception as e:
                continue
        
        time.sleep(random.uniform(1, 2))
        
    except Exception as e:
        results.append({"source": "Infogreffe", "erreur": f"Erreur: {str(e)}"})
    
    return results

# Interface utilisateur
st.sidebar.header("🔍 Recherche Automatisée OSINT")
search_input = st.sidebar.text_input("Nom, prénom, entreprise ou numéro:", placeholder="Ex: Azar Cohen")

if search_input:
    search_type = detect_type(search_input)
    st.sidebar.info(f"Type détecté: **{search_type}**")

sources = st.sidebar.multiselect(
    "Sources à scraper automatiquement :",
    ["Google", "Société.com", "Pappers", "Pages Jaunes", "Infogreffe"],
    default=["Google", "Société.com", "Pappers"]
)

# Historique
if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'all_results' not in st.session_state:
    st.session_state['all_results'] = []

# Lancement recherche automatisée
if st.button("🚀 Lancer le scraping automatisé") and search_input:
    st.info(f"🔍 Scraping automatisé de **{search_input}** sur : {', '.join(sources)}")
    
    # Session avec rotation User-Agent
    session = get_session()
    
    st.session_state['history'].append({
        "recherche": search_input, 
        "type": search_type, 
        "sources": sources,
        "date": time.strftime("%Y-%m-%d %H:%M")
    })
    
    all_results = []
    
    with st.spinner("Scraping en cours... Cela peut prendre 1-2 minutes."):
        if "Google" in sources:
            st.write("🔍 Scraping Google...")
            google_results = scrape_google_search(search_input, session)
            all_results.extend(google_results)
            
        if "Société.com" in sources:
            st.write("🏢 Scraping Société.com...")
            societe_results = scrape_societe_com(search_input, session)
            all_results.extend(societe_results)
            
        if "Pappers" in sources:
            st.write("📊 Scraping Pappers...")
            pappers_results = scrape_pappers(search_input, session)
            all_results.extend(pappers_results)
            
        if "Pages Jaunes" in sources:
            st.write("📞 Scraping Pages Jaunes...")
            pj_results = scrape_pages_jaunes(search_input, session)
            all_results.extend(pj_results)
            
        if "Infogreffe" in sources:
            st.write("⚖️ Scraping Infogreffe...")
            info_results = scrape_infogreffe(search_input, session)
            all_results.extend(info_results)
    
    st.session_state['all_results'] = all_results
    
    # Affichage des résultats
    if all_results:
        st.success(f"✅ {len(all_results)} résultats automatisés trouvés!")
        
        # Résumé des informations trouvées
        all_emails = []
        all_phones = []
        all_sirens = []
        all_addresses = []
        
        for result in all_results:
            if result.get('emails') and result['emails'] != "Aucun":
                all_emails.extend(result['emails'].split(', '))
            if result.get('téléphones') and result['téléphones'] != "Aucun":
                all_phones.extend(result['téléphones'].split(', '))
            if result.get('téléphone') and result['téléphone'] != "Non trouvé":
                all_phones.append(result['téléphone'])
            if result.get('siren') and result['siren'] != "Non trouvé":
                all_sirens.append(result['siren'])
            if result.get('adresse') and result['adresse'] not in ["Non trouvée", "Non trouvé"]:
                all_addresses.append(result['adresse'])
        
        # Affichage du résumé
        if any([all_emails, all_phones, all_sirens, all_addresses]):
            st.subheader("📋 Résumé des informations automatiquement extraites")
            col1, col2, col3, col4 = st.columns(4)
            
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
                if all_sirens:
                    st.write("🏢 **SIREN:**")
                    for siren in set(all_sirens):
                        st.write(f"• {siren}")
            
            with col4:
                if all_addresses:
                    st.write("📍 **Adresses:**")
                    for address in set(all_addresses):
                        st.write(f"• {address}")
        
        # Affichage détaillé
        st.subheader("🔍 Résultats détaillés par source")
        for result in all_results:
            with st.expander(f"📋 {result.get('source', 'Source inconnue')}"):
                for key, value in result.items():
                    if key != 'source':
                        st.write(f"**{key.title()}:** {value}")
        
        # Tableau complet
        st.subheader("📊 Tableau complet")
        df = pd.DataFrame(all_results)
        st.dataframe(df, use_container_width=True)
        
    else:
        st.warning("Aucun résultat trouvé par le scraping automatisé.")

# Export
if st.session_state.get('all_results'):
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Exporter tous les résultats"):
            df = pd.DataFrame(st.session_state['all_results'])
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Télécharger CSV complet",
                data=csv,
                file_name=f"scraping_{search_input.replace(' ', '_')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📋 Voir historique"):
            if st.session_state['history']:
                st.dataframe(pd.DataFrame(st.session_state['history']))
            else:
                st.info("Aucune recherche dans l'historique")

st.markdown("---")
st.info("""
🎯 **Version avec scraping automatisé complet :**
- Scraping direct de Google, Société.com, Pappers, Pages Jaunes, Infogreffe
- Extraction automatique d'emails, téléphones, SIREN, adresses
- Rotation des User-Agents pour éviter les blocages
- Pauses aléatoires entre requêtes
- Résumé automatique des informations trouvées

💡 **Testez avec "Azar Cohen" pour voir le scraping en action !**
""")
