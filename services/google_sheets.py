import os
import json
import gspread
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
            
            # TENTAR PRIMEIRO: Secret File do Render (/etc/secrets/)
            secret_file = '/etc/secrets/service-account.json'
            if os.path.exists(secret_file):
                print("✅ Usando secret file do Render")
                creds = service_account.Credentials.from_service_account_file(
                    secret_file, scopes=scopes
                )
            
            # TENTAR SEGUNDO: Variável de ambiente GOOGLE_CREDENTIALS
            elif os.environ.get('GOOGLE_CREDENTIALS'):
                print("✅ Usando GOOGLE_CREDENTIALS do ambiente")
                credentials_info = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
                creds = service_account.Credentials.from_service_account_info(
                    credentials_info, scopes=scopes
                )
            
            # TENTAR TERCEIRO: Arquivo local (desenvolvimento)
            elif os.path.exists('service-account.json'):
                print("✅ Usando service-account.json local")
                creds = service_account.Credentials.from_service_account_file(
                    'service-account.json', scopes=scopes
                )
            
            else:
                raise Exception("Nenhuma credencial encontrada")

            # Autoriza o gspread com as credenciais
            self.client = gspread.authorize(creds)
            # Abre a planilha pelo ID
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            print("✅ Conectado ao Google Sheets com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao carregar credenciais: {e}")
            raise e

    def get_all_values(self, sheet_name):
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            return worksheet.get_all_values()
        except Exception as e:
            print(f"Erro ao buscar dados da aba {sheet_name}: {e}")
            return []

    def append_row(self, sheet_name, row_data):
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            return worksheet.append_row(row_data)
        except Exception as e:
            print(f"Erro ao inserir linha na aba {sheet_name}: {e}")
            return False
    
    def get_aba(self, nome_aba):
        """
        Retorna uma worksheet (aba) específica da planilha
        """
        try:
            worksheet = self.spreadsheet.worksheet(nome_aba)
            return worksheet
        except Exception as e:
            print(f"❌ Erro ao acessar aba '{nome_aba}': {e}")
            return None
    
    # ==================== MÉTODO ADICIONADO ====================
    
    def delete_row(self, sheet_name, row_number):
        """
        Deleta uma linha específica de uma aba
        """
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            worksheet.delete_rows(row_number)
            print(f"✅ Linha {row_number} deletada da aba {sheet_name}")
            return True
        except Exception as e:
            print(f"❌ Erro ao deletar linha {row_number} da aba {sheet_name}: {e}")
            return False