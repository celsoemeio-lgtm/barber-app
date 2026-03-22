from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime

from config import Config
from services.google_sheets import GoogleSheetsService
from services.auth_service import AuthService
from services.agenda_service import AgendaService
from services.clientes_service import ClientesService
from services.servicos_service import ServicosService
from services.barbeiros_service import BarbeirosService
from services.vendas_service import VendasService
from services.relatorios_service import RelatoriosService

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Inicializa serviços
sheets_service = GoogleSheetsService()
auth_service = AuthService(sheets_service)
agenda_service = AgendaService(sheets_service)
clientes_service = ClientesService(sheets_service)
servicos_service = ServicosService(sheets_service)
barbeiros_service = BarbeirosService(sheets_service)
vendas_service = VendasService(sheets_service)
relatorios_service = RelatoriosService(sheets_service)

# Decorator de login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user'].get('nivel') != 'ADM':
            return jsonify({'erro': 'Acesso negado'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROTAS PÚBLICAS ====================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user' in session:
            return redirect(url_for('dashboard'))
        return render_template('Login.html')
    
    data = request.get_json()
    resultado = auth_service.validar_login_barbeiro(data['user'], data['pass'])
    
    if resultado['sucesso']:
        session['user'] = {
            'nome': resultado['nome'],
            'tipo': 'BARBEIRO',
            'nivel': resultado['nivel']
        }
        return jsonify({'success': True, 'redirect': '/dashboard'})
    
    return jsonify({'success': False, 'message': resultado['msg']})

# ROTA PARA MOSTRAR A PÁGINA DE LOGIN DO CLIENTE (GET)
@app.route('/login_cliente', methods=['GET'])
def login_cliente_page():
    return render_template('Login_Cliente.html')

# ROTA PARA PROCESSAR O LOGIN DO CLIENTE (POST)
@app.route('/login_cliente', methods=['POST'])
def login_cliente():
    data = request.get_json()
    resultado = auth_service.gerenciar_acesso_cliente(data)
    
    if resultado['status'] in ["EXISTENTE", "NOVO"]:
        session['user'] = {
            'nome': resultado['nome'],
            'tipo': 'CLIENTE',
            'celular': resultado['celular']
        }
        return jsonify({
            'success': True,
            'status': resultado['status'],
            'redirect': '/painel_diario'
        })
    
    return jsonify({'success': False, 'message': resultado.get('msg', 'Erro')})

# ==================== ROTAS DO CLIENTE (LINK SEPARADO) ====================

# NOVA ROTA PARA O LINK SEPARADO (página HTML)
@app.route('/cliente', methods=['GET'])
def cliente_login_separado():
    return render_template('login_cliente.html')

# NOVA API PARA AUTENTICAÇÃO DO CLIENTE VIA LINK SEPARADO
@app.route('/cliente/auth', methods=['POST'])
def cliente_auth_separado():
    data = request.get_json()
    resultado = auth_service.gerenciar_acesso_cliente(data)
    
    if resultado['status'] in ["EXISTENTE", "NOVO"]:
        session['user'] = {
            'nome': resultado['nome'],
            'tipo': 'CLIENTE',
            'celular': resultado['celular']
        }
        return jsonify({
            'success': True,
            'status': resultado['status'],
            'redirect': '/painel_diario'
        })
    
    return jsonify({'success': False, 'message': resultado.get('msg', 'Erro')})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==================== ROTA USUÁRIO ATUAL (CORRIGIDA) ====================
@app.route('/api/usuario_atual')
def usuario_atual():
    if 'user' in session:
        # Adiciona o campo logado explicitamente
        user_data = session['user'].copy()
        user_data['logado'] = True
        return jsonify(user_data)
    return jsonify({'logado': False})

# ==================== ROTAS DE PÁGINAS ====================

@app.route('/dashboard')
@login_required
def dashboard():
    if session['user']['tipo'] != 'BARBEIRO':
        return redirect(url_for('painel_diario'))
    return render_template('Dashboard.html', user=session['user'])

@app.route('/painel_diario')
@login_required
def painel_diario():
    return render_template('Painel_Diario.html', user=session['user'])

@app.route('/form_agendamento')
@login_required
def form_agendamento():
    cache = session.get('temp_agendamento', {})
    return render_template('Form_Agendamento.html', user=session['user'], cache=cache)

@app.route('/form_atendimento')
@login_required
def form_atendimento():
    if session['user']['tipo'] != 'BARBEIRO':
        return redirect(url_for('painel_diario'))
    return render_template('Form_Atendimento.html', user=session['user'])

@app.route('/form_relatorio')
@login_required
def form_relatorio():
    if session['user']['tipo'] != 'BARBEIRO':
        return redirect(url_for('painel_diario'))
    return render_template('Form_Relatorio.html', user=session['user'])

@app.route('/form_cliente')
@login_required
@admin_required
def form_cliente():
    return render_template('Form_Cliente.html', user=session['user'])

@app.route('/form_servicos')
@login_required
@admin_required
def form_servicos():
    return render_template('Form_Servicos.html', user=session['user'])

@app.route('/form_barbeiros')
@login_required
@admin_required
def form_barbeiros():
    return render_template('Form_Barbeiros.html', user=session['user'])

@app.route('/relatorio_folha')
@login_required
@admin_required
def relatorio_folha():
    return render_template('Relatorio_folha.html', user=session['user'])

@app.route('/form_gerencial')
@login_required
@admin_required
def form_gerencial():
    return render_template('Form_Gerencial.html', user=session['user'])

@app.route('/dados_agenda')
@login_required
@admin_required
def dados_agenda():
    return render_template('Dados_Agenda.html', user=session['user'])

# ==================== API AGENDA ====================

@app.route('/api/agenda/dados', methods=['POST'])
@login_required
def api_agenda_dados():
    data = request.get_json()
    resultado = agenda_service.get_dados_painel_diario(data['data'])
    return jsonify(resultado)

@app.route('/api/agenda/preparar', methods=['POST'])
@login_required
def api_agenda_preparar():
    dados = request.get_json()
    session['temp_agendamento'] = dados
    return jsonify({'success': True})

@app.route('/api/agenda/salvar', methods=['POST'])
@login_required
def api_agenda_salvar():
    dados = request.get_json()
    dados['isAdm'] = (session['user']['tipo'] == 'BARBEIRO')
    resultado = agenda_service.salvar_agendamento(dados)
    return jsonify(resultado)

@app.route('/api/agenda/cancelar', methods=['POST'])
@login_required
def api_agenda_cancelar():
    dados = request.get_json()
    resultado = agenda_service.cancelar_agendamento(dados)
    return jsonify(resultado)

@app.route('/api/agenda/listar')
@login_required
@admin_required
def api_agenda_listar():
    resultado = agenda_service.listar_agenda()
    return jsonify(resultado)

@app.route('/api/agenda/excluir', methods=['POST'])
@login_required
@admin_required
def api_agenda_excluir():
    dados = request.get_json()
    resultado = agenda_service.excluir_linha_agenda(dados)
    return jsonify(resultado)

# ==================== API CLIENTES ====================

@app.route('/api/clientes/listar')
@login_required
def api_clientes_listar():
    if session['user']['tipo'] == 'BARBEIRO' and session['user'].get('nivel') == 'ADM':
        clientes = clientes_service.listar_clientes()
    else:
        clientes = clientes_service.buscar_nomes_clientes()
    return jsonify(clientes)

@app.route('/api/clientes/salvar', methods=['POST'])
@login_required
@admin_required
def api_clientes_salvar():
    dados = request.get_json()
    resultado = clientes_service.salvar_cliente(
        dados['nome'],
        dados['whats'],
        dados['plano'],
        dados.get('idx')
    )
    return jsonify({'status': resultado})

@app.route('/api/clientes/nomes')
@login_required
def api_clientes_nomes():
    nomes = clientes_service.buscar_nomes_clientes()
    return jsonify(nomes)

# ==================== API SERVIÇOS ====================

@app.route('/api/servicos/listar')
@login_required
def api_servicos_listar():
    servicos = servicos_service.listar_servicos()
    return jsonify(servicos)

@app.route('/api/servicos/nomes')
@login_required
def api_servicos_nomes():
    servicos = servicos_service.listar_nomes_servicos()
    return jsonify(servicos)

@app.route('/api/servicos/salvar', methods=['POST'])
@login_required
@admin_required
def api_servicos_salvar():
    dados = request.get_json()
    resultado = servicos_service.salvar_servico(dados['nome'], dados['preco'])
    return jsonify({'status': resultado})

# ==================== API BARBEIROS ====================

@app.route('/api/barbeiros/listar')
@login_required
def api_barbeiros_listar():
    nomes = barbeiros_service.listar_nomes()
    return jsonify(nomes)

@app.route('/api/barbeiros/buscar', methods=['POST'])
@login_required
@admin_required
def api_barbeiros_buscar():
    dados = request.get_json()
    resultado = barbeiros_service.buscar_dados(dados['nome'])
    return jsonify(resultado)

@app.route('/api/barbeiros/salvar', methods=['POST'])
@login_required
@admin_required
def api_barbeiros_salvar():
    dados = request.get_json()
    resultado = barbeiros_service.salvar(dados)
    return jsonify({'status': resultado})

@app.route('/api/barbeiros/foto', methods=['POST'])
@login_required
def api_barbeiros_foto():
    dados = request.get_json()
    foto = auth_service.buscar_foto_barbeiro(dados['nome'])
    return jsonify({'foto': foto})

# ==================== API VENDAS ====================

@app.route('/api/vendas/dados_iniciais')
@login_required
def api_vendas_dados_iniciais():
    if session['user']['tipo'] != 'BARBEIRO':
        return jsonify({'erro': 'Acesso negado'}), 403
    resultado = vendas_service.get_dados_iniciais()
    return jsonify(resultado)

@app.route('/api/vendas/finalizar', methods=['POST'])
@login_required
def api_vendas_finalizar():
    if session['user']['tipo'] != 'BARBEIRO':
        return jsonify({'erro': 'Acesso negado'}), 403
    dados = request.get_json()
    resultado = vendas_service.processar_venda(dados)
    return jsonify(resultado)

# ==================== API RELATÓRIOS ====================

@app.route('/api/relatorios/diario', methods=['POST'])
@login_required
def api_relatorios_diario():
    try:
        if session['user']['tipo'] != 'BARBEIRO':
            return jsonify({'erro': 'Acesso negado'}), 403
        
        dados = request.get_json()
        if not dados or 'data' not in dados:
            return jsonify({'erro': 'Data não fornecida'}), 400
        
        data = dados['data']
        nome_barbeiro = session['user']['nome']
        
        # Log para debug no servidor
        print(f"🔍 Relatório diário - Data: {data}, Barbeiro: {nome_barbeiro}")
        
        resultado = relatorios_service.get_dados_relatorio_diario(data, nome_barbeiro)
        
        return jsonify(resultado)
    
    except Exception as e:
        import traceback
        erro_detalhado = traceback.format_exc()
        print("❌ ERRO em /api/relatorios/diario:")
        print(erro_detalhado)
        return jsonify({'erro': str(e), 'detalhes': erro_detalhado}), 500

@app.route('/api/relatorios/fechamento', methods=['POST'])
@login_required
# @admin_required  # REMOVIDO - Agora USER também pode acessar
def api_relatorios_fechamento():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        print(f"🔍 Fechamento - Barbeiro: {dados.get('barbeiro')}, Datas: {dados.get('data_inicio')} a {dados.get('data_fim')}")
        
        resultado = relatorios_service.obter_fechamento_unificado(
            dados.get('barbeiro'),
            dados.get('data_inicio'),
            dados.get('data_fim'),
            dados.get('valor_assinatura', 80),
            dados.get('perc_casa', 50)
        )
        
        return jsonify(resultado)
    
    except Exception as e:
        import traceback
        erro_detalhado = traceback.format_exc()
        print("❌ ERRO em /api/relatorios/fechamento:")
        print(erro_detalhado)
        return jsonify({'erro': str(e), 'detalhes': erro_detalhado}), 500

@app.route('/api/relatorios/gerencial', methods=['POST'])
@login_required
@admin_required
def api_relatorios_gerencial():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        resultado = relatorios_service.get_relatorio_gerencial(
            dados.get('data_inicio'),
            dados.get('data_fim')
        )
        
        return jsonify(resultado)
    
    except Exception as e:
        import traceback
        erro_detalhado = traceback.format_exc()
        print("❌ ERRO em /api/relatorios/gerencial:")
        print(erro_detalhado)
        return jsonify({'erro': str(e), 'detalhes': erro_detalhado}), 500

@app.route('/teste', methods=['GET'])
def teste():
    return jsonify({'status': 'ok', 'mensagem': 'Servidor funcionando'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)