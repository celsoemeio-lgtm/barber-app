from models.user import User
from config import Config

class AuthService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def validar_login_barbeiro(self, user, password):
        """Valida login de barbeiro"""
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            
            for i in range(1, len(valores)):
                linha = valores[i]
                if len(linha) < 4:
                    continue
                
                nome = linha[0].strip()
                senha = linha[3].strip()
                nivel = linha[4].strip() if len(linha) > 4 else "USER"
                status = linha[11].strip() if len(linha) > 11 else "ATIVO"
                
                if nome.upper() == user.upper().strip() and senha == password:
                    if status.upper() != "ATIVO":
                        return {'sucesso': False, 'msg': "Usuário inativo"}
                    
                    return {
                        'sucesso': True,
                        'nome': nome,
                        'nivel': nivel,
                        'tipo': 'BARBEIRO'
                    }
            
            return {'sucesso': False, 'msg': "Usuário ou senha incorretos"}
        except Exception as e:
            return {'sucesso': False, 'msg': f"Erro: {str(e)}"}
    
    def gerenciar_acesso_cliente(self, dados):
        """Gerencia acesso de cliente via WhatsApp"""
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['clientes'])
            celular_busca = ''.join(filter(str.isdigit, dados.get('celular', '')))
            
            for i in range(1, len(valores)):
                linha = valores[i]
                if len(linha) < 2:
                    continue
                
                celular_planilha = ''.join(filter(str.isdigit, linha[1]))
                
                if celular_planilha == celular_busca:
                    return {
                        'status': "EXISTENTE",
                        'nome': linha[0],
                        'celular': linha[1],
                        'tipo': "CLIENTE"
                    }
            
            if dados.get('nome'):
                data_hoje = self.sheets.get_data_formatada()
                self.sheets.append_row(
                    Config.SHEETS['clientes'],
                    [dados['nome'], dados['celular'], "", data_hoje]
                )
                return {
                    'status': "NOVO",
                    'nome': dados['nome'],
                    'celular': dados['celular'],
                    'tipo': "CLIENTE"
                }
            
            return {'status': "NAO_ENCONTRADO"}
        except Exception as e:
            return {'status': "ERRO", 'msg': str(e)}
    
    def buscar_foto_barbeiro(self, nome):
        """Busca foto do barbeiro"""
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            nome_busca = nome.upper().strip()
            
            for i in range(1, len(valores)):
                if valores[i][0].upper().strip() == nome_busca:
                    return valores[i][10] if len(valores[i]) > 10 else ""
            return ""
        except:
            return ""