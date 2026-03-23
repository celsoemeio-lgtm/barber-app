from config import Config
from datetime import datetime, timedelta
import re

class RelatoriosService:
    def __init__(self, sheets_service):
        self.sheets = sheets_service
    
    def get_dados_relatorio_diario(self, data_filtro, barbeiro_logado):
        """Relatório diário do barbeiro logado"""
        print(f"\n=== RELATÓRIO DIÁRIO ===")
        print(f"Data: {data_filtro}")
        print(f"Barbeiro: {barbeiro_logado}")
        
        try:
            # Converte a data para o formato dd/mm/yyyy
            partes = data_filtro.split('-')
            data_busca = f"{partes[2]}/{partes[1]}/{partes[0]}"
            print(f"Data busca: {data_busca}")
            
            # 1. Buscar dados do barbeiro na aba Cad_Barbeiros
            valores_b = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            percentual_comissao = 0
            meta_diaria = 0
            url_foto = ""
            
            for i in range(1, len(valores_b)):
                if len(valores_b[i]) > 0 and valores_b[i][0].upper() == barbeiro_logado.upper():
                    # Comissão (coluna C - índice 2)
                    try:
                        comissao_str = valores_b[i][2].replace('%', '').replace(',', '.')
                        percentual_comissao = float(comissao_str)
                        print(f"✅ Comissão: {percentual_comissao}%")
                    except:
                        percentual_comissao = 0
                        print(f"⚠️ Comissão não encontrada, usando 0%")
                    
                    # Meta diária (coluna F - índice 5) - CORRIGIDO
                    try:
                        meta_str = str(valores_b[i][5]).replace('R$', '').replace(' ', '').replace(',', '.').strip()
                        meta_num = re.sub(r'[^0-9.]', '', meta_str)
                        if meta_num.count('.') > 1:
                            partes_meta = meta_num.split('.')
                            meta_num = partes_meta[0] + '.' + partes_meta[1]
                        meta_diaria = float(meta_num)
                        print(f"✅ Meta diária: R$ {meta_diaria:.2f}")
                    except Exception as e:
                        meta_diaria = 0
                        print(f"⚠️ Erro ao ler meta: {e}, usando R$ 0")
                    
                    # Foto (coluna K - índice 10)
                    if len(valores_b[i]) > 10:
                        url_foto = valores_b[i][10]
                        print(f"✅ Foto encontrada")
                    break
            
            # 2. Buscar vendas na BASE_VENDAS
            valores_v = self.sheets.get_all_values(Config.SHEETS['vendas'])
            
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
            
            # Processar vendas do dia e barbeiro
            for i in range(1, len(valores_v)):
                if len(valores_v[i]) < 5:
                    continue
                
                # Verifica se é a data correta (coluna A) e barbeiro (coluna E)
                if valores_v[i][0] == data_busca and valores_v[i][4].upper() == barbeiro_logado.upper():
                    chave = f"{valores_v[i][0]}|{valores_v[i][1]}|{valores_v[i][2]}"
                    
                    # Contagem única por atendimento
                    if chave not in atendimentos_unicos:
                        # Verifica se é VIP (coluna G)
                        if len(valores_v[i]) > 6 and valores_v[i][6].upper() == "VIP":
                            r['atendimentosVip'] += 1
                        else:
                            r['atendimentosAvulsos'] += 1
                        atendimentos_unicos.add(chave)
                        tempo_ocupado += 45  # 45 min por atendimento
                        
                        # Desconto (coluna I)
                        if len(valores_v[i]) > 8 and valores_v[i][8]:
                            try:
                                desc_limpo = valores_v[i][8].replace('R$', '').replace('.', '').replace(',', '.').strip()
                                r['totalDescontos'] += float(desc_limpo) if desc_limpo else 0
                            except:
                                pass
                    
                    # Valor do serviço (coluna H - TOTAL DIA)
                    try:
                        valor_limpo = valores_v[i][7].replace('R$', '').replace('.', '').replace(',', '.').strip() if len(valores_v[i]) > 7 else "0"
                        valor_float = float(valor_limpo) if valor_limpo else 0
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
            
            # Cálculos finais
            r['faturamentoLiquido'] = r['totalBruto'] - r['totalDescontos']
            r['atendimentosTotal'] = r['atendimentosVip'] + r['atendimentosAvulsos']
            r['comissaoValor'] = (r['faturamentoLiquido'] * percentual_comissao) / 100 if percentual_comissao > 0 else 0
            r['ocupacao'] = min(round((tempo_ocupado / 480) * 100), 100) if tempo_ocupado > 0 else 0
            
            if meta_diaria > 0:
                r['metaAtingida'] = min(round((r['comissaoValor'] / meta_diaria) * 100), 100)
            
            print(f"\n=== RESULTADO RELATÓRIO DIÁRIO ===")
            print(f"Atendimentos: {r['atendimentosTotal']} (VIP: {r['atendimentosVip']}, Avulso: {r['atendimentosAvulsos']})")
            print(f"Faturamento Líquido: R$ {r['faturamentoLiquido']:.2f}")
            print(f"Comissão: R$ {r['comissaoValor']:.2f}")
            print(f"Ocupação: {r['ocupacao']}%")
            print(f"Meta Atingida: {r['metaAtingida']}%")
            print(f"=================================\n")
            
            return r
            
        except Exception as e:
            print(f"❌ Erro no relatório diário: {e}")
            import traceback
            traceback.print_exc()
            return {'erro': str(e)}
    
    def obter_fechamento_unificado(self, barbeiro, data_i, data_f, valor_assinatura, perc_casa):
        """Relatório de fechamento para ADMIN com rateio VIP corrigido"""
        print(f"\n=== FECHAMENTO ADMIN ===")
        print(f"Barbeiro: {barbeiro}")
        print(f"Período: {data_i} até {data_f}")
        print(f"Assinatura: R$ {valor_assinatura}")
        print(f"Barbearia: {perc_casa}%")
        
        try:
            nome_busca = barbeiro.lower().strip()
            d_ini = datetime.strptime(data_i, "%Y-%m-%d")
            d_fim = datetime.strptime(data_f, "%Y-%m-%d")
            print(f"Datas convertidas: {d_ini.strftime('%d/%m/%Y')} até {d_fim.strftime('%d/%m/%Y')}")
            
            # ========== 1. DADOS DO BARBEIRO ==========
            print("Buscando dados do barbeiro...")
            valores_b = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            print(f"Total de barbeiros na planilha: {len(valores_b)-1}")
            
            meta_diaria = 0
            comissao_base = 0
            url_foto = ""
            
            for i in range(1, len(valores_b)):
                if len(valores_b[i]) > 0 and valores_b[i][0].lower().strip() == nome_busca:
                    print(f"✅ Barbeiro encontrado: {valores_b[i][0]}")
                    
                    # Comissão (coluna C)
                    try:
                        comissao_str = valores_b[i][2].replace('%', '')
                        comissao_base = float(comissao_str)
                        print(f"   Comissão: {comissao_base}%")
                    except:
                        comissao_base = 0
                        print(f"   Comissão: não encontrada, usando 0%")
                    
                    # Meta diária (coluna F) - CORRIGIDO
                    try:
                        meta_str = str(valores_b[i][5]).replace('R$', '').replace(' ', '').replace(',', '.').strip()
                        meta_num = re.sub(r'[^0-9.]', '', meta_str)
                        if meta_num.count('.') > 1:
                            partes_meta = meta_num.split('.')
                            meta_num = partes_meta[0] + '.' + partes_meta[1]
                        meta_diaria = float(meta_num)
                        print(f"   Meta diária: R$ {meta_diaria:.2f}")
                    except Exception as e:
                        meta_diaria = 0
                        print(f"   ⚠️ Erro ao ler meta: {e}, usando R$ 0")
                    
                    # Foto (coluna K)
                    if len(valores_b[i]) > 10:
                        url_foto = valores_b[i][10]
                        print(f"   Foto: {url_foto[:50]}...")
                    break
            
            # ========== 2. CALCULAR DIAS TRABALHADOS ==========
            print("Calculando dias no período...")
            dias_trab = 0
            temp = d_ini
            while temp <= d_fim:
                dias_trab += 1
                temp = temp + timedelta(days=1)
            
            print(f"   Dias no período: {dias_trab}")
            meta_periodo = dias_trab * meta_diaria
            print(f"   Meta do período: R$ {meta_periodo:.2f}")
            
            # ========== 3. CONTAR CLIENTES VIP ATIVOS NO PERÍODO ==========
            print("Contando clientes VIP ativos...")
            valores_c = self.sheets.get_all_values(Config.SHEETS['clientes'])
            total_vips_ativos = 0
            
            for i in range(1, len(valores_c)):
                if len(valores_c[i]) > 2 and valores_c[i][2] == "VIP":
                    # Verifica se o cliente foi cadastrado no período
                    try:
                        if len(valores_c[i]) > 3 and valores_c[i][3]:
                            data_parts = valores_c[i][3].split('/')
                            if len(data_parts) == 3:
                                d_cad = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
                                if d_ini <= d_cad <= d_fim:
                                    total_vips_ativos += 1
                        else:
                            total_vips_ativos += 1
                    except:
                        total_vips_ativos += 1
            
            print(f"✅ Clientes VIP ativos no período: {total_vips_ativos}")
            
            # ========== 4. CALCULAR VALOR TOTAL DO RATEIO VIP ==========
            faturamento_vip_total = total_vips_ativos * float(valor_assinatura)
            sobra_rateio = faturamento_vip_total * ((100 - float(perc_casa)) / 100)
            print(f"💰 Faturamento VIP total: R$ {faturamento_vip_total:.2f}")
            print(f"💰 Valor para rateio (após {perc_casa}% barbearia): R$ {sobra_rateio:.2f}")
            
            # ========== 5. BUSCAR VENDAS ==========
            print("Buscando vendas...")
            valores_v = self.sheets.get_all_values(Config.SHEETS['vendas'])
            print(f"   Total de vendas na planilha: {len(valores_v)-1}")
            
            # ========== 6. CONTAR CORTES VIP POR BARBEIRO ==========
            print("Contando cortes VIP no período...")
            cortes_vip_por_barbeiro = {}
            total_cortes_vip_geral = 0
            
            for i in range(1, len(valores_v)):
                if len(valores_v[i]) < 8:
                    continue
                
                prof = valores_v[i][4].lower().strip() if len(valores_v[i]) > 4 else ""
                servico = valores_v[i][3].upper() if len(valores_v[i]) > 3 else ""
                is_vip = len(valores_v[i]) > 6 and valores_v[i][6].upper() == "VIP"
                
                # Verifica se é CORTE e VIP
                if is_vip and servico.find("CORTE") >= 0:
                    # Verifica data
                    try:
                        data_parts = valores_v[i][0].split('/')
                        if len(data_parts) == 3:
                            d_venda = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
                            if d_ini <= d_venda <= d_fim:
                                total_cortes_vip_geral += 1
                                if prof not in cortes_vip_por_barbeiro:
                                    cortes_vip_por_barbeiro[prof] = 0
                                cortes_vip_por_barbeiro[prof] += 1
                    except:
                        pass
            
            print(f"✂️ Total de cortes VIP no período: {total_cortes_vip_geral}")
            for prof, qtd in cortes_vip_por_barbeiro.items():
                print(f"   {prof}: {qtd} cortes VIP")
            
            # ========== 7. VALOR POR CORTE VIP ==========
            valor_por_corte_vip = sobra_rateio / total_cortes_vip_geral if total_cortes_vip_geral > 0 else 0
            print(f"💰 Valor por corte VIP: R$ {valor_por_corte_vip:.2f}")
            
            # ========== 8. PROCESSAR VENDAS DO BARBEIRO ==========
            fat_bruto = 0
            comissao_total = 0
            bonus_vip_total = 0
            servicos_lista = []
            cortes_vip_contador = 0
            atendimentos_unicos = set()
            
            print("Processando vendas do barbeiro...")
            for i in range(1, len(valores_v)):
                if len(valores_v[i]) < 8:
                    continue
                
                if len(valores_v[i]) > 4 and valores_v[i][4].lower().strip() == nome_busca:
                    try:
                        data_parts = valores_v[i][0].split('/')
                        if len(data_parts) == 3:
                            d_venda = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
                            
                            if d_ini <= d_venda <= d_fim:
                                # Valor da coluna H (TOTAL DIA) - valor efetivamente pago
                                valor_str = valores_v[i][7] if len(valores_v[i]) > 7 else "0"
                                valor_limpo = str(valor_str).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
                                valor_bruto = float(valor_limpo) if valor_limpo else 0
                                
                                # Valor da coluna F (V. UNIT) - valor de tabela do serviço
                                valor_unitario_str = valores_v[i][5] if len(valores_v[i]) > 5 else "0"
                                valor_unitario_limpo = str(valor_unitario_str).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
                                valor_unitario = float(valor_unitario_limpo) if valor_unitario_limpo else 0
                                
                                is_vip = len(valores_v[i]) > 6 and valores_v[i][6].upper() == "VIP"
                                servico_nome = valores_v[i][3].upper() if len(valores_v[i]) > 3 else ""
                                is_corte = servico_nome.find("CORTE") >= 0
                                
                                # Chave única para este atendimento (data|hora|cliente)
                                chave = f"{valores_v[i][0]}|{valores_v[i][1]}|{valores_v[i][2]}"
                                
                                # SEMPRE adiciona o serviço à lista (para exibição)
                                servicos_lista.append({
                                    'data': valores_v[i][0],
                                    'cliente': valores_v[i][2],
                                    'detalhe': valores_v[i][3],
                                    'isVip': is_vip,
                                    'valor': valor_bruto,
                                    'valorServico': valor_unitario,
                                    'comissao': 0
                                })
                                
                                # Cálculo de comissão (apenas uma vez por atendimento)
                                if chave not in atendimentos_unicos:
                                    atendimentos_unicos.add(chave)
                                    
                                    if is_vip and is_corte:
                                        # CORTE VIP: recebe do rateio
                                        ganho = valor_por_corte_vip
                                        bonus_vip_total += ganho
                                        cortes_vip_contador += 1
                                        # Atualiza a comissão para este serviço
                                        for item in servicos_lista:
                                            if item['data'] == valores_v[i][0] and item['cliente'] == valores_v[i][2] and item['detalhe'] == valores_v[i][3]:
                                                item['comissao'] = ganho
                                                break
                                    else:
                                        # Serviços avulsos ou VIP não-CORTE: comissão normal
                                        ganho = valor_bruto * (comissao_base / 100)
                                        fat_bruto += valor_bruto
                                        # Atualiza a comissão para este serviço
                                        for item in servicos_lista:
                                            if item['data'] == valores_v[i][0] and item['cliente'] == valores_v[i][2] and item['detalhe'] == valores_v[i][3]:
                                                item['comissao'] = ganho
                                                break
                    except Exception as e:
                        print(f"   Erro na venda linha {i}: {e}")
                        continue
            
            # Calcula a comissão total
            comissao_total = fat_bruto * (comissao_base / 100) if comissao_base > 0 else 0
            comissao_total += bonus_vip_total
            
            print(f"   Cortes VIP do barbeiro: {cortes_vip_contador}")
            
            # ========== 9. CALCULAR OCUPAÇÃO ==========
            # Usa atendimentos únicos para ocupação
            tempo_total = len(atendimentos_unicos) * 45
            tempo_disponivel = dias_trab * 480
            ocupacao = (tempo_total / tempo_disponivel * 100) if tempo_disponivel > 0 else 0
            
            # ========== 10. CALCULAR PERCENTUAL DA META ==========
            perc_atingido = (comissao_total / meta_periodo * 100) if meta_periodo > 0 else 0
            
            print(f"\n=== RESULTADO DO FECHAMENTO ===")
            print(f"Faturamento Avulso: R$ {fat_bruto:.2f}")
            print(f"Bônus VIP (cortes): R$ {bonus_vip_total:.2f}")
            print(f"Total Comissão: R$ {comissao_total:.2f}")
            print(f"Cortes VIP do barbeiro: {cortes_vip_contador}")
            print(f"Atendimentos únicos: {len(atendimentos_unicos)}")
            print(f"Total serviços: {len(servicos_lista)}")
            print(f"Ocupação: {ocupacao:.1f}%")
            print(f"Meta Atingida: {perc_atingido:.1f}%")
            print(f"===============================\n")
            
            return {
                'foto': url_foto,
                'totalVendas': fat_bruto,
                'valorUnitarioCesta': bonus_vip_total,
                'totalComissao': comissao_total,
                'qtdAtendimentosReais': len(atendimentos_unicos),
                'qtdVips': cortes_vip_contador,
                'percComissaoBase': comissao_base,
                'metaValor': meta_periodo,
                'metaPercent': perc_atingido,
                'taxaOcupacao': ocupacao,
                'servicos': servicos_lista
            }
            
        except Exception as e:
            print(f"❌ Erro no fechamento: {e}")
            import traceback
            traceback.print_exc()
            return {'erro': str(e)}
    
    def get_relatorio_gerencial(self, data_ini, data_fim):
        """Relatório gerencial com rankings e detalhamento por dia"""
        print(f"\n=== RELATÓRIO GERENCIAL ===")
        print(f"Período: {data_ini} até {data_fim}")
        
        try:
            d_ini = datetime.strptime(data_ini, "%Y-%m-%d")
            d_fim = datetime.strptime(data_fim, "%Y-%m-%d")
            
            # Buscar vendas
            valores_v = self.sheets.get_all_values(Config.SHEETS['vendas'])
            vendas_periodo = []
            
            for i in range(1, len(valores_v)):
                try:
                    if len(valores_v[i]) > 7 and valores_v[i][0]:
                        data_parts = valores_v[i][0].split('/')
                        if len(data_parts) == 3:
                            d_venda = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
                            if d_ini <= d_venda <= d_fim:
                                vendas_periodo.append(valores_v[i])
                except:
                    pass
            
            print(f"Vendas no período: {len(vendas_periodo)}")
            
            # ========== DETALHAMENTO POR DIA ==========
            dias_dict = {}
            
            for v in vendas_periodo:
                try:
                    data_str = v[0]
                    partes = data_str.split('/')
                    data_iso = f"{partes[2]}-{partes[1]}-{partes[0]}"
                    
                    # Valor da venda (coluna H - TOTAL DIA)
                    valor_str = v[7] if len(v) > 7 else "0"
                    valor_limpo = str(valor_str).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
                    valor = float(valor_limpo) if valor_limpo else 0
                    
                    if valor > 0:
                        if data_iso not in dias_dict:
                            dias_dict[data_iso] = {
                                'data': data_iso,
                                'faturamento': 0,
                                'atendimentos': 0,
                                'ocupacao': 0,
                                'ticketMedio': 0
                            }
                        
                        dias_dict[data_iso]['faturamento'] += valor
                        dias_dict[data_iso]['atendimentos'] += 1
                except:
                    pass
            
            for dia in dias_dict.values():
                tempo_total = dia['atendimentos'] * 45
                dia['ocupacao'] = round(min((tempo_total / 480) * 100, 100))
                if dia['atendimentos'] > 0:
                    dia['ticketMedio'] = round(dia['faturamento'] / dia['atendimentos'], 2)
            
            dias_lista = sorted(dias_dict.values(), key=lambda x: x['data'])
            print(f"Dias com movimento: {len(dias_lista)}")
            
            # Dias com movimento (para meta)
            dias_set = set()
            for v in vendas_periodo:
                if len(v) > 0:
                    dias_set.add(v[0])
            dias_movimento = len(dias_set) or 1
            print(f"Dias com movimento: {dias_movimento}")
            
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
                atend = 0
                for v in vendas_b:
                    try:
                        if len(v) > 7 and v[7]:
                            valor_str = v[7]
                            valor_limpo = str(valor_str).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
                            valor = float(valor_limpo) if valor_limpo else 0
                            if valor > 0:
                                fat += valor
                                atend += 1
                    except:
                        pass
                
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
                    if len(v) > 7 and v[7]:
                        valor_str = v[7]
                        valor_limpo = str(valor_str).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
                        valor = float(valor_limpo) if valor_limpo else 0
                        if valor > 0:
                            fat_total += valor
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
            
            print(f"\n=== RESULTADO GERENCIAL ===")
            print(f"Faturamento Total: R$ {fat_total:.2f}")
            print(f"Total Atendimentos: {total_atendimentos}")
            print(f"Novos Clientes: {novos}")
            print(f"Cortes VIP: {cortes_ass}")
            print(f"Cortes Avulsos: {cortes_avulsos}")
            print(f"Barbeiros processados: {len(cards)}")
            print(f"Dias detalhados: {len(dias_lista)}")
            print(f"==========================\n")
            
            return {
                'geral': {
                    'fatBruto': round(fat_total, 2),
                    'clientesComuns': novos - novos_vips,
                    'assinaturas': novos_vips,
                    'cortesAss': cortes_ass,
                    'cortesAvulsos': cortes_avulsos,
                    'ticketMedio': round(fat_total / total_atendimentos, 2) if total_atendimentos > 0 else 0
                },
                'barbeiros': cards,
                'dias': dias_lista
            }
        except Exception as e:
            print(f"❌ Erro no relatório gerencial: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}