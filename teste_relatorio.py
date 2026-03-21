from services.google_sheets import GoogleSheetsService
from services.relatorios_service import RelatoriosService
from config import Config
import json

print("=" * 60)
print("🧪 TESTE DO RELATÓRIO DE FECHAMENTO")
print("=" * 60)

# Configuração dos valores (os mesmos que você seleciona no HTML)
BARBEIRO = "CASSIO"
DATA_INICIO = "2026-02-18"
DATA_FIM = "2026-03-20"
VALOR_ASSINATURA = 80
PERC_CASA = 50

print("\n📋 PARÂMETROS DO TESTE:")
print(f"   Barbeiro: {BARBEIRO}")
print(f"   Período: {DATA_INICIO} até {DATA_FIM}")
print(f"   Assinatura: R$ {VALOR_ASSINATURA}")
print(f"   Casa: {PERC_CASA}%")
print("=" * 60)

try:
    # Conecta na planilha
    print("\n🔌 Conectando ao Google Sheets...")
    sheets = GoogleSheetsService()
    print("✅ Conexão estabelecida!")
    
    # Cria o serviço de relatórios
    relatorios = RelatoriosService(sheets)
    
    # Executa o cálculo
    print("\n📊 Executando cálculo do relatório...")
    resultado = relatorios.obter_fechamento_unificado(
        BARBEIRO,
        DATA_INICIO,
        DATA_FIM,
        VALOR_ASSINATURA,
        PERC_CASA
    )
    
    print("\n" + "=" * 60)
    print("📈 RESULTADO DO RELATÓRIO:")
    print("=" * 60)
    
    # Verifica se houve erro
    if isinstance(resultado, dict) and 'erro' in resultado:
        print(f"❌ ERRO: {resultado['erro']}")
    else:
        # Exibe os dados formatados
        print(f"\n👤 BARBEIRO: {BARBEIRO}")
        print(f"📸 FOTO: {resultado.get('foto', 'Sem foto')[:50]}...")
        
        print(f"\n💰 FATURAMENTO:")
        print(f"   Total Bruto: R$ {resultado.get('totalVendas', 0):.2f}")
        print(f"   Total Comissão: R$ {resultado.get('totalComissao', 0):.2f}")
        print(f"   Bônus VIP: R$ {resultado.get('valorUnitarioCesta', 0):.2f}")
        
        print(f"\n📊 MÉTRICAS:")
        print(f"   Atendimentos: {resultado.get('qtdAtendimentosReais', 0)}")
        print(f"   Cortes VIP: {resultado.get('qtdVips', 0)}")
        print(f"   Comissão Base: {resultado.get('percComissaoBase', 0)}%")
        print(f"   Ocupação: {resultado.get('taxaOcupacao', 0):.1f}%")
        
        print(f"\n🎯 META:")
        print(f"   Meta do Período: R$ {resultado.get('metaValor', 0):.2f}")
        print(f"   Percentual Atingido: {resultado.get('metaPercent', 0):.1f}%")
        
        # Lista os serviços
        servicos = resultado.get('servicos', [])
        print(f"\n📋 SERVIÇOS ({len(servicos)} atendimentos):")
        print("-" * 60)
        
        if servicos:
            for i, servico in enumerate(servicos[:10], 1):  # Mostra os primeiros 10
                vip_marker = "⭐ VIP" if servico.get('isVip') else "📌"
                print(f"   {i:2}. {servico['data']} | {vip_marker} {servico['detalhe']:20} | R$ {servico['valor']:.2f}")
            
            if len(servicos) > 10:
                print(f"   ... e mais {len(servicos) - 10} serviços")
        else:
            print("   Nenhum serviço encontrado no período")
        
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        
        # Salva o resultado em um arquivo JSON para análise
        with open('resultado_relatorio.json', 'w', encoding='utf-8') as f:
            # Converte para JSON (trata valores não serializáveis)
            resultado_json = {}
            for key, value in resultado.items():
                if key == 'servicos':
                    resultado_json[key] = value
                else:
                    resultado_json[key] = value if not isinstance(value, (int, float)) else float(value)
            json.dump(resultado_json, f, indent=2, ensure_ascii=False)
        print("📁 Resultado salvo em: resultado_relatorio.json")
        
except Exception as e:
    print(f"\n❌ ERRO GRAVE:")
    print(f"   {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)