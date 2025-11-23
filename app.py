import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time 
import random 
import urllib.parse 
from youtubesearchpython import VideosSearch
import json 

# =================================================================
# 🌐 Dizionario dei Testi Bilingue (IT e EN)
# =================================================================

TEXT_LABELS = {
    'it': {
        'page_title': "TagTurbo: Ottimizzatore SEO Video",
        'main_title': "🚀 TagTurbo: Generatore SEO di Nicchia",
        'subtitle': "Analizza i competitor e genera i tag vincenti per i tuoi video in pochi secondi.",
        'search_placeholder': "🔍 Inserisci l'argomento del tuo video (es. 'migliori ETF per dividendi 2025')",
        'button_generate': "Genera Tag Ottimizzati 🧙‍♂️",
        'search_query_missing': "Devi inserire un argomento per generare i tag.",
        'limit_reached': "❌ Limite Gratuito Raggiunto! Hai usato {} ricerche gratuite.",
        'unlock_cta_warning': "Per continuare, [**sblocca l'accesso Pro dalla sidebar!**]({})",
        'analysis_in_progress': "Ricerca stabile dei competitor e scraping dei meta-tag in corso...",
        'generation_success': "✅ Generazione Completata!",
        'high_perf_tags_title': "1. Tag ad Alta Performance (dei competitor)",
        'long_tail_tags_title': "2. Tag a Bassa Concorrenza (Long-Tail)",
        'tag_count_caption': "Totale Tag: {}. Analisi su {} competitor.",
        'low_comp_caption': "Questi ti aiutano ad essere trovato nelle ricerche più specifiche e con meno competizione.",
        'summary_title': "Riepilogo e Esportazione (Totale: {} Tag)",
        'download_label': "Scarica tutti i tag (CSV)",
        'table_type': 'Tipo',
        'table_tag': 'Tag',
        'type_high': 'Alta Performance',
        'type_low': 'Bassa Concorrenza',
        'no_tags_found': "Non è stato possibile estrarre tag utili. Prova una ricerca più specifica.",
        'sidebar_header': "⚡ Accesso Pro Illimitato",
        'pro_active': "🎉 Stato PRO Attivo! Ricerche illimitate.",
        'free_uses_caption': "Ricerche gratuite usate oggi: {}",
        'free_cta_text': "**Sblocca subito** ricerche illimitate e analisi avanzate per soli **€3/mese**.",
        'pro_link_text': "👉 [**Ottieni l'accesso Pro su Ko-fi!**]({})",
        'pro_key_input': "Hai già una chiave PRO? Inseriscila qui:",
        'unlock_button': "Sblocca Ora",
        'invalid_key': "Chiave non valida. Assicurati di aver acquistato la Membership Ko-fi.",
        'key_success_toast': "Accesso Pro sbloccato con successo!",
        'language_selector': "Seleziona Lingua",
        'search_error': "Si è verificato un errore inaspettato durante la ricerca: {}",
    },
    'en': {
        'page_title': "TagTurbo: Video SEO Optimizer",
        'main_title': "🚀 TagTurbo: Niche SEO Tag Generator",
        'subtitle': "Analyze competitors and generate winning tags for your videos in seconds.",
        'search_placeholder': "🔍 Enter your video topic (e.g., 'best dividend ETFs 2025')",
        'button_generate': "Generate Optimized Tags 🧙‍♂️",
        'search_query_missing': "You must enter a topic to generate tags.",
        'limit_reached': "❌ Free Limit Reached! You have used {} free searches.",
        'unlock_cta_warning': "To continue, [**unlock Pro access in the sidebar!**]({})",
        'analysis_in_progress': "Stable competitor search and meta-tag scraping in progress...",
        'generation_success': "✅ Generation Complete!",
        'high_perf_tags_title': "1. High-Performance Tags (from competitors)",
        'long_tail_tags_title': "2. Low-Competition Tags (Long-Tail)",
        'tag_count_caption': "Total Tags: {}. Analysis on {} competitors.",
        'low_comp_caption': "These help you get found in more specific, low-competition searches.",
        'summary_title': "Summary and Export (Total: {} Tags)",
        'download_label': "Download All Tags (CSV)",
        'table_type': 'Type',
        'table_tag': 'Tag',
        'type_high': 'High Performance',
        'type_low': 'Low Competition',
        'no_tags_found': "Could not extract useful tags. Try a more specific search.",
        'sidebar_header': "⚡ Unlimited Pro Access",
        'pro_active': "🎉 PRO Status Active! Unlimited searches.",
        'free_uses_caption': "Free searches used today: {}",
        'free_cta_text': "**Unlock unlimited** searches and advanced analysis for only **€3/month**.",
        'pro_link_text': "👉 [**Get Pro Access on Ko-fi!**]({})",
        'pro_key_input': "Got a PRO key? Enter it here:",
        'unlock_button': "Unlock Now",
        'invalid_key': "Invalid key. Please ensure you have purchased the Ko-fi Membership.",
        'key_success_toast': "Pro access unlocked successfully!",
        'language_selector': "Select Language",
        'search_error': "An unexpected error occurred during the search: {}",
    }
}

# =================================================================
# ⚙️ Funzione per Ottenere il Testo Corretto
# =================================================================

def get_text(key, lang=None):
    """Restituisce il testo nella lingua selezionata, o italiano come fallback."""
    if lang is None:
        lang = st.session_state.language
    return TEXT_LABELS[lang].get(key, TEXT_LABELS['it'].get(key, f"MISSING TEXT: {key}"))


# =================================================================
# 🔑 Impostazioni di BASE e Chiave di Sblocco Ko-fi
# =================================================================

try:
    KOFI_PRO_KEY = st.secrets["kofi_key"]
except KeyError:
    KOFI_PRO_KEY = "CHIAVE_DI_TEST_LOCALE" 

KOFI_MEMBERSHIP_LINK = "https://ko-fi.com/screemerss/tiers"
MAX_FREE_USES = 5 

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/109.0.1518.78',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
]

# =================================================================
# ⚙️ Configurazione della Pagina e Stato della Sessione
# =================================================================

# Imposta lingua predefinita
if 'language' not in st.session_state:
    st.session_state.language = 'it'

st.set_page_config(
    page_title=get_text('page_title'),
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
        # Selettore di Lingua
        st.session_state.language = st.selectbox(
            get_text('language_selector', lang='it'), # Usa sempre il testo IT per il selettore se non in sessione
            options=['it', 'en'],
            format_func=lambda x: 'Italiano' if x == 'it' else 'English',
            key='lang_select'
        )
        
        st.header(get_text('sidebar_header'))
        
        if st.session_state.is_pro:
            st.success(get_text('pro_active'))
            st.markdown(get_text('free_uses_caption').format(st.session_state.count))
        else:
            st.markdown(get_text('free_cta_text'))
            st.markdown(get_text('pro_link_text').format(KOFI_MEMBERSHIP_LINK))

            # Campo per inserire la chiave
            user_key = st.text_input(get_text('pro_key_input'), type="password")
            
            if st.button(get_text('unlock_button')):
                if user_key == KOFI_PRO_KEY:
                    st.session_state.is_pro = True
                    st.toast(get_text('key_success_toast'), icon='🔓')
                    st.rerun() 
                else:
                    st.error(get_text('invalid_key'))

# =================================================================
# 🛠️ Logica Unica dello Script: Estrazione Tag Competitor
# =================================================================

def get_optimized_tags(query):
    """
    Cerca su YouTube i video più rilevanti usando la libreria youtube-search-python,
    poi estrae i tag dai metadati di ogni pagina video.
    """
    if not query:
        return [], []
        
    st.info(get_text('analysis_in_progress').replace('...', f": **{query}**...")) # Breve hack per usare la stringa di info
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS) 
    }
    
    try:
        # 1. CERCA I LINK AI VIDEO YOUTUBE USANDO LA LIBRERIA
        
        limit = 10 if st.session_state.is_pro else 5
        
        videosSearch = VideosSearch(query, limit=limit)
        results = videosSearch.result()
        
        youtube_links = []
        for video in results.get('result', []):
            youtube_links.append(video['link'])

        if not youtube_links:
            st.error(get_text('no_tags_found'))
            return [], []

        # 2. ESTRAZIONE DEI TAG DA OGNI VIDEO (Tramite scraping dei meta-tag)
        all_competitor_tags = set()
        
        for i, url in enumerate(youtube_links):
            try:
                time.sleep(random.uniform(0.5, 1.5))
                video_response = requests.get(url, headers=headers, timeout=7) 
                video_soup = BeautifulSoup(video_response.text, 'html.parser')
                meta_tag = video_soup.find('meta', attrs={'name': 'keywords'})
                
                if meta_tag and 'content' in meta_tag.attrs:
                    tag_string = meta_tag['content']
                    tags = [tag.strip().lower() for tag in tag_string.split(',') if tag.strip()]
                    all_competitor_tags.update(tags)
            except requests.exceptions.RequestException:
                continue 
                
        # 3. SUDDIVISIONE E CLASSIFICAZIONE
        high_perf_tags = sorted(list({tag for tag in all_competitor_tags if len(tag.split()) <= 2})) 
        low_comp_tags = sorted(list({tag for tag in all_competitor_tags if len(tag.split()) > 2}))
        
        if not low_comp_tags:
            low_comp_tags.append(query.lower())
            
        return high_perf_tags, low_comp_tags
        
    except Exception as e:
        st.error(get_text('search_error').format(e))
        return [], []


# =================================================================
# 💻 Corpo Principale dell'App
# =================================================================

handle_kofi_access()

st.title(get_text('main_title'))
st.markdown(get_text('subtitle'))

search_query = st.text_input(
    get_text('search_placeholder'),
    key="topic_input",
    label_visibility="collapsed",
    placeholder=get_text('search_placeholder')
)

if st.button(get_text('button_generate'), type="primary", use_container_width=True):
    
    if not search_query:
        st.warning(get_text('search_query_missing'))
        st.stop()
    
    # A. Controllo del Limite Gratuito
    if not st.session_state.is_pro and st.session_state.count >= MAX_FREE_USES:
        st.error(get_text('limit_reached').format(MAX_FREE_USES))
        st.warning(get_text('unlock_cta_warning').format(KOFI_MEMBERSHIP_LINK))
        st.stop()
        
    # B. Esecuzione della Logica
    with st.spinner(get_text('analysis_in_progress')):
        high_perf_tags, low_comp_tags = get_optimized_tags(search_query)

        if high_perf_tags or low_comp_tags:
            
            # C. Incremento del Contatore (solo per utenti Free)
            if not st.session_state.is_pro:
                st.session_state.count += 1
                st.toast(get_text('free_uses_caption').format(MAX_FREE_USES - st.session_state.count), icon='⏳')
                
            st.success(get_text('generation_success'))
            
            # D. Output dei Risultati
            competitor_count = 10 if st.session_state.is_pro else 5
            
            st.subheader(get_text('high_perf_tags_title'))
            st.code(", ".join(high_perf_tags), language='text')
            st.caption(get_text('tag_count_caption').format(len(high_perf_tags), competitor_count))
            
            st.subheader(get_text('long_tail_tags_title'))
            st.code(", ".join(low_comp_tags), language='text')
            st.caption(get_text('low_comp_caption'))
            
            # Tabella e Download
            total_tags = high_perf_tags + low_comp_tags
            data = {
                get_text('table_type'): [get_text('type_high')] * len(high_perf_tags) + [get_text('type_low')] * len(low_comp_tags),
                get_text('table_tag'): total_tags
            }
            df = pd.DataFrame(data)
            
            st.markdown("---")
            st.subheader(get_text('summary_title').format(len(total_tags)))
            
            st.download_button(
                label=get_text('download_label'),
                data=df.to_csv(index=False).encode('utf-8'),
                file_name=f"TagTurbo_{search_query.replace(' ', '_')}.csv",
                mime='text/csv',
            )
            
            st.dataframe(df, use_container_width=True)

        else:
            st.warning(get_text('no_tags_found'))