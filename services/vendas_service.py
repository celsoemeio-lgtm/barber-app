from config import Config
from datetime import datetime

class VendasService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def get_dados_iniciais(self):
        """Retorna barbeiros, clientes e serviços para o formulário"""
        try:
            # Barbeiros ativos
            aba_b = self.sheets.get_aba(Config.SHEETS['barbeiros'])
            dados_b = aba_b.get_all_values()
            barbeiros = []
            for i in range(1, len(dados_b)):
                if dados_b[i][0] and (len(dados_b[i]) <= 11 or dados_b[i][11] == "ATIVO"):
                    barbeiros.append(dados_b[i][0])
            
            # Clientes
            aba_c = self.sheets.get_aba(Config.SHEETS['clientes'])
            dados_c = aba_c.get_all_values()
            clientes = []
            for i in range(1, len(dados_c)):
                if dados_c[i][0]:
                    clientes.append({
                        'nome': dados_c[i][0],
                        'plano': dados_c[i][2] if len(dados_c[i]) > 2 else "Avulso"
                    })
            
            # Serviços
            aba_s = self.sheets.get_aba(Config.SHEETS['servicos'])
            dados_s = aba_s.get_all_values()
            servicos = []
            for i in range(1, len(dados_s)):
                if dados_s[i][0]:
                    try:
                        preco = float(dados_s[i][1]) if len(dados_s[i]) > 1 else 0
                    except:
                        preco = 0
                    servicos.append({
                        'nome': dados_s[i][0],
                        'preco': preco
                    })
            
            return {
                'barbeiros': barbeiros,
                'clientes': clientes,
                'servicos': servicos
            }
        except Exception as e:
            return {'erro': str(e)}
    
    def processar_venda(self, dados):
        """Registra venda na BASE_VENDAS"""
        try:
            aba = self.sheets.get_aba(Config.SHEETS['vendas'])
            
            data_hoje = datetime.now()
            data_formatada = data_hoje.strftime("%d/%m/%Y")
            hora_formatada = data_hoje.strftime("%H:%M:%S")
            
            total_tabela = sum(item['preco'] for item in dados['itens'])
            
            valor_pago_str = dados['valorPago'].replace('R$', '').replace('.', '').replace(',', '.').strip()
            try:
                valor_pago = float(valor_pago_str)
            except:
                valor_pago = 0
            
            valor_desconto = max(0, total_tabela - valor_pago)
            
            for idx, item in enumerate(dados['itens']):
                soma_total = valor_pago if idx == 0 else 0
                desconto = valor_desconto if idx == 0 else 0
                
                aba.append_row([
                    data_formatada,
                    hora_formatada,
                    dados['cliente'],
                    item['nome'],
                    dados['barbeiro'],
                    item['preco'],
                    dados['plano'],
                    soma_total,
                    desconto
                ])
            
            return {'sucesso': True}
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}