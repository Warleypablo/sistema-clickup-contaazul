import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Carregar variáveis de ambiente
load_dotenv()

def get_db_connection():
    """Função para conectar ao banco de dados usando as mesmas configurações do app.py"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Para Heroku
        conn = psycopg2.connect(database_url, sslmode='require')
    else:
        # Para desenvolvimento local
        conn = psycopg2.connect(
            host=os.getenv('PG_HOST', 'localhost'),
            database=os.getenv('PG_DBNAME'),
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
            port=os.getenv('PG_PORT', '5432')
        )
    return conn

def test_agropedd_queries():
    """Testa várias consultas para entender por que a Agropedd não aparece"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cnpj = '00703697000167'
    
    print(f"=== TESTANDO CONSULTAS PARA CNPJ: {cnpj} ===")
    print()
    
    # 1. Verificar se existe na tabela clientes_turbo
    print("1. Verificando se existe em clientes_turbo:")
    cursor.execute("""
        SELECT nome, cnpj 
        FROM clientes_turbo 
        WHERE cnpj = %s
    """, (cnpj,))
    cliente = cursor.fetchone()
    if cliente:
        print(f"   ✓ Cliente encontrado: {cliente['nome']}")
        nome_cliente = cliente['nome']
    else:
        print("   ✗ Cliente NÃO encontrado em clientes_turbo")
        return
    
    print()
    
    # 2. Verificar registros em a_receber_turbo
    print("2. Verificando registros em a_receber_turbo:")
    cursor.execute("""
        SELECT COUNT(*) as total, 
               COUNT(CASE WHEN nao_pago > 0 THEN 1 END) as nao_pagos
        FROM a_receber_turbo a
        JOIN clientes_turbo c ON a.cliente_nome = c.nome
        WHERE c.cnpj = %s
    """, (cnpj,))
    result = cursor.fetchone()
    print(f"   Total de registros: {result['total']}")
    print(f"   Registros não pagos (nao_pago > 0): {result['nao_pagos']}")
    
    print()
    
    # 3. Verificar dados específicos de a_receber_turbo
    print("3. Dados detalhados de a_receber_turbo:")
    cursor.execute("""
        SELECT a.descricao, a.data_vencimento, a.total, a.nao_pago, a.status
        FROM a_receber_turbo a
        JOIN clientes_turbo c ON a.cliente_nome = c.nome
        WHERE c.cnpj = %s
        ORDER BY a.data_vencimento
    """, (cnpj,))
    registros = cursor.fetchall()
    for reg in registros:
        print(f"   - {reg['descricao']}: R$ {reg['total']:.2f} (Não pago: R$ {reg['nao_pago']:.2f}) - Status: {reg['status']}")
    
    print()
    
    # 4. Verificar se existe em clientes_clickup
    print("4. Verificando se existe em clientes_clickup:")
    cursor.execute("""
        SELECT responsavel, segmento, cluster, status_conta, telefone
        FROM clientes_clickup 
        WHERE cnpj = %s
    """, (cnpj,))
    clickup = cursor.fetchone()
    if clickup:
        print(f"   ✓ Dados ClickUp encontrados:")
        print(f"     - Responsável: {clickup['responsavel']}")
        print(f"     - Segmento: {clickup['segmento']}")
        print(f"     - Cluster: {clickup['cluster']}")
        print(f"     - Status: {clickup['status_conta']}")
    else:
        print("   ✗ Cliente NÃO encontrado em clientes_clickup")
    
    print()
    
    # 5. Verificar dados de LTV
    print("5. Verificando dados de LTV:")
    cursor.execute("""
        SELECT total_pago, total_faturas
        FROM (
            SELECT cliente_nome, 
                   SUM(pago) as total_pago,
                   COUNT(*) as total_faturas
            FROM a_receber_turbo 
            GROUP BY cliente_nome
        ) ltv
        WHERE ltv.cliente_nome = %s
    """, (nome_cliente,))
    ltv = cursor.fetchone()
    if ltv:
        print(f"   ✓ Dados LTV encontrados:")
        print(f"     - Total pago: R$ {ltv['total_pago']:.2f}")
        print(f"     - Total faturas: {ltv['total_faturas']}")
    else:
        print("   ✗ Dados LTV NÃO encontrados")
    
    print()
    
    # 6. Testar a consulta completa do app.py
    print("6. Testando consulta completa do app.py:")
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
        ORDER BY a.data_vencimento DESC
    """, (cnpj,))
    
    resultados = cursor.fetchall()
    print(f"   Resultados encontrados: {len(resultados)}")
    
    if resultados:
        for i, row in enumerate(resultados, 1):
            print(f"   Registro {i}:")
            print(f"     - Descrição: {row['descricao']}")
            print(f"     - Vencimento: {row['data_vencimento']}")
            print(f"     - Total: R$ {row['total']:.2f}")
            print(f"     - Não pago: R$ {row['nao_pago']:.2f}")
            print(f"     - Responsável: {row['responsavel']}")
            ltv_value = row['ltv_total'] if row['ltv_total'] is not None else 0
            print(f"     - LTV Total: R$ {ltv_value:.2f}")
            print()
    else:
        print("   ✗ NENHUM resultado encontrado na consulta completa!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        test_agropedd_queries()
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()