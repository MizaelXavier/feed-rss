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

# Escopo necessário para o Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_credentials():
    creds = None
    # Verifica se já existem tokens salvos
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Se não há credenciais válidas, solicita ao usuário que faça login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva as credenciais para a próxima execução
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def update_sheet(service, spreadsheet_id, values):
    try:
        # Primeiro, vamos verificar se precisamos adicionar o cabeçalho
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='A1:E1'
        ).execute()
        
        # Se não houver valores, adiciona o cabeçalho
        if 'values' not in result:
            headers = [['DATA', 'UUID', 'VIDEO', 'TITLE', 'USER']]
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='A1',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': headers}
            ).execute()

        # Adiciona os novos valores
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
        print(f'Dados adicionados com sucesso!')
        return result
    except Exception as e:
        print(f'Erro ao atualizar planilha: {str(e)}')
        return None

def process_feed(rss_url):
    # Parse do feed RSS
    feed = feedparser.parse(rss_url)
    
    # Prepara os dados para a planilha
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
        
        # Extrai o link do vídeo
        video_link = entry.get('link', '')
        
        # Extrai o título
        title = entry.get('title', '')
        
        # Tenta extrair o nome do usuário do autor ou do título
        user = entry.get('author', '')
        if not user and 'author' in entry:
            user = entry['author']
        if not user:
            # Se não encontrar o autor, deixa em branco
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

def main():
    print("Iniciando automação RSS para Google Sheets...")
    
    # Solicita as informações necessárias ao usuário
    rss_url = input("Digite a URL do feed RSS: ")
    spreadsheet_id = input("Digite o ID da planilha do Google Sheets: ")
    
    print("\nAutenticando com o Google Sheets...")
    creds = get_google_credentials()
    service = build('sheets', 'v4', credentials=creds)
    
    print("\nMonitorando o feed RSS...")
    print("O script irá verificar novos vídeos a cada 5 minutos.")
    print("Para interromper o monitoramento, pressione Ctrl+C\n")
    processed_entries = set()
    
    while True:
        try:
            entries = process_feed(rss_url)
            new_entries = []
            
            for entry in entries:
                entry_id = entry[2]  # Usa o link do vídeo como identificador único
                if entry_id not in processed_entries:
                    new_entries.append(entry)
                    processed_entries.add(entry_id)
            
            if new_entries:
                print(f"\nEncontrados {len(new_entries)} novos itens!")
                update_sheet(service, spreadsheet_id, new_entries)
            else:
                print(".", end="", flush=True)  # Indica que o script está rodando
            
            time.sleep(300)  # Verifica a cada 5 minutos
            
        except Exception as e:
            print(f"\nErro durante a execução: {str(e)}")
            time.sleep(60)  # Espera 1 minuto em caso de erro

if __name__ == "__main__":
    main() 