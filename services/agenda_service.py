from config import Config
from datetime import datetime
import time

class AgendaService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
        self._cache_barbeiros = None
        self._cache_barbeiros_time = None
        self._cache_agendamentos = {}
        self._cache_agendamentos_time = {}
        self._cache_ttl = 60  # 60 segundos para agendamentos
    
    def _get_barbeiros_ativos(self):
        """Busca barbeiros ativos com cache"""
        if self._cache_barbeiros_time:
            if time.time() - self._cache_barbeiros_time < 300:  # 5 minutos
                print("📦 Usando cache de barbeiros ativos")
                return self._cache_barbeiros
        
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            barbeiros = []
            for i in range(1, len(valores)):
                linha = valores[i]
                if linha and linha[0]:
                    status = linha[11] if len(linha) > 11 else "ATIVO"
                    if status.upper() == "ATIVO":
                        barbeiros.append(linha[0])
            
            self._cache_barbeiros = barbeiros
            self._cache_barbeiros_time = time.time()
            return barbeiros
        except:
            return []
    
    def _get_agendamentos_dia(self, data_iso):
        """Busca agendamentos do dia com cache"""
        cache_key = f"agendamentos_{data_iso}"
        if cache_key in self._cache_agendamentos_time:
            if time.time() - self._cache_agendamentos_time[cache_key] < self._cache_ttl:
                print(f"📦 Usando cache de agendamentos para {data_iso}")
                return self._cache_agendamentos.get(cache_key, [])
        
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['agenda'])
            agendamentos = []
            if len(valores) <= 1:
                return agendamentos
            
            partes = data_iso.split('-')
            data_busca = f"{partes[2]}/{partes[1]}/{partes[0]}"
            
            for i in range(1, len(valores)):
                linha = valores[i]
                if len(linha) < 4:
                    continue
                
                if linha[0] == data_busca:
                    agendamentos.append({
                        'data': linha[0],
                        'hora': linha[1] if len(linha) > 1 else "",
                        'cliente': linha[2] if len(linha) > 2 else "",
                        'barbeiro': linha[3] if len(linha) > 3 else "",
                        'servico': linha[4] if len(linha) > 4 else "",
                        'status': linha[5] if len(linha) > 5 else "Avulso"
                    })
            
            self._cache_agendamentos[cache_key] = agendamentos
            self._cache_agendamentos_time[cache_key] = time.time()
            return agendamentos
        except:
            return []
    
    def salvar_agendamento(self, dados):
        """Salva um novo agendamento e limpa cache do dia"""
        try:
            plano = self._get_plano_cliente(dados.get('cliente', ''))
            partes = dados['data'].split('-')
            data_objeto = f"{partes[2]}/{partes[1]}/{partes[0]}"
            
            self.sheets.append_row(
                Config.SHEETS['agenda'],
                [
                    data_objeto,
                    dados['horario'],
                    dados['cliente'],
                    dados['barbeiro'],
                    dados['servico'],
                    "Interno" if dados.get('isAdm') else "Cliente Web",
                    plano
                ]
            )
            
            # Limpa cache do dia
            cache_key = f"agendamentos_{dados['data']}"
            self._cache_agendamentos.pop(cache_key, None)
            self._cache_agendamentos_time.pop(cache_key, None)
            
            link_zap = None
            if not dados.get('isAdm'):
                msg = f"✂️ *AGENDAMENTO CONFIRMADO!*%0A%0A👤 *Cliente:* {dados['cliente']}%0A📅 *Data:* {dados['data']}%0A⏰ *Hora:* {dados['horario']}%0A💈 *Barbeiro:* {dados['barbeiro']}%0A✂️ *Serviço:* {dados['servico']}"
                link_zap = f"https://api.whatsapp.com/send?phone=5541996324841&text={msg}"
            
            return {'sucesso': True, 'linkWhatsapp': link_zap}
        except Exception as e:
            return {'sucesso': False, 'msg': str(e)}
    
    # Mantenha os outros métodos (cancelar_agendamento, listar_agenda, etc.)
    # ...