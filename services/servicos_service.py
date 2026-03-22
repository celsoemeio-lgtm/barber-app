from config import Config

class ServicosService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def listar_servicos(self):
        """Retorna lista de serviços com preços da planilha"""
        try:
            print("\n🔍 BUSCANDO SERVIÇOS NA PLANILHA...")
            valores = self.sheets.get_all_values(Config.SHEETS['servicos'])
            
            print(f"📊 Total de linhas na planilha: {len(valores)}")
            print(f"📋 Cabeçalho: {valores[0] if valores else 'Vazio'}")
            
            servicos = []
            for i in range(1, len(valores)):
                linha = valores[i]
                if len(linha) >= 1 and linha[0].strip():
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
            return servicos
        except Exception as e:
            print(f"❌ Erro ao listar serviços: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def listar_nomes_servicos(self):
        """Retorna apenas nomes para select (com preço formatado)"""
        try:
            servicos = self.listar_servicos()
            nomes = []
            for s in servicos:
                preco_formatado = f"{s['preco']:.2f}".replace('.', ',')
                nomes.append({
                    'nome': s['nome'],
                    'preco': preco_formatado
                })
            return nomes
        except Exception as e:
            print(f"❌ Erro ao listar nomes: {e}")
            return []
    
    def salvar_servico(self, nome, preco):
        """Salva ou edita um serviço"""
        try:
            aba = self.sheets.get_aba(Config.SHEETS['servicos'])
            valores = aba.get_all_values()
            
            linha_edit = -1
            for i in range(1, len(valores)):
                if valores[i][0].lower() == nome.lower():
                    linha_edit = i + 1
                    break
            
            # Converte preço de formato brasileiro para número
            preco_limpo = preco.replace('.', '').replace(',', '.').strip()
            preco_num = float(preco_limpo)
            
            if linha_edit != -1:
                aba.update_cell(linha_edit, 2, preco_num)
            else:
                aba.append_row([nome, preco_num])
            
            return "ok"
        except Exception as e:
            return f"Erro: {e}"