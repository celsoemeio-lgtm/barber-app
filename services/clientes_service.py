from config import Config
from datetime import datetime
import time

class ClientesService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 60  # 60 segundos de cache
    
    def _get_cache(self, key):
        """Retorna valor do cache se ainda for válido"""
        if key in self._cache and key in self._cache_time:
            if time.time() - self._cache_time[key] < self._cache_ttl:
                return self._cache[key]
        return None
    
    def _set_cache(self, key, value):
        """Guarda valor no cache"""
        self._cache[key] = value
        self._cache_time[key] = time.time()
    
    def listar_clientes(self):
        """Retorna lista de todos os clientes com cache"""
        cache_key = "listar_clientes"
        cached = self._get_cache(cache_key)
        if cached:
            print("📦 Usando cache de clientes")
            return cached
        
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
            
            self._set_cache(cache_key, clientes)
            return clientes
        except Exception as e:
            print(f"Erro ao listar clientes: {e}")
            return []
    
    def salvar_cliente(self, nome, whats, plano, idx=None):
        """Salva ou edita um cliente e limpa o cache"""
        try:
            aba = self.sheets.get_aba(Config.SHEETS['clientes'])
            
            if idx is not None and idx != "":
                linha_editar = int(idx) + 2
                aba.update_cell(linha_editar, 1, nome)
                aba.update_cell(linha_editar, 2, whats)
                aba.update_cell(linha_editar, 3, plano)
            else:
                data_hoje = self.sheets.get_data_formatada()
                aba.append_row([nome, whats, plano, data_hoje])
            
            # Limpa cache após alteração
            self._cache.pop("listar_clientes", None)
            self._cache.pop("buscar_nomes_clientes", None)
            
            return "ok"
        except Exception as e:
            return f"Erro: {e}"
    
    def buscar_nomes_clientes(self):
        """Retorna apenas os nomes dos clientes com cache"""
        cache_key = "buscar_nomes_clientes"
        cached = self._get_cache(cache_key)
        if cached:
            print("📦 Usando cache de nomes de clientes")
            return cached
        
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['clientes'])
            nomes = []
            
            for i in range(1, len(valores)):
                if valores[i][0]:
                    nomes.append(valores[i][0].strip())
            
            resultado = sorted(nomes)
            self._set_cache(cache_key, resultado)
            return resultado
        except Exception as e:
            print(f"Erro ao buscar nomes: {e}")
            return []
    
    def buscar_cliente_por_whats(self, whats):
        """Busca cliente pelo WhatsApp (sem cache, pois é consulta pontual)"""
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