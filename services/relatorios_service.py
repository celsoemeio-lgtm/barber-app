from config import Config
from datetime import datetime

class RelatoriosService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def get_dados_relatorio_diario(self, data_filtro, barbeiro_logado):
        """Relatório diário do barbeiro"""
        try:
            # Busca dados do barbeiro
            valores_b = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            percentual_comissao = 0
            meta_diaria = 0
            url_foto = ""
            
            for i in range(1, len(valores_b)):
                if valores_b[i][0].upper() == barbeiro_logado.upper():
                    try:
                        percentual_comissao = float(valores_b[i][2]) if len(valores_b[i]) > 2 else 0
                    except:
                        percentual_comissao = 0
                    try:
                        meta_diaria = float(valores_b[i][5]) if len(valores_b[i]) > 5 else 0
                    except:
                        meta_diaria = 0
                    url_foto = valores_b[i][10] if len(valores_b[i]) > 10 else ""
                    break
            
            # Busca vendas
            valores_v = self.sheets.get_all_values(Config.SHEETS['vendas'])
            data_busca = data_filtro.split('-')[::-1] if data_filtro else datetime.now().strftime("%d/%m/%Y")
            if isinstance(data_busca, list):
                data_busca = f"{data_busca[0]}/{data_busca[1]}/{data_busca[2]}"
            
            r = {
                'data': data_busca,
                'usuario': barbeiro_logado,
                'foto': url_foto,
                'totalBruto': 0,
                'totalDescontos': 0,
                'faturamentoLiquido': 0,
                'comissaoValor': 0,
                'atendimentosTotal': 0,
                'atendimentosVip': 0,
                'atendimentosAvulsos': 0,
                'ocupacao': 0,
                'metaAtingida': 0,
                'listaDetalhada': []
            }
            
            atendimentos_unicos = set()
            tempo_ocupado = 0
            
            for i in range(1, len(valores_v)):
                if len(valores_v[i]) < 5:
                    continue
                
                if valores_v[i][0] == data_busca and valores_v[i][4].upper() == barbeiro_logado.upper():
                    chave = f"{valores_v[i][0]}|{valores_v[i][1]}|{valores_v[i][2]}"
                    
                    if chave not in atendimentos_unicos:
                        if len(valores_v[i]) > 6 and valores_v[i][6].upper().find("VIP") >= 0:
                            r['atendimentosVip'] += 1
                        else:
                            r['atendimentosAvulsos'] += 1
                        atendimentos_unicos.add(chave)
                        tempo_ocupado += 40
                        
                        if len(valores_v[i]) > 8:
                            desc = valores_v[i][8].replace('R$', '').replace('.', '').replace(',', '.').strip()
                            try:
                                r['totalDescontos'] += float(desc)
                            except:
                                pass
                    
                    valor = valores_v[i][5].replace('R$', '').replace('.', '').replace(',', '.').strip()
                    try:
                        valor_float = float(valor)
                        r['totalBruto'] += valor_float
                        
                        r['listaDetalhada'].append({
                            'cliente': valores_v[i][2],
                            'servico': valores_v[i][3],
                            'valor': valor_float,
                            'tipo': valores_v[i][6] if len(valores_v[i]) > 6 else "AVULSO",
                            'servicoOriginal': valores_v[i][3]
                        })
                    except:
                        pass
            
            r['faturamentoLiquido'] = r['totalBruto'] - r['totalDescontos']
            r['atendimentosTotal'] = r['atendimentosVip'] + r['atendimentosAvulsos']
            r['comissaoValor'] = (r['faturamentoLiquido'] * percentual_comissao) / 100 if percentual_comissao > 0 else 0
            r['ocupacao'] = min(round((tempo_ocupado / 480) * 100), 100) if tempo_ocupado > 0 else 0
            
            if meta_diaria > 0:
                r['metaAtingida'] = min(round((r['comissaoValor'] / meta_diaria) * 100), 100)
            
            return r
        except Exception as e:
            return {'erro': str(e)}
    
    def obter_fechamento_unificado(self, barbeiro, data_i, data_f, valor_assinatura, perc_casa):
        """Relatório de fechamento para ADMIN"""
        try:
            nome_busca = barbeiro.lower().strip()
            d_ini = datetime.strptime(data_i, "%Y-%m-%d")
            d_fim = datetime.strptime(data_f, "%Y-%m-%d")
            
            # Dados do barbeiro
            valores_b = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            meta_diaria = 0
            dia_folga = ""
            comissao_base = 0
            url_foto = ""
            
            dias_semana = {"Domingo":0, "Segunda":1, "Terça":2, "Quarta":3, "Quinta":4, "Sexta":5, "Sábado":6}
            
            for i in range(1, len(valores_b)):
                if valores_b[i][0].lower().strip() == nome_busca:
                    try:
                        comissao_base = float(valores_b[i][2]) if len(valores_b[i]) > 2 else 0
                    except:
                        comissao_base = 0
                    try:
                        meta_diaria = float(valores_b[i][5]) if len(valores_b[i]) > 5 else 0
                    except:
                        meta_diaria = 0
                    dia_folga = valores_b[i][8] if len(valores_b[i]) > 8 else ""
                    url_foto = valores_b[i][10] if len(valores_b[i]) > 10 else ""
                    break
            
            # Dias trabalhados
            dias_trab = 0
            temp = d_ini
            indice_folga = dias_semana.get(dia_folga, -1)
            
            while temp <= d_fim:
                if temp.weekday() != indice_folga:
                    dias_trab += 1
                temp = temp.replace(day=temp.day + 1)
            
            meta_periodo = dias_trab * meta_diaria
            
            # Clientes VIP
            valores_c = self.sheets.get_all_values(Config.SHEETS['clientes'])
            total_vips = 0
            for i in range(1, len(valores_c)):
                if len(valores_c[i]) > 2 and valores_c[i][2] == "VIP":
                    total_vips += 1
            
            fat_vip_total = total_vips * float(valor_assinatura)
            sobra_rateio = fat_vip_total * ((100 - float(perc_casa)) / 100)
            
            # Vendas
            valores_v = self.sheets.get_all_values(Config.SHEETS['vendas'])
            total_cortes_vip = 0
            
            for i in range(1, len(valores_v)):
                if len(valores_v[i]) < 7:
                    continue
                if valores_v[i][6].upper().find("VIP") >= 0 and valores_v[i][3].upper().find("CORTE") >= 0:
                    try:
                        data_parts = valores_v[i][0].split('/')
                        d_venda = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
                        if d_ini <= d_venda <= d_fim:
                            total_cortes_vip += 1
                    except:
                        pass
            
            valor_por_corte = sobra_rateio / total_cortes_vip if total_cortes_vip > 0 else 0
            
            # Processa ganhos
            fat_bruto = 0
            comissao_total = 0
            bonus_vip = 0
            cortes_vip_count = 0
            servicos_lista = []
            
            for i in range(1, len(valores_v)):
                if len(valores_v[i]) < 7:
                    continue
                
                if valores_v[i][4].lower().strip() == nome_busca:
                    try:
                        data_parts = valores_v[i][0].split('/')
                        d_venda = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
                        
                        if d_ini <= d_venda <= d_fim:
                            valor_bruto = 0
                            try:
                                valor_bruto = float(valores_v[i][5].replace('R$', '').replace('.', '').replace(',', '.').strip())
                            except:
                                pass
                            
                            is_vip = valores_v[i][6].upper().find("VIP") >= 0
                            is_corte = valores_v[i][3].upper().find("CORTE") >= 0
                            
                            ganho = 0
                            
                            if is_vip and is_corte:
                                ganho = valor_por_corte
                                bonus_vip += ganho
                                cortes_vip_count += 1
                            else:
                                ganho = valor_bruto * (comissao_base / 100)
                                fat_bruto += valor_bruto
                            
                            comissao_total += ganho
                            
                            servicos_lista.append({
                                'data': valores_v[i][0],
                                'detalhe': valores_v[i][3],
                                'isVip': is_vip,
                                'valorBruto': valor_bruto,
                                'comissao': ganho
                            })
                    except:
                        pass
            
            perc_atingido = (comissao_total / meta_periodo * 100) if meta_periodo > 0 else 0
            
            return {
                'foto': url_foto,
                'totalVendas': fat_bruto,
                'valorUnitarioCesta': bonus_vip,
                'totalComissao': comissao_total,
                'qtdAtendimentosReais': len(servicos_lista),
                'qtdVips': cortes_vip_count,
                'percComissaoBase': comissao_base,
                'metaValor': meta_periodo,
                'metaPercent': perc_atingido,
                'servicos': servicos_lista
            }
        except Exception as e:
            return {'erro': str(e)}
    
    def get_relatorio_gerencial(self, data_ini, data_fim):
        """Relatório gerencial com rankings"""
        try:
            d_ini = datetime.strptime(data_ini, "%Y-%m-%d")
            d_fim = datetime.strptime(data_fim, "%Y-%m-%d")
            
            # Vendas
            valores_v = self.sheets.get_all_values(Config.SHEETS['vendas'])
            vendas_periodo = []
            
            for i in range(1, len(valores_v)):
                try:
                    data_parts = valores_v[i][0].split('/')
                    if len(data_parts) == 3:
                        d_venda = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
                        if d_ini <= d_venda <= d_fim:
                            vendas_periodo.append(valores_v[i])
                except:
                    pass
            
            # Dias com movimento
            dias_set = set()
            for v in vendas_periodo:
                if len(v) > 0:
                    dias_set.add(v[0])
            dias_movimento = len(dias_set) or 1
            
            # Barbeiros
            valores_b = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            cards = []
            total_atendimentos = 0
            
            for i in range(1, len(valores_b)):
                if len(valores_b[i]) == 0 or not valores_b[i][0]:
                    continue
                    
                nome = valores_b[i][0].strip()
                try:
                    meta_diaria = float(valores_b[i][5]) if len(valores_b[i]) > 5 and valores_b[i][5] else 0
                except:
                    meta_diaria = 0
                
                vendas_b = []
                for v in vendas_periodo:
                    if len(v) > 4 and v[4].strip().lower() == nome.lower():
                        vendas_b.append(v)
                
                fat = 0
                for v in vendas_b:
                    try:
                        valor_str = v[7] if len(v) > 7 and v[7] else "0"
                        valor_limpo = str(valor_str).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
                        if valor_limpo:
                            fat += float(valor_limpo)
                    except:
                        pass
                
                atend = len(vendas_b)
                total_atendimentos += atend
                
                meta_total = meta_diaria * dias_movimento
                perc_meta = (fat / meta_total * 100) if meta_total > 0 else 0
                
                vips = 0
                for v in vendas_b:
                    if len(v) > 3 and len(v) > 6:
                        if v[3].upper().find("CORTE") >= 0 and v[6].upper().find("VIP") >= 0:
                            vips += 1
                
                cards.append({
                    'nome': nome,
                    'foto': valores_b[i][10] if len(valores_b[i]) > 10 else "",
                    'ocupacao': round(((atend * 40) / (dias_movimento * 540)) * 100, 1) if dias_movimento > 0 else 0,
                    'vips': vips,
                    'atendimentos': atend,
                    'faturamento': round(fat, 2),
                    'ticket': round(fat / atend, 2) if atend > 0 else 0,
                    'metaAtingida': fat >= meta_total and fat > 0,
                    'percentualMeta': min(100, round(perc_meta))
                })
            
            # Clientes novos
            valores_c = self.sheets.get_all_values(Config.SHEETS['clientes'])
            novos = 0
            novos_vips = 0
            
            for i in range(1, len(valores_c)):
                try:
                    if len(valores_c[i]) > 3 and valores_c[i][3]:
                        data_parts = valores_c[i][3].split('/')
                        if len(data_parts) == 3:
                            d_cad = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
                            if d_ini <= d_cad <= d_fim:
                                novos += 1
                                if len(valores_c[i]) > 2 and valores_c[i][2] == "VIP":
                                    novos_vips += 1
                except:
                    pass
            
            fat_total = 0
            for v in vendas_periodo:
                try:
                    valor_str = v[7] if len(v) > 7 and v[7] else "0"
                    valor_limpo = str(valor_str).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
                    if valor_limpo:
                        fat_total += float(valor_limpo)
                except:
                    pass
            
            cortes_ass = 0
            cortes_avulsos = 0
            for v in vendas_periodo:
                if len(v) > 3 and v[3].upper().find("CORTE") >= 0:
                    if len(v) > 6 and v[6].upper().find("VIP") >= 0:
                        cortes_ass += 1
                    else:
                        cortes_avulsos += 1
            
            return {
                'geral': {
                    'fatBruto': round(fat_total, 2),
                    'clientesComuns': novos - novos_vips,
                    'assinaturas': novos_vips,
                    'cortesAss': cortes_ass,
                    'cortesAvulsos': cortes_avulsos,
                    'ticketMedio': round(fat_total / total_atendimentos, 2) if total_atendimentos > 0 else 0
                },
                'barbeiros': cards
            }
        except Exception as e:
            print(f"❌ Erro detalhado: {e}")
            return {'error': str(e)}