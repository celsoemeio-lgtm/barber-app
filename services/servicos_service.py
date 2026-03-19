from config import Config

class ServicosService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def listar_servicos(self):
        """VERSÃO DE TESTE - Retorna valores fixos"""
        print("="*50)
        print("🔍 USANDO VERSÃO DE TESTE DOS SERVIÇOS")
        print("="*50)
        
        # VALORES FIXOS PARA TESTE
        servicos = [
            {'nome': 'Corte', 'preco': 35.00},
            {'nome': 'Barba', 'preco': 25.00},
            {'nome': 'Sobrancelha', 'preco': 10.00}
        ]
        
        print(f"✅ Serviços de teste: {servicos}")
        return servicos
    
    def listar_nomes_servicos(self):
        """Versão de teste com nomes e preços formatados"""
        servicos = [
            {'nome': 'Corte', 'preco': '35,00'},
            {'nome': 'Barba', 'preco': '25,00'},
            {'nome': 'Sobrancelha', 'preco': '10,00'}
        ]
        return servicos
    
    def salvar_servico(self, nome, preco):
        """Versão de teste - só retorna ok"""
        return "ok"