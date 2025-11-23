import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time 
import random 
import urllib.parse 
import json 

# =================================================================
# 🔑 Impostazioni di BASE e Chiave di Sblocco Ko-fi
# =================================================================

# 1. La tua chiave segreta Ko-fi
# Leggiamo la chiave da st.secrets. 
# Se stiamo testando in locale senza aver configurato i secrets, usiamo un valore di fallback.
try:
    KOFI_PRO_KEY = st.secrets["kofi_key"]
except KeyError:
    # QUESTO VALORE DEVE ESSERE SOLO PER IL TEST LOCALE. 
    # Streamlit Cloud userà la chiave vera inserita nella sua interfaccia "Secrets".
    KOFI_PRO_KEY = "CHIAVE_DI_TEST_LOCALE" 

# 2. Il link alla tua pagina di membership/abbonamento Ko-fi
KOFI_MEMBERSHIP_LINK = "https://ko-fi.com/screemerss/tiers"

MAX_FREE_USES = 5 

# Lista di User-Agent per simulare un browser reale
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/109.0.1518.78',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
]

# =================================================================
# ⚙️ Configurazione della Pagina e Stato della Sessione
# =================================================================

st.set_page_config(
    page_title="TagTurbo: Ottimizzatore SEO Video",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inizializza lo stato della sessione per la monetizzazione
if 'count' not in st.session_state:
    st.session_state.count = 0
if 'is_pro' not in st.session_state:
    st.session_state.is_pro = False


# =================================================================
# ☕ Funzione per la Gestione dell'Accesso Pro (Sidebar)
# =================================================================

def handle_kofi_access():
    """Gestisce la logica di verifica della chiave Ko-fi nella sidebar."""
    with st.sidebar:
        st.header("⚡ Accesso Pro Illimitato")
        if st.session_state.is_pro:
            st.success("🎉 Stato PRO Attivo! Ricerche illimitate.")
            st.markdown(f"Ricerche gratuite usate oggi: {st.session_state.count}")
        else:
            st.markdown(f"**Sblocca subito** ricerche illimitate e analisi avanzate per soli **€3/mese**.")
            st.markdown(f"👉 [**Ottieni l'accesso Pro su Ko-fi!**]({KOFI_MEMBERSHIP_LINK})")

            # Campo per inserire la chiave
            user_key = st.text_input("Hai già una chiave PRO? Inseriscila qui:", type="password")
            
            if st.button("Sblocca Ora"):
                # Qui usiamo la chiave letta in modo sicuro
                if user_key == KOFI_PRO_KEY:
                    st.session_state.is_pro = True
                    st.toast("Accesso Pro sbloccato con successo!", icon='🔓')
                    st.rerun() 
                else:
                    st.error("Chiave non valida. Assicurati di aver acquistato la Membership Ko-fi.")

# =================================================================
# 🛠️ Logica Unica dello Script: Estrazione Tag Competitor (JSON Parsing)
# =================================================================

def get_optimized_tags(query):
    """
    Cerca direttamente su YouTube i video più rilevanti e ne estrae i tag analizzando il JSON.
    """
    if not query:
        return [], []
        
    st.info(f"Analisi della concorrenza per: **{query}**...")
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS) 
    }
    
    try:
        # 1. CERCA DIRETTAMENTE SUI RISULTATI DI RICERCA DI YOUTUBE
        youtube_search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
        
        response = requests.get(youtube_search_url, headers=headers)
        response.raise_for_status() 
        time.sleep(random.uniform(2, 4)) # Ritardo per simulare utente
        
        soup = BeautifulSoup(response.text, 'html.parser')
        youtube_links = []
        
        # 2. TROVA I LINK AI VIDEO YOUTUBE ANALIZZANDO IL CODICE JAVASCRIPT/JSON
        
        # Cerca la variabile JavaScript 'ytInitialData'
        script_tag = soup.find('script', text=re.compile('var ytInitialData'))
        
        if script_tag:
            # Estrai e carica il JSON
            json_text = script_tag.string.split('var ytInitialData = ')[1].split(';')[0]
            data = json.loads(json_text)
            
            # Naviga la complessa struttura JSON di YouTube
            contents_path = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
            
            if contents_path and len(contents_path) > 0 and 'itemSectionRenderer' in contents_path[0]:
                search_results = contents_path[0]['itemSectionRenderer']['contents']
                
                for item in search_results:
                    if 'videoRenderer' in item:
                        video_id = item['videoRenderer']['videoId']
                        clean_url = f"https://www.youtube.com/watch?v={video_id}"
                        
                        if clean_url not in youtube_links:
                            youtube_links.append(clean_url)
                        
                        # Limite per utenti PRO (10) vs Free (5)
                        limit = 10 if st.session_state.is_pro else 5
                        if len(youtube_links) >= limit: 
                            break

        if not youtube_links:
            st.error("Nessun video YouTube trovato. Prova una query diversa. Il parsing JSON è fallito o non ci sono video.")
            return [], []

        # 3. ESTRAZIONE DEI TAG DA OGNI VIDEO
        all_competitor_tags = set()
        
        for i, url in enumerate(youtube_links):
            try:
                time.sleep(random.uniform(0.5, 1.5)) # Piccolo ritardo
                
                video_response = requests.get(url, headers=headers, timeout=7) 
                video_soup = BeautifulSoup(video_response.text, 'html.parser')
                
                # Estrae il meta tag 'keywords'
                meta_tag = video_soup.find('meta', attrs={'name': 'keywords'})
                
                if meta_tag and 'content' in meta_tag.attrs:
                    tag_string = meta_tag['content']
                    tags = [tag.strip().lower() for tag in tag_string.split(',') if tag.strip()]
                    all_competitor_tags.update(tags)
            except requests.exceptions.RequestException:
                continue 
                
        
        # 4. SUDDIVISIONE E CLASSIFICAZIONE
        high_perf_tags = sorted(list({tag for tag in all_competitor_tags if len(tag.split()) <= 2})) 
        low_comp_tags = sorted(list({tag for tag in all_competitor_tags if len(tag.split()) > 2}))
        
        # 5. ARRICCHIMENTO
        if not low_comp_tags:
            low_comp_tags.append(query.lower())
            
        return high_perf_tags, low_comp_tags
        
    except requests.exceptions.RequestException as e:
        st.error(f"Errore di connessione o HTTP: {e}. Il tuo IP potrebbe essere stato temporaneamente bloccato.")
        return [], []
    except json.JSONDecodeError:
        st.error("Errore nel decodificare i dati JSON di YouTube. Struttura della pagina inattesa.")
        return [], []
    except Exception as e:
        st.error(f"Si è verificato un errore inatteso: {e}")
        return [], []


# =================================================================
# 💻 Corpo Principale dell'App
# =================================================================

handle_kofi_access()

st.title("🚀 TagTurbo: Generatore SEO di Nicchia")
st.markdown("Analizza i competitor e genera i tag vincenti per i tuoi video in pochi secondi.")

search_query = st.text_input(
    "🔍 Inserisci l'argomento del tuo video (es. 'migliori ETF per dividendi 2025')",
    key="topic_input"
)

if st.button("Genera Tag Ottimizzati 🧙‍♂️", type="primary", use_container_width=True):
    
    if not search_query:
        st.warning("Devi inserire un argomento per generare i tag.")
        st.stop()
    
    # A. Controllo del Limite Gratuito
    if not st.session_state.is_pro and st.session_state.count >= MAX_FREE_USES:
        st.error(f"❌ Limite Gratuito Raggiunto! Hai usato {MAX_FREE_USES} ricerche gratuite.")
        st.warning(f"Per continuare, [**sblocca l'accesso Pro dalla sidebar!**]({KOFI_MEMBERSHIP_LINK})")
        st.stop()
        
    # B. Esecuzione della Logica
    with st.spinner('Analisi della concorrenza e scraping JSON in corso...'):
        high_perf_tags, low_comp_tags = get_optimized_tags(search_query)

        if high_perf_tags or low_comp_tags:
            
            # C. Incremento del Contatore (solo per utenti Free)
            if not st.session_state.is_pro:
                st.session_state.count += 1
                st.toast(f"Ricerche gratuite rimanenti: {MAX_FREE_USES - st.session_state.count}", icon='⏳')
                
            st.success("✅ Generazione Completata!")
            
            # D. Output dei Risultati
            st.subheader("1. Tag ad Alta Performance (dei competitor)")
            st.code(", ".join(high_perf_tags), language='text')
            st.caption(f"Totale Tag: {len(high_perf_tags)}. Analisi su {10 if st.session_state.is_pro else 5} competitor.")
            
            st.subheader("2. Tag a Bassa Concorrenza (Long-Tail)")
            st.code(", ".join(low_comp_tags), language='text')
            st.caption(f"Questi ti aiutano ad essere trovato nelle ricerche più specifiche e con meno competizione.")
            
            # Tabella e Download
            total_tags = high_perf_tags + low_comp_tags
            data = {'Tipo': ['Alta Performance'] * len(high_perf_tags) + ['Bassa Concorrenza'] * len(low_comp_tags),
                    'Tag': total_tags}
            df = pd.DataFrame(data)
            
            st.markdown("---")
            st.subheader(f"Riepilogo e Esportazione (Totale: {len(total_tags)} Tag)")
            
            st.download_button(
                label="Scarica tutti i tag (CSV)",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name=f"TagTurbo_{search_query.replace(' ', '_')}.csv",
                mime='text/csv',
            )
            
            st.dataframe(df, use_container_width=True)

        else:
            st.warning("Non è stato possibile estrarre tag utili. Prova una ricerca più specifica.")