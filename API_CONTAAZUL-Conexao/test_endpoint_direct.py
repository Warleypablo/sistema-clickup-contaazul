import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import json

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

def simulate_buscar_endpoint(cnpj):
    """Simula exatamente o que o endpoint /buscar faz"""
    print(f"Simulando endpoint /buscar com CNPJ: {cnpj}")
    
    try:
        conn = get_db_connection()
        if not conn:
            print("Erro: Não foi possível conectar ao banco de dados")
            return []
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consulta exata do app.py
        print("Executando consulta SQL...")
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
        
        # Converter resultados para dicionário (usando RealDictCursor)
        rows = cursor.fetchall()
        result = []
        
        print(f"Encontrados {len(rows)} registros para CNPJ {cnpj}")
        
        for row in rows:
            # RealDictCursor já retorna um dict-like object
            row_dict = dict(row)
            # Tratar valores None para evitar erros de formatação
            for key, value in row_dict.items():
                if value is None:
                    row_dict[key] = None
                elif isinstance(value, (int, float)) and key in ['ltv_total', 'total_faturas', 'valor_inadimplente_total']:
                    row_dict[key] = float(value) if value is not None else 0.0
            result.append(row_dict)
        
        print(f"Resultado processado: {len(result)} registros")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
        # Converter para JSON como faria o Flask
        json_result = json.dumps(result, default=str, ensure_ascii=False, indent=2)
        print(f"JSON resultado (primeiros 500 chars): {json_result[:500]}...")
        
        return result
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    # Testar com o CNPJ da Agropedd
    cnpj_teste = '00703697000167'
    resultado = simulate_buscar_endpoint(cnpj_teste)
    
    print(f"\n=== RESULTADO FINAL ===")
    print(f"Número de registros retornados: {len(resultado)}")
    
    if resultado:
        print("\nPrimeiro registro:")
        primeiro = resultado[0]
        print(f"  Cliente: {primeiro.get('cliente_nome')}")
        print(f"  Descrição: {primeiro.get('descricao')}")
        print(f"  Valor: R$ {primeiro.get('total', 0):.2f}")
        print(f"  Não pago: R$ {primeiro.get('nao_pago', 0):.2f}")
        print(f"  Responsável: {primeiro.get('responsavel')}")
        print(f"  LTV Total: R$ {primeiro.get('ltv_total', 0):.2f}")
    else:
        print("NENHUM registro encontrado!")