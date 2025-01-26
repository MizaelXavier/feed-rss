import pickle
import json

# Lê o arquivo token.pickle
with open('token.pickle', 'rb') as token_file:
    creds = pickle.load(token_file)
    
    # Converte as credenciais para um dicionário
    creds_dict = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    
    # Converte para JSON
    creds_json = json.dumps(creds_dict)
    print("\nCopie este valor para a variável GOOGLE_CREDENTIALS no Railway:\n")
    print(creds_json) 