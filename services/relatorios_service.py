from config import Config
from datetime import datetime, timedelta

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
                    
                    # Meta diária (coluna F - índice 5)
                    try:
                        meta_str = valores_b[i][5].replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
                        meta_diaria = float(meta_str)
                        print(f"✅ Meta diária: R$ {meta_diaria:.2f}")
                    except:
                        meta_diaria = 0
                        print(f"⚠️ Meta diária não encontrada, usando R$ 0")
                    
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
                    
                    # Valor do serviço (coluna F)
                    try:
                        valor_limpo = valores_v[i][5].replace('R$', '').replace('.', '').replace(',', '.').strip()
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
        """Relatório de fechamento para ADMIN"""
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
            
            # 1. Buscar dados do barbeiro
            print("Buscando dados do barbeiro...")
            valores_b = self.sheets.get_all_values(Config.SHEETS['barbeiros'])
            print(f"Total de barbeiros na planilha: {len(valores_b)-1}")
            
            meta_diaria = 0
            comissao_base = 0
            url_foto = ""
            
            for i in range(1, len(valores_b)):
                if len(valores_b[i]) > 0 and valores_b[i][0].lower().strip() == nome_busca:
                    print(f"✅ Barbeiro encontrado: {valores_b[i][0]}")
                    
                    # Comissão (coluna 2)
                    try:
                        comissao_str = valores_b[i][2].replace('%', '')
                        comissao_base = float(comissao_str)
                        print(f"   Comissão: {comissao_base}%")
                    except:
                        comissao_base = 0
                        print(f"   Comissão: não encontrada, usando 0%")
                    
                    # Meta diária (coluna 5)
                    try:
                        meta_str = valores_b[i][5].replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
                        meta_diaria = float(meta_str)
                        print(f"   Meta diária: R$ {meta_diaria:.2f}")
                    except:
                        meta_diaria = 0
                        print(f"   Meta diária: não encontrada, usando R$ 0")
                    
                    # Foto (coluna 10)
                    if len(valores_b[i]) > 10:
                        url_foto = valores_b[i][10]
                        print(f"   Foto: {url_foto[:50]}...")
                    break
            
            # 2. Calcular dias trabalhados (CORRIGIDO COM TIMEDELTA)
            print("Calculando dias no período...")
            dias_trab = 0
            temp = d_ini
            while temp <= d_fim:
                dias_trab += 1
                temp = temp + timedelta(days=1)
            
            print(f"   Dias no período: {dias_trab}")
            meta_periodo = dias_trab * meta_diaria
            print(f"   Meta do período: R$ {meta_periodo:.2f}")
            
            # 3. Buscar vendas
            print("Buscando vendas...")
            valores_v = self.sheets.get_all_values(Config.SHEETS['vendas'])
            print(f"   Total de vendas na planilha: {len(valores_v)-1}")
            
            # 4. Processar vendas do barbeiro
            fat_bruto = 0
            comissao_total = 0
            servicos_lista = []
            vendas_encontradas = 0
            
            print("Processando vendas...")
            for i in range(1, len(valores_v)):
                if len(valores_v[i]) < 5:
                    continue
                
                # Verifica se é do barbeiro (coluna 4 - PROFISSIONAL)
                if len(valores_v[i]) > 4 and valores_v[i][4].lower().strip() == nome_busca:
                    try:
                        # Converte data da venda (DD/MM/YYYY)
                        data_parts = valores_v[i][0].split('/')
                        if len(data_parts) == 3:
                            d_venda = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
                            
                            if d_ini <= d_venda <= d_fim:
                                vendas_encontradas += 1
                                
                                # Valor bruto (coluna 5 - V.UNIT)
                                valor_str = valores_v[i][5].replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
                                valor_bruto = float(valor_str) if valor_str else 0
                                
                                # Verifica se é VIP (coluna 6 - ASS)
                                is_vip = len(valores_v[i]) > 6 and valores_v[i][6].upper() == "VIP"
                                
                                # Calcula comissão
                                ganho = valor_bruto * (comissao_base / 100)
                                
                                fat_bruto += valor_bruto
                                comissao_total += ganho
                                
                                servicos_lista.append({
                                    'data': valores_v[i][0],
                                    'detalhe': valores_v[i][3],
                                    'isVip': is_vip,
                                    'valor': valor_bruto,
                                    'comissao': ganho
                                })
                    except Exception as e:
                        print(f"   Erro na venda linha {i}: {e}")
                        continue
            
            print(f"   Vendas encontradas no período: {vendas_encontradas}")
            
            # 5. Calcular ocupação
            tempo_total = len(servicos_lista) * 45
            tempo_disponivel = dias_trab * 480
            ocupacao = (tempo_total / tempo_disponivel * 100) if tempo_disponivel > 0 else 0
            
            # 6. Calcular percentual da meta
            perc_atingido = (comissao_total / meta_periodo * 100) if meta_periodo > 0 else 0
            
            print(f"\n=== RESULTADO DO FECHAMENTO ===")
            print(f"Faturamento Bruto: R$ {fat_bruto:.2f}")
            print(f"Total Comissão: R$ {comissao_total:.2f}")
            print(f"Atendimentos: {len(servicos_lista)}")
            print(f"Ocupação: {ocupacao:.1f}%")
            print(f"Meta Atingida: {perc_atingido:.1f}%")
            print(f"===============================\n")
            
            return {
                'foto': url_foto,
                'totalVendas': fat_bruto,
                'valorUnitarioCesta': 0,
                'totalComissao': comissao_total,
                'qtdAtendimentosReais': len(servicos_lista),
                'qtdVips': 0,
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
        """Relatório gerencial com rankings"""
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
                    if len(valores_v[i]) > 0 and valores_v[i][0]:
                        data_parts = valores_v[i][0].split('/')
                        if len(data_parts) == 3:
                            d_venda = datetime(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
                            if d_ini <= d_venda <= d_fim:
                                vendas_periodo.append(valores_v[i])
                except:
                    pass
            
            print(f"Vendas no período: {len(vendas_periodo)}")
            
            # Dias com movimento
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
                for v in vendas_b:
                    try:
                        # Tenta coluna 5 primeiro (V.UNIT)
                        if len(v) > 5 and v[5]:
                            valor_str = v[5]
                        # Se não, tenta coluna 7 (TOTAL DIA)
                        elif len(v) > 7 and v[7]:
                            valor_str = v[7]
                        else:
                            continue
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
                    if len(v) > 5 and v[5]:
                        valor_str = v[5]
                    elif len(v) > 7 and v[7]:
                        valor_str = v[7]
                    else:
                        continue
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
            
            print(f"\n=== RESULTADO GERENCIAL ===")
            print(f"Faturamento Total: R$ {fat_total:.2f}")
            print(f"Total Atendimentos: {total_atendimentos}")
            print(f"Novos Clientes: {novos}")
            print(f"Cortes VIP: {cortes_ass}")
            print(f"Cortes Avulsos: {cortes_avulsos}")
            print(f"Barbeiros processados: {len(cards)}")
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
                'barbeiros': cards
            }
        except Exception as e:
            print(f"❌ Erro no relatório gerencial: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}