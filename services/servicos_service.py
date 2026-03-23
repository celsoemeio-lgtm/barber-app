from config import Config

class ServicosService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def listar_servicos(self):
        """Retorna lista de serviços com preços"""
        try:
            print("=" * 50)
            print("🔍 BUSCANDO SERVIÇOS NA PLANILHA")
            print("=" * 50)
            
            nome_aba = Config.SHEETS['servicos']
            print(f"📌 Nome da aba configurada: '{nome_aba}'")
            
            valores = self.sheets.get_all_values(nome_aba)
            print(f"📊 Total de linhas na planilha: {len(valores)}")
            
            if valores:
                print(f"📋 Cabeçalho: {valores[0]}")
            else:
                print("⚠️ Planilha vazia!")
                return []
            
            servicos = []
            for i in range(1, len(valores)):
                linha = valores[i]
                print(f"\n📌 Linha {i+1}: {linha}")
                
                if len(linha) > 0 and linha[0]:
                    nome = linha[0].strip()
                    print(f"   Nome: '{nome}'")
                    
                    # Pega o preço da coluna B (índice 1)
                    preco_bruto = linha[1] if len(linha) > 1 else "0"
                    print(f"   Preço bruto: '{preco_bruto}'")
                    
                    # Converte de formato brasileiro para número
                    try:
                        # Remove R$, espaços, troca vírgula por ponto
                        preco_limpo = preco_bruto.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
                        print(f"   Preço limpo: '{preco_limpo}'")
                        
                        if preco_limpo:
                            preco = float(preco_limpo)
                            print(f"   ✅ Preço convertido: {preco}")
                        else:
                            preco = 0
                            print(f"   ⚠️ Preço vazio, usando 0")
                    except Exception as e:
                        print(f"   ❌ Erro na conversão: {e}")
                        preco = 0
                    
                    servicos.append({
                        'nome': nome,
                        'preco': preco
                    })
                else:
                    print(f"   ⚠️ Linha sem nome, ignorada")
            
            print(f"\n✅ Total de serviços carregados: {len(servicos)}")
            print("=" * 50 + "\n")
            
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
            print(f"❌ Erro: {e}")
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
            
            preco_num = float(preco.replace(",", "."))
            
            if linha_edit != -1:
                aba.update_cell(linha_edit, 2, preco_num)
            else:
                aba.append_row([nome, preco_num])
            
            return "ok"
        except Exception as e:
            return f"Erro: {e}"