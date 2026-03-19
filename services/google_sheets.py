import os
import json
import gspread # Adicione esta importação
from google.oauth2 import service_account

class GoogleSheetsService:
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.spreadsheet_id = "1xLDg039JNhTjWXDGCkRUX1HNevWTUFqgTLHol8J2bGw"
        self._connect()
    
    def _connect(self):
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Lógica de credenciais que você já tinha
            credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
            if credentials_json:
                credentials_info = json.loads(credentials_json)
                creds = service_account.Credentials.from_service_account_info(
                    credentials_info, scopes=scopes
                )
            elif os.path.exists('service-account.json'):
                creds = service_account.Credentials.from_service_account_file(
                    'service-account.json', scopes=scopes
                )
            else:
                raise Exception("Nenhuma credencial encontrada")

            # --- AQUI ESTÁ O QUE FALTAVA ---
            # Autoriza o gspread com as credenciais
            self.client = gspread.authorize(creds)
            # Abre a planilha pelo ID
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            print("✅ Conectado ao Google Sheets com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao carregar credenciais: {e}")
            raise e

    # Método para pegar todos os valores de uma aba
    def get_all_values(self, sheet_name):
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            return worksheet.get_all_values() # Este é o método do gspread
        except Exception as e:
            print(f"Erro ao buscar dados da aba {sheet_name}: {e}")
            return []

    # Método para adicionar linha (útil para o processar_venda)
    def append_row(self, sheet_name, row_data):
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            return worksheet.append_row(row_data)
        except Exception as e:
            print(f"Erro ao inserir linha na aba {sheet_name}: {e}")
            return False