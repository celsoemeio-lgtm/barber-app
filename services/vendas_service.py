from config import Config
from datetime import datetime

class VendasService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def get_dados_iniciais(self):
        """Retorna barbeiros, clientes e serviços para o formulário"""
        try:
            print("\n" + "="*50)
            print("🔍 BUSCANDO DADOS INICIAIS")
            print("="*50)
            
            # 1. BARBEIROS ATIVOS
            print(f"\n📌 Buscando aba: '{Config.SHEETS['barbeiros']}'")
            try:
                aba_b = self.sheets.get_aba(Config.SHEETS['barbeiros'])
                dados_b = aba_b.get_all_values()
                print(f"✅ Total de barbeiros na planilha: {len(dados_b)-1}")
                barbeiros = []
                for i in range(1, len(dados_b)):
                    if dados_b[i][0] and (len(dados_b[i]) <= 11 or dados_b[i][11] == "ATIVO"):
                        barbeiros.append(dados_b[i][0])
                print(f"✅ Barbeiros ativos: {len(barbeiros)}")
            except Exception as e:
                print(f"❌ Erro ao buscar barbeiros: {e}")
                barbeiros = []
            
            # 2. CLIENTES
            print(f"\n📌 Buscando aba: '{Config.SHEETS['clientes']}'")
            try:
                aba_c = self.sheets.get_aba(Config.SHEETS['clientes'])
                dados_c = aba_c.get_all_values()
                print(f"✅ Total de clientes na planilha: {len(dados_c)-1}")
                clientes = []
                for i in range(1, len(dados_c)):
                    if dados_c[i][0]:
                        clientes.append({
                            'nome': dados_c[i][0],
                            'plano': dados_c[i][2] if len(dados_c[i]) > 2 else "Avulso"
                        })
                print(f"✅ Clientes carregados: {len(clientes)}")
            except Exception as e:
                print(f"❌ Erro ao buscar clientes: {e}")
                clientes = []
            
            # 3. SERVIÇOS
            nome_aba_servicos = Config.SHEETS['servicos']
            print(f"\n📌 Buscando aba: '{nome_aba_servicos}'")
            
            try:
                aba_s = self.sheets.get_aba(nome_aba_servicos)
                dados_s = aba_s.get_all_values()
                print(f"✅ Total de linhas na aba: {len(dados_s)}")
                print(f"✅ Cabeçalho: {dados_s[0] if dados_s else 'Vazio'}")
                
                servicos = []
                for i in range(1, len(dados_s)):
                    linha = dados_s[i]
                    if len(linha) > 0 and linha[0]:
                        nome = linha[0].strip()
                        
                        # Pega o preço da coluna B (índice 1)
                        preco_str = linha[1] if len(linha) > 1 else "0"
                        print(f"   Linha {i}: {nome} - Preço bruto: '{preco_str}'")
                        
                        # Converte preço corretamente
                        try:
                            # Remove R$, espaços, troca vírgula por ponto
                            preco_limpo = str(preco_str).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
                            preco = float(preco_limpo) if preco_limpo else 0
                            print(f"      ✅ Convertido: {preco}")
                        except Exception as e:
                            print(f"      ⚠️ Erro na conversão: {e}")
                            preco = 0
                        
                        servicos.append({
                            'nome': nome,
                            'preco': preco
                        })
                
                print(f"\n✅ Total de serviços carregados: {len(servicos)}")
                
                # Mostra resumo dos serviços
                if servicos:
                    print("\n📋 SERVIÇOS CARREGADOS:")
                    for s in servicos[:5]:
                        print(f"   - {s['nome']}: R$ {s['preco']:.2f}")
                    if len(servicos) > 5:
                        print(f"   ... e mais {len(servicos)-5} serviços")
                
            except Exception as e:
                print(f"❌ Erro ao acessar aba '{nome_aba_servicos}': {e}")
                servicos = []
            
            print("\n" + "="*50)
            print("✅ CARREGAMENTO CONCLUÍDO")
            print("="*50 + "\n")
            
            return {
                'barbeiros': barbeiros,
                'clientes': clientes,
                'servicos': servicos
            }
        except Exception as e:
            print(f"❌ Erro geral em get_dados_iniciais: {e}")
            import traceback
            traceback.print_exc()
            return {'erro': str(e)}
    
    def processar_venda(self, dados):
        """Registra venda na BASE_VENDAS"""
        try:
            print("\n" + "="*50)
            print("💵 PROCESSANDO VENDA")
            print("="*50)
            print(f"Cliente: {dados['cliente']}")
            print(f"Barbeiro: {dados['barbeiro']}")
            print(f"Plano: {dados['plano']}")
            print(f"Itens: {len(dados['itens'])}")
            print(f"Valor Pago: {dados['valorPago']}")
            
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
            
            print(f"Total Tabela: R$ {total_tabela:.2f}")
            print(f"Valor Pago: R$ {valor_pago:.2f}")
            print(f"Desconto: R$ {valor_desconto:.2f}")
            
            for idx, item in enumerate(dados['itens']):
                soma_total = valor_pago if idx == 0 else 0
                desconto = valor_desconto if idx == 0 else 0
                
                linha = [
                    data_formatada,
                    hora_formatada,
                    dados['cliente'],
                    item['nome'],
                    dados['barbeiro'],
                    item['preco'],
                    dados['plano'],
                    soma_total,
                    desconto
                ]
                print(f"   Registrando item: {item['nome']} - R$ {item['preco']:.2f}")
                aba.append_row(linha)
            
            print("✅ Venda registrada com sucesso!")
            print("="*50 + "\n")
            
            return {'sucesso': True}
        except Exception as e:
            print(f"❌ Erro ao processar venda: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e)}