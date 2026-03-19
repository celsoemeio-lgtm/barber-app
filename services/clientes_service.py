from config import Config
from datetime import datetime

class ClientesService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def listar_clientes(self):
        """Retorna lista de todos os clientes com todos os dados"""
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['clientes'])
            clientes = []
            
            for i in range(1, len(valores)):
                linha = valores[i]
                clientes.append({
                    'nome': linha[0] if len(linha) > 0 else "",
                    'whatsapp': linha[1] if len(linha) > 1 else "",
                    'plano': linha[2] if len(linha) > 2 else ""
                })
            
            return clientes
        except Exception as e:
            print(f"Erro ao listar clientes: {e}")
            return []
    
    def salvar_cliente(self, nome, whats, plano, idx=None):
        """Salva ou edita um cliente"""
        try:
            aba = self.sheets.get_aba(Config.SHEETS['clientes'])
            
            # Se tem índice, é edição
            if idx is not None and idx != "":
                linha_editar = int(idx) + 2  # +2 por causa do cabeçalho e índice 0
                aba.update_cell(linha_editar, 1, nome)
                aba.update_cell(linha_editar, 2, whats)
                aba.update_cell(linha_editar, 3, plano)
            else:
                # Novo cliente
                data_hoje = self.sheets.get_data_formatada()
                aba.append_row([nome, whats, plano, data_hoje])
            
            return "ok"
        except Exception as e:
            return f"Erro: {e}"
    
    def buscar_nomes_clientes(self):
        """Retorna apenas os nomes dos clientes para select"""
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['clientes'])
            nomes = []
            
            for i in range(1, len(valores)):
                if valores[i][0]:  # Se tem nome
                    nomes.append(valores[i][0].strip())
            
            return sorted(nomes)  # Ordem alfabética
        except Exception as e:
            print(f"Erro ao buscar nomes: {e}")
            return []
    
    def buscar_cliente_por_whats(self, whats):
        """Busca cliente pelo WhatsApp"""
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['clientes'])
            whats_limpo = ''.join(filter(str.isdigit, whats))
            
            for i in range(1, len(valores)):
                linha = valores[i]
                if len(linha) < 2:
                    continue
                
                whats_planilha = ''.join(filter(str.isdigit, linha[1]))
                
                if whats_planilha == whats_limpo:
                    return {
                        'nome': linha[0],
                        'whatsapp': linha[1],
                        'plano': linha[2] if len(linha) > 2 else "Avulso"
                    }
            return None
        except Exception as e:
            print(f"Erro ao buscar por WhatsApp: {e}")
            return None