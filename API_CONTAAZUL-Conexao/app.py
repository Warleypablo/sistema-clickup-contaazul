import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import traceback

# Tentar importar psycopg2, mas continuar mesmo se não estiver disponível
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("AVISO: psycopg2 não está instalado. A conexão com o banco de dados não estará disponível.")
    print("Para instalar, execute: pip install psycopg2-binary")

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da aplicação Flask
app = Flask(__name__)

# Função para conectar ao banco de dados
def get_db_connection():
    if not PSYCOPG2_AVAILABLE:
        return None
        
    try:
        # Verificar se estamos no Heroku (DATABASE_URL estará disponível)
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Formato esperado: postgres://user:password@host:port/dbname
            # Heroku usa postgresql:// em vez de postgres://, então precisamos substituir
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
            # Conectar usando a URL do banco de dados
            conn = psycopg2.connect(database_url)
        else:
            # Conectar usando variáveis de ambiente individuais
            conn = psycopg2.connect(
                host=os.getenv("PG_HOST"),
                dbname=os.getenv("PG_DBNAME"),
                user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            port=os.getenv("PG_PORT")
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        app.logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None

# Rota principal - página de consulta
@app.route('/')
def index():
    return render_template('index.html')

# Rota para verificar a conexão com o banco de dados
@app.route('/check-db')
def check_db():
    import sys
    print("=== DEBUG: Endpoint /check-db chamado ===", file=sys.stderr)
    if not PSYCOPG2_AVAILABLE:
        return jsonify({
            'status': 'error', 
            'message': 'O módulo psycopg2 não está instalado. Por favor, instale-o com: pip install psycopg2-binary'
        }), 500
        
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            print("=== DEBUG: Conexão com banco bem-sucedida ===", file=sys.stderr)
            return jsonify({'status': 'success', 'message': 'Conexão com o banco de dados estabelecida com sucesso!'})
        else:
            print("=== DEBUG: Falha na conexão com banco ===", file=sys.stderr)
            return jsonify({'status': 'error', 'message': 'Não foi possível conectar ao banco de dados.'}), 500
    except Exception as e:
        print(f"=== DEBUG: Erro na conexão: {str(e)} ===", file=sys.stderr)
        return jsonify({'status': 'error', 'message': f'Erro ao verificar conexão: {str(e)}'}), 500

@app.route('/test-post', methods=['POST'])
def test_post():
    import sys
    print("=== DEBUG: Endpoint /test-post chamado ===", file=sys.stderr)
    print(f"=== DEBUG: request.form = {request.form} ===", file=sys.stderr)
    print(f"=== DEBUG: request.method = {request.method} ===", file=sys.stderr)
    return jsonify({'status': 'success', 'form_data': dict(request.form)})

# Rota para buscar dados por CNPJ
@app.route('/buscar', methods=['POST'])
def buscar():
    import sys
    print("=== DEBUG: Endpoint /buscar chamado ===", file=sys.stderr)
    print(f"=== DEBUG: request.form = {request.form} ===", file=sys.stderr)
    
    cnpj = request.form.get('cnpj')
    print(f"=== DEBUG: CNPJ recebido: {cnpj} ===", file=sys.stderr)
    
    if not cnpj:
        print("=== DEBUG: CNPJ não fornecido ===", file=sys.stderr)
        return jsonify({'error': 'CNPJ é obrigatório'}), 400
    
    if not PSYCOPG2_AVAILABLE:
        return jsonify({
            'error': 'O módulo psycopg2 não está instalado. Por favor, instale-o com: pip install psycopg2-binary'
        }), 500
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Não foi possível conectar ao banco de dados'}), 500
            
        cursor = conn.cursor()
        
        # Usar RealDictCursor para facilitar o manuseio dos dados
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consulta para buscar contas a receber pelo CNPJ do cliente
        # Mostrando registros com saldo pendente (nao_pago > 0)
        # Incluindo informações do ClickUp e LTV quando disponíveis
        cursor.execute("""
        SELECT a.id, a.status, a.total, a.descricao, a.data_vencimento, 
               a.nao_pago, a.pago, a.data_criacao, a.data_alteracao, 
               a.cliente_id, a.cliente_nome, a.link_pagamento,
               ck.responsavel, ck.segmento, ck.cluster, ck.status_conta, 
               ck.atividade, ck.telefone as telefone_clickup,
               ltv.total_pago as ltv_total,
               ltv.total_faturas,
               ltv.valor_inadimplente_total
        FROM a_receber_turbo a
        JOIN clientes_turbo c ON a.cliente_nome = c.nome
        LEFT JOIN clientes_clickup ck ON c.cnpj = ck.cnpj
        LEFT JOIN (
            SELECT cliente_nome,
                   SUM(pago) as total_pago,
                   COUNT(*) as total_faturas,
                   SUM(CASE WHEN nao_pago > 0 AND data_vencimento < CURRENT_DATE THEN nao_pago ELSE 0 END) as valor_inadimplente_total
            FROM a_receber_turbo
            GROUP BY cliente_nome
        ) ltv ON a.cliente_nome = ltv.cliente_nome
        WHERE c.cnpj = %s
          AND a.nao_pago > 0
          AND a.data_vencimento <= CURRENT_DATE
        ORDER BY a.data_vencimento DESC
        """, (cnpj,))
        
        # Converter resultados para dicionário (usando RealDictCursor)
        rows = cursor.fetchall()
        result = []
        
        print(f"DEBUG: Encontrados {len(rows)} registros para CNPJ {cnpj}")
        
        for row in rows:
            # RealDictCursor já retorna um dict-like object
            row_dict = dict(row)
            # Tratar valores None para evitar erros de formatação
            for key, value in row_dict.items():
                if value is None:
                    row_dict[key] = None
                elif isinstance(value, (int, float)) and key in ['ltv_total', 'total_faturas', 'valor_inadimplente_total']:
                    row_dict[key] = float(value) if value is not None else 0.0
            
            # Debug: imprimir dados do ClickUp para verificação
            print(f"DEBUG ClickUp para {row_dict.get('cliente_nome')}: responsavel={row_dict.get('responsavel')}, segmento={row_dict.get('segmento')}, cluster={row_dict.get('cluster')}, status_conta={row_dict.get('status_conta')}")
            
            result.append(row_dict)
        
        print(f"DEBUG: Resultado processado: {len(result)} registros")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Erro ao buscar por CNPJ: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# Rota alternativa para buscar por nome do cliente
@app.route('/buscar_por_nome', methods=['POST'])
def buscar_por_nome():
    nome = request.form.get('nome')
    
    if not nome:
        return jsonify({'error': 'Nome não fornecido'}), 400
    
    if not PSYCOPG2_AVAILABLE:
        return jsonify({
            'error': 'O módulo psycopg2 não está instalado. Por favor, instale-o com: pip install psycopg2-binary'
        }), 500
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Não foi possível conectar ao banco de dados'}), 500
            
        # Usar RealDictCursor para facilitar o manuseio dos dados
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consulta para buscar contas a receber pelo nome do cliente
        # Mostrando registros com saldo pendente (nao_pago > 0)
        # Incluindo informações do ClickUp e LTV quando disponíveis
        cursor.execute("""
        SELECT a.id, a.status, a.total, a.descricao, a.data_vencimento, 
               a.nao_pago, a.pago, a.data_criacao, a.data_alteracao, 
               a.cliente_id, a.cliente_nome, a.link_pagamento,
               ck.responsavel, ck.segmento, ck.cluster, ck.status_conta, 
               ck.atividade, ck.telefone as telefone_clickup,
               ltv.total_pago as ltv_total,
               ltv.total_faturas,
               ltv.valor_inadimplente_total
        FROM a_receber_turbo a
        LEFT JOIN clientes_turbo c ON a.cliente_nome = c.nome
        LEFT JOIN clientes_clickup ck ON c.cnpj = ck.cnpj
        LEFT JOIN (
            SELECT cliente_nome,
                   SUM(pago) as total_pago,
                   COUNT(*) as total_faturas,
                   SUM(CASE WHEN nao_pago > 0 AND data_vencimento < CURRENT_DATE THEN nao_pago ELSE 0 END) as valor_inadimplente_total
            FROM a_receber_turbo
            GROUP BY cliente_nome
        ) ltv ON a.cliente_nome = ltv.cliente_nome
        WHERE a.cliente_nome ILIKE %s
          AND a.nao_pago > 0
          AND a.data_vencimento <= CURRENT_DATE
        ORDER BY a.data_vencimento DESC
        """, (f'%{nome}%',))
        
        # Converter resultados para dicionário (usando RealDictCursor)
        rows = cursor.fetchall()
        result = []
        
        print(f"DEBUG: Encontrados {len(rows)} registros para nome {nome}")
        
        for row in rows:
            # RealDictCursor já retorna um dict-like object
            row_dict = dict(row)
            # Tratar valores None para evitar erros de formatação
            for key, value in row_dict.items():
                if value is None:
                    row_dict[key] = None
                elif isinstance(value, (int, float)) and key in ['ltv_total', 'total_faturas', 'valor_inadimplente_total']:
                    row_dict[key] = float(value) if value is not None else 0.0
            
            # Debug: imprimir dados do ClickUp para verificação
            print(f"DEBUG ClickUp para {row_dict.get('cliente_nome')}: responsavel={row_dict.get('responsavel')}, segmento={row_dict.get('segmento')}, cluster={row_dict.get('cluster')}, status_conta={row_dict.get('status_conta')}")
            
            result.append(row_dict)
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Erro ao buscar por nome: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# Rota para listar todos os clientes
@app.route('/listar-clientes', methods=['GET'])
def listar_clientes():
    import sys
    print("=== DEBUG: Endpoint /listar-clientes chamado ===", file=sys.stderr)
    
    if not PSYCOPG2_AVAILABLE:
        return jsonify({
            'error': 'O módulo psycopg2 não está instalado. Por favor, instale-o com: pip install psycopg2-binary'
        }), 500
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Não foi possível conectar ao banco de dados'}), 500
            
        # Usar RealDictCursor para facilitar o manuseio dos dados
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consulta para buscar todos os clientes únicos com informações do ClickUp
        cursor.execute("""
        SELECT DISTINCT c.nome, c.cnpj,
               ck.responsavel, ck.segmento, ck.cluster, ck.status_conta, 
               ck.atividade, ck.telefone as telefone_clickup,
               CASE 
                   WHEN COUNT(a.id) FILTER (WHERE a.nao_pago > 0 AND a.data_vencimento <= CURRENT_DATE) > 0 THEN true
                   ELSE false
               END as tem_pendencias
        FROM clientes_turbo c
        LEFT JOIN clientes_clickup ck ON c.cnpj = ck.cnpj
        LEFT JOIN a_receber_turbo a ON c.nome = a.cliente_nome
        GROUP BY c.nome, c.cnpj, ck.responsavel, ck.segmento, ck.cluster, ck.status_conta, ck.atividade, ck.telefone
        ORDER BY c.nome
        """)
        
        # Converter resultados para dicionário
        rows = cursor.fetchall()
        result = []
        
        print(f"DEBUG: Encontrados {len(rows)} clientes")
        
        for row in rows:
            row_dict = dict(row)
            # Tratar valores None
            for key, value in row_dict.items():
                if value is None:
                    row_dict[key] = None
            
            result.append(row_dict)
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Erro ao listar clientes: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# Iniciar a aplicação
if __name__ == '__main__':
    # Obter a porta do ambiente (para compatibilidade com Heroku) ou usar 5000 como padrão
    port = int(os.environ.get("PORT", 5000))
    # Definir o modo de depuração com base no ambiente
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=True, host='0.0.0.0', port=port)