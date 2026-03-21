import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    
    # Google Sheets
    SPREADSHEET_ID = "1xLDg039JNhTjWXDGCkRUX1HNevWTUFqgTLHol8J2bGw"
    SERVICE_ACCOUNT_FILE = 'service-account.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
              'https://www.googleapis.com/auth/drive']
    
    # Nomes das abas
    SHEETS = {
        'agenda': 'Agenda',
        'clientes': 'Cad_Clientes_Simples',
        'servicos': 'Cad_Serviços',
        'barbeiros': 'Cad_Barbeiros',
        'vendas': 'BASE_VENDAS'
    }
    
    # Pastas do Drive
    FOTOS_FOLDER_ID = "16uIn_8OVj0xr0sMkU8sz7D9VX2epjV6M"

    