from config import Config
from datetime import datetime

class AgendaService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def get_dados_painel_diario(self, data_escolhida):
        """Monta o grid do painel diário"""
        try:
            horarios_grid = [
                "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                "13:30", "14:00", "14:30", "15:00", "15:30", "16:00",
                "16:30", "17:00", "17:30", "18:00", "18:30"
            ]
            
            barbeiros = self._get_barbeiros_ativos()
            agendamentos = self._get_agendamentos_dia(data_escolhida)
            
            partes = data_escolhida.split('-')
            data_busca = f"{partes[2]}/{partes[1]}/{partes[0]}"
            
            hoje = datetime.now()
            hoje_num = int(hoje.strftime("%Y%m%d"))
            data_mapa_num = int(data_escolhida.replace('-', ''))
            hora_agora_num = int(hoje.strftime("%H%M"))
            
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
            
            return {
                'barbeiros': barbeiros,
                'grade': grade,
                'dataIso': data_escolhida,
                'success': True
            }
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    def _get_barbeiros_ativos(self):
        try:
            valores = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            barbeiros = []
            for i in range(1, len(valores)):
                linha = valores[i]
                if linha and linha[0]:
                    status = linha[11] if len(linha) > 11 else "ATIVO"
                    if status.upper() == "ATIVO":
                        barbeiros.append(linha[0])
            return barbeiros
        except:
            return []
    
    def _get_agendamentos_dia(self, data_iso):
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
            return agendamentos
        except:
            return []
    
    def _get_plano_cliente(self, nome_cliente):
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
            
            link_zap = None
            if not dados.get('isAdm'):
                msg = f"✂️ *AGENDAMENTO CONFIRMADO!*%0A%0A👤 *Cliente:* {dados['cliente']}%0A📅 *Data:* {dados['data']}%0A⏰ *Hora:* {dados['horario']}%0A💈 *Barbeiro:* {dados['barbeiro']}%0A✂️ *Serviço:* {dados['servico']}"
                link_zap = f"https://api.whatsapp.com/send?phone=5541996324841&text={msg}"
            
            return {'sucesso': True, 'linkWhatsapp': link_zap}
        except Exception as e:
            return {'sucesso': False, 'msg': str(e)}
    
    def cancelar_agendamento(self, dados):
        try:
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
                    return {'sucesso': True}
            
            return {'sucesso': False, 'msg': "Agendamento não encontrado"}
        except Exception as e:
            return {'sucesso': False, 'msg': str(e)}
    
    def listar_agenda(self):
        try:
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
            
            return {'sucesso': True, 'lista': lista}
        except Exception as e:
            return {'sucesso': False, 'msg': str(e)}
    
    def excluir_linha_agenda(self, dados):
        try:
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
                    return {'sucesso': True}
            
            return {'sucesso': False, 'msg': "Registro não encontrado"}
        except Exception as e:
            return {'sucesso': False, 'msg': str(e)}
    
    def preparar_agendamento(self, dados):
        """Guarda dados temporários para o formulário"""
        return dados