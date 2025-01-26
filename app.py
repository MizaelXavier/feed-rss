import streamlit as st
import feedparser
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import time
from datetime import datetime
import uuid
import json
import base64
import pandas as pd
from models import SessionLocal, RSSFeed

# Configuração da página
st.set_page_config(
    page_title="Monitor de Feed RSS",
    page_icon="📰",
    layout="wide"
)

# Função para obter sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Título principal
st.title("📰 Monitor de Feed RSS para Google Sheets")

# Sidebar para configurações
st.sidebar.header("Configurações")

# Campos de entrada
nome = st.sidebar.text_input("Nome do Monitor", key="nome")
feed_rss = st.sidebar.text_input("URL do Feed RSS", key="feed_rss")
sheet_id = st.sidebar.text_input("ID da Planilha Google Sheets", key="sheet_id")

# Área de logs
if 'logs' not in st.session_state:
    st.session_state.logs = []

def add_log(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.insert(0, f"[{current_time}] {message}")

# Função para salvar feed no banco de dados
def save_feed_to_db(nome, feed_url, sheet_id):
    try:
        db = get_db()
        feed = RSSFeed(
            id=str(uuid.uuid4()),
            name=nome,
            feed_url=feed_url,
            sheet_id=sheet_id,
            is_active=True,
            last_check=datetime.utcnow()
        )
        db.add(feed)
        db.commit()
        add_log(f"✅ Feed '{nome}' salvo no banco de dados com sucesso!")
        return True
    except Exception as e:
        add_log(f"❌ Erro ao salvar feed no banco de dados: {str(e)}")
        return False

# Função para atualizar último check do feed
def update_feed_last_check(feed_id):
    try:
        db = get_db()
        feed = db.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
        if feed:
            feed.last_check = datetime.utcnow()
            db.commit()
    except Exception as e:
        add_log(f"❌ Erro ao atualizar último check: {str(e)}")

# Função para listar feeds ativos
def get_active_feeds():
    try:
        db = get_db()
        feeds = db.query(RSSFeed).filter(RSSFeed.is_active == True).all()
        return feeds
    except Exception as e:
        add_log(f"❌ Erro ao buscar feeds ativos: {str(e)}")
        return []

# Função para processar o feed
def process_feed(rss_url):
    feed = feedparser.parse(rss_url)
    entries = []
    for entry in feed.entries:
        # Extrai a data e formata
        published_date = entry.get('published', '')
        try:
            if published_date:
                date_obj = datetime.strptime(published_date, '%a, %d %b %Y %H:%M:%S %z')
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            else:
                formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Gera UUID único para cada entrada
        entry_uuid = str(uuid.uuid4())
        
        # Extrai informações
        video_link = entry.get('link', '')
        title = entry.get('title', '')
        user = entry.get('author', '')
        if not user and 'author' in entry:
            user = entry['author']
        if not user:
            user = ''

        row = [
            formatted_date,
            entry_uuid,
            video_link,
            title,
            user
        ]
        entries.append(row)
    
    return entries

def get_google_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', ['https://www.googleapis.com/auth/spreadsheets'])
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def update_sheet(service, spreadsheet_id, values):
    try:
        # Verifica cabeçalho
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='A1:E1'
        ).execute()
        
        if 'values' not in result:
            headers = [['DATA', 'UUID', 'VIDEO', 'TITLE', 'USER']]
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='A1',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': headers}
            ).execute()

        # Adiciona valores
        body = {
            'values': values
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='A2',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        add_log(f'✅ {len(values)} novos itens adicionados à planilha!')
        return result
    except Exception as e:
        add_log(f'❌ Erro ao atualizar planilha: {str(e)}')
        return None

def get_existing_feeds(service, spreadsheet_id):
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='A:E'
        ).execute()
        
        if 'values' in result:
            values = result['values']
            if len(values) > 1:  # Se houver mais que apenas o cabeçalho
                df = pd.DataFrame(values[1:], columns=values[0])
                return df
        return pd.DataFrame(columns=['DATA', 'UUID', 'VIDEO', 'TITLE', 'USER'])
    except Exception as e:
        add_log(f'❌ Erro ao buscar feeds existentes: {str(e)}')
        return pd.DataFrame(columns=['DATA', 'UUID', 'VIDEO', 'TITLE', 'USER'])

# Layout em duas colunas
col1, col2 = st.columns([1, 1])

# Área principal
if st.sidebar.button("Iniciar Monitoramento", key="start"):
    if not nome or not feed_rss or not sheet_id:
        st.error("Por favor, preencha todos os campos!")
    else:
        try:
            # Salva o feed no banco de dados
            if save_feed_to_db(nome, feed_rss, sheet_id):
                # Inicializa credenciais do Google
                add_log("🔑 Autenticando com Google Sheets...")
                creds = get_google_credentials()
                service = build('sheets', 'v4', credentials=creds)
                
                # Inicializa conjunto para rastrear entradas processadas
                processed_entries = set()
                
                # Container para logs em tempo real
                with col1:
                    log_container = st.empty()
                
                # Container para feeds existentes
                with col2:
                    feeds_container = st.empty()
                
                while True:
                    try:
                        entries = process_feed(feed_rss)
                        new_entries = []
                        
                        for entry in entries:
                            entry_id = entry[2]  # Usa o link como identificador
                            if entry_id not in processed_entries:
                                new_entries.append(entry)
                                processed_entries.add(entry_id)
                        
                        if new_entries:
                            update_sheet(service, sheet_id, new_entries)
                        
                        # Atualiza último check no banco
                        update_feed_last_check(feed_rss)
                        
                        # Atualiza logs na interface
                        with log_container.container():
                            st.write("### Logs do Sistema")
                            for log in st.session_state.logs[:50]:  # Mostra últimos 50 logs
                                st.text(log)
                        
                        # Atualiza feeds existentes
                        with feeds_container.container():
                            st.write("### Feeds Existentes")
                            df = get_existing_feeds(service, sheet_id)
                            if not df.empty:
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info("Nenhum feed encontrado ainda.")
                        
                        time.sleep(300)  # Verifica a cada 5 minutos
                        
                    except Exception as e:
                        add_log(f"❌ Erro durante a execução: {str(e)}")
                        time.sleep(60)
                    
        except Exception as e:
            st.error(f"Erro ao iniciar monitoramento: {str(e)}")

# Layout inicial em duas colunas
with col1:
    st.write("### Logs do Sistema")
    for log in st.session_state.logs[:50]:
        st.text(log)

with col2:
    st.write("### Feeds Existentes")
    if sheet_id:
        try:
            creds = get_google_credentials()
            service = build('sheets', 'v4', credentials=creds)
            df = get_existing_feeds(service, sheet_id)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Nenhum feed encontrado ainda.")
        except Exception as e:
            st.error(f"Erro ao carregar feeds existentes: {str(e)}")
    else:
        st.info("Insira o ID da planilha para visualizar os feeds existentes.") 