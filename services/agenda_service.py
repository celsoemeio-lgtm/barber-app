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
    
    def get_dados_painel_diario(self, data_escolhida):
        """Monta o grid do painel diário"""
        print(f"🔍 AgendaService.get_dados_painel_diario({data_escolhida})")
        try:
            horarios_grid = [
                "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                "13:30", "14:00", "14:30", "15:00", "15:30", "16:00",
                "16:30", "17:00", "17:30", "18:00", "18:30"
            ]
            
            print("📌 Buscando barbeiros...")
            barbeiros = self._get_barbeiros_ativos()
            print(f"✅ Barbeiros encontrados: {len(barbeiros)}")
            
            print("📌 Buscando agendamentos...")
            agendamentos = self._get_agendamentos_dia(data_escolhida)
            print(f"✅ Agendamentos encontrados: {len(agendamentos)}")
            
            partes = data_escolhida.split('-')
            data_busca = f"{partes[2]}/{partes[1]}/{partes[0]}"
            print(f"📅 Data busca: {data_busca}")
            
            agora = datetime.now()
            hoje_num = int(agora.strftime("%Y%m%d"))
            data_mapa_num = int(data_escolhida.replace('-', ''))
            hora_agora_num = int(agora.strftime("%H%M"))
            
            grade = []
            for hora_grid in horarios_grid:
                linha = [hora_grid]
                hora_grid_num = int(hora_grid.replace(':', ''))
                
                eh_passado = (data_mapa_num < hoje_num) or \
                             (data_mapa_num == hoje_num and hora_grid_num < hora_agora_num)
                
                for barbeiro in barbeiros:
                    agendado = None
                    for a in agendamentos:
                        if (a['data'] == data_busca and 
                            a['hora'][:5] == hora_grid and 
                            a['barbeiro'].upper().strip() == barbeiro.upper().strip()):
                            agendado = a
                            break
                    
                    if agendado:
                        linha.append(f"🔴 {agendado['cliente'].upper()} | {agendado.get('status', 'Avulso')} | {agendado.get('servico', '---')}")
                    elif eh_passado:
                        linha.append("🚫 ENCERRADO")
                    else:
                        linha.append("🟢 LIVRE")
                
                grade.append(linha)
            
            print(f"✅ Grade montada com {len(grade)} horários")
            return {
                'barbeiros': barbeiros,
                'grade': grade,
                'dataIso': data_escolhida,
                'success': True
            }
        except Exception as e:
            print(f"❌ Erro em get_dados_painel_diario: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e), 'success': False}
    
    def _get_barbeiros_ativos(self):
        """Busca barbeiros ativos com cache"""
        if self._cache_barbeiros_time:
            if time.time() - self._cache_barbeiros_time < 300:  # 5 minutos
                print("📦 Usando cache de barbeiros ativos")
                return self._cache_barbeiros
        
        try:
            print("📊 Lendo barbeiros da planilha...")
            valores = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            print(f"📊 Total de barbeiros na planilha: {len(valores)-1}")
            
            barbeiros = []
            for i in range(1, len(valores)):
                linha = valores[i]
                if linha and linha[0]:
                    status = linha[11] if len(linha) > 11 else "ATIVO"
                    if status.upper() == "ATIVO":
                        barbeiros.append(linha[0])
                        print(f"   ✅ Barbeiro ativo: {linha[0]}")
            
            self._cache_barbeiros = barbeiros
            self._cache_barbeiros_time = time.time()
            return barbeiros
        except Exception as e:
            print(f"❌ Erro ao buscar barbeiros: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_agendamentos_dia(self, data_iso):
        """Busca agendamentos do dia com cache"""
        cache_key = f"agendamentos_{data_iso}"
        if cache_key in self._cache_agendamentos_time:
            if time.time() - self._cache_agendamentos_time[cache_key] < self._cache_ttl:
                print(f"📦 Usando cache de agendamentos para {data_iso}")
                return self._cache_agendamentos.get(cache_key, [])
        
        try:
            print(f"📊 Lendo agendamentos para {data_iso}...")
            valores = self.sheets.get_all_values(Config.SHEETS['agenda'])
            agendamentos = []
            if len(valores) <= 1:
                return agendamentos
            
            partes = data_iso.split('-')
            data_busca = f"{partes[2]}/{partes[1]}/{partes[0]}"
            print(f"📅 Data busca: {data_busca}")
            
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
                    print(f"   ✅ Agendamento: {linha[2]} às {linha[1]} com {linha[3]}")
            
            self._cache_agendamentos[cache_key] = agendamentos
            self._cache_agendamentos_time[cache_key] = time.time()
            print(f"✅ Total de agendamentos: {len(agendamentos)}")
            return agendamentos
        except Exception as e:
            print(f"❌ Erro ao buscar agendamentos: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_plano_cliente(self, nome_cliente):
        """Busca o plano do cliente pelo nome"""
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['clientes'])
            for i in range(1, len(valores)):
                linha = valores[i]
                if linha and linha[0].strip().upper() == nome_cliente.strip().upper():
                    return linha[2] if len(linha) > 2 else "Avulso"
            return "Avulso"
        except:
            return "Avulso"
    
    def salvar_agendamento(self, dados):
        """Salva um novo agendamento"""
        try:
            print(f"📝 Salvando agendamento: {dados}")
            
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
            
            print("✅ Agendamento salvo com sucesso!")
            return {'sucesso': True, 'linkWhatsapp': link_zap}
        except Exception as e:
            print(f"❌ Erro ao salvar agendamento: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'msg': str(e)}
    
    def cancelar_agendamento(self, dados):
        """Cancela um agendamento existente"""
        try:
            print(f"📝 Cancelando agendamento: {dados}")
            valores = self.sheets.get_all_values(Config.SHEETS['agenda'])
            
            partes = dados['data'].split('-')
            data_alvo = f"{partes[2]}/{partes[1]}/{partes[0]}"
            hora_alvo = dados['hora'].strip()[:5]
            cliente_alvo = dados['cliente'].strip().upper()
            barbeiro_alvo = dados['barbeiro'].strip().upper()
            
            for i in range(len(valores) - 1, 0, -1):
                linha = valores[i]
                if len(linha) < 4:
                    continue
                
                data_plan = linha[0]
                hora_plan = linha[1][:5] if len(linha) > 1 else ""
                cliente_plan = linha[2].strip().upper() if len(linha) > 2 else ""
                barbeiro_plan = linha[3].strip().upper() if len(linha) > 3 else ""
                
                if (data_plan == data_alvo and 
                    hora_plan == hora_alvo and 
                    cliente_plan == cliente_alvo and 
                    barbeiro_plan == barbeiro_alvo):
                    
                    self.sheets.delete_row(Config.SHEETS['agenda'], i + 1)
                    print("✅ Agendamento cancelado!")
                    return {'sucesso': True}
            
            return {'sucesso': False, 'msg': "Agendamento não encontrado"}
        except Exception as e:
            print(f"❌ Erro ao cancelar agendamento: {e}")
            return {'sucesso': False, 'msg': str(e)}
    
    def listar_agenda(self):
        """Lista todos os agendamentos"""
        try:
            print("📋 Listando todos os agendamentos...")
            valores = self.sheets.get_all_values(Config.SHEETS['agenda'])
            
            if len(valores) <= 1:
                return {'sucesso': True, 'lista': []}
            
            lista = []
            for i in range(1, len(valores)):
                linha = valores[i]
                if len(linha) >= 4:
                    lista.append({
                        'data': linha[0],
                        'hora': linha[1][:5] if len(linha) > 1 else "",
                        'cliente': linha[2] if len(linha) > 2 else "",
                        'barbeiro': linha[3] if len(linha) > 3 else "",
                        'servico': linha[4] if len(linha) > 4 else ""
                    })
            
            print(f"✅ Total de agendamentos: {len(lista)}")
            return {'sucesso': True, 'lista': lista}
        except Exception as e:
            print(f"❌ Erro ao listar agenda: {e}")
            return {'sucesso': False, 'msg': str(e)}
    
    def excluir_linha_agenda(self, dados):
        """Exclui uma linha específica da agenda"""
        try:
            print(f"📝 Excluindo linha da agenda: {dados}")
            valores = self.sheets.get_all_values(Config.SHEETS['agenda'])
            
            for i in range(len(valores) - 1, 0, -1):
                linha = valores[i]
                if len(linha) < 3:
                    continue
                
                data_plan = linha[0]
                hora_plan = linha[1][:5] if len(linha) > 1 else ""
                cliente_plan = linha[2].strip().upper() if len(linha) > 2 else ""
                
                if (data_plan == dados['data'] and 
                    hora_plan == dados['hora'] and 
                    cliente_plan == dados['cliente'].strip().upper()):
                    
                    self.sheets.delete_row(Config.SHEETS['agenda'], i + 1)
                    print("✅ Linha excluída com sucesso!")
                    return {'sucesso': True}
            
            return {'sucesso': False, 'msg': "Registro não encontrado"}
        except Exception as e:
            print(f"❌ Erro ao excluir linha: {e}")
            return {'sucesso': False, 'msg': str(e)}
    
    def preparar_agendamento(self, dados):
        """Guarda dados temporários para o formulário"""
        return dados