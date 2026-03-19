from config import Config

class BarbeirosService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def listar_nomes(self):
        """Retorna lista de nomes dos barbeiros"""
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            nomes = []
            
            for i in range(1, len(valores)):
                if valores[i][0]:
                    nomes.append(valores[i][0])
            
            return sorted(nomes)
        except:
            return []
    
    def buscar_dados(self, nome):
        """Busca dados completos de um barbeiro"""
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            
            for i in range(1, len(valores)):
                if valores[i][0] == nome:
                    return {
                        'linha': i + 1,
                        'nome': valores[i][0],
                        'whats': valores[i][1] if len(valores[i]) > 1 else "",
                        'comissao': valores[i][2] if len(valores[i]) > 2 else "",
                        'senha': valores[i][3] if len(valores[i]) > 3 else "",
                        'nivel': valores[i][4] if len(valores[i]) > 4 else "USER",
                        'meta': valores[i][5] if len(valores[i]) > 5 else "",
                        'inicio': valores[i][6] if len(valores[i]) > 6 else "Segunda",
                        'fim': valores[i][7] if len(valores[i]) > 7 else "Sexta",
                        'folga': valores[i][8] if len(valores[i]) > 8 else "Domingo",
                        'foto': valores[i][10] if len(valores[i]) > 10 else "",
                        'status': valores[i][11] if len(valores[i]) > 11 else "ATIVO"
                    }
            return None
        except:
            return None
    
    def salvar(self, dados):
        """Salva ou edita um barbeiro"""
        try:
            aba = self.sheets.get_aba(Config.SHEETS['barbeiros'])
            
            if dados.get('linhaRef') and dados['linhaRef'] != "":
                linha = int(dados['linhaRef'])
            else:
                valores = aba.get_all_values()
                linha = len(valores) + 1
            
            foto_final = dados['foto']
            if dados['foto'] and dados['foto'].startswith('data:image'):
                foto_final = dados['foto']
            
            dados_linha = [
                dados['nome'],
                dados['whats'],
                dados['comissao'],
                dados['senha'],
                dados['nivel'],
                dados['meta'],
                dados['inicio'],
                dados['fim'],
                dados['folga'],
                "",
                foto_final,
                dados['status']
            ]
            
            if linha <= len(aba.get_all_values()):
                for col, valor in enumerate(dados_linha, 1):
                    if col <= 12:
                        aba.update_cell(linha, col, valor)
            else:
                aba.append_row(dados_linha)
            
            return "ok"
        except Exception as e:
            return f"Erro: {e}"