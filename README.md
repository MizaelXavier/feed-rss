# Automação RSS para Google Sheets

Esta automação monitora um feed RSS e adiciona automaticamente novos itens a uma planilha do Google Sheets.

## Pré-requisitos

1. Python 3.7 ou superior
2. Bibliotecas Python listadas em `requirements.txt`
3. Credenciais do Google Cloud Platform

## Configuração

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure as credenciais do Google:
   - Acesse o [Google Cloud Console](https://console.cloud.google.com)
   - Crie um novo projeto ou selecione um existente
   - Ative a API do Google Sheets
   - Crie credenciais do tipo "OAuth 2.0 Client ID"
   - Baixe o arquivo de credenciais e renomeie para `credentials.json`
   - Coloque o arquivo `credentials.json` na mesma pasta do script

3. Prepare sua planilha do Google Sheets:
   - Crie uma nova planilha no Google Sheets
   - Copie o ID da planilha (encontrado na URL)
   - Compartilhe a planilha com o email da sua conta de serviço

## Uso

1. Execute o script:
```bash
python rss_to_sheets.py
```

2. Quando solicitado:
   - Digite a URL do feed RSS
   - Digite o ID da planilha do Google Sheets

3. Na primeira execução, será necessário autorizar o acesso à sua conta Google através do navegador.

O script irá monitorar o feed RSS a cada 5 minutos e adicionar novos itens à planilha automaticamente. 