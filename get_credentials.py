import base64
import pickle

# Lê o arquivo token.pickle e converte para base64
with open('token.pickle', 'rb') as token_file:
    token_data = token_file.read()
    base64_data = base64.b64encode(token_data).decode('utf-8')
    print("\nCopie este valor para a variável GOOGLE_CREDENTIALS no Railway:\n")
    print(base64_data) 