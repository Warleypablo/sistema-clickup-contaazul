import os
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

try:
    # Conectar ao banco de dados
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        dbname=os.getenv("PG_DBNAME"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        port=os.getenv("PG_PORT")
    )
    
    cursor = conn.cursor()
    
    # Testar a consulta com JOIN
    query = """
    SELECT a.cliente_nome, a.total, a.nao_pago, 
           ck.responsavel, ck.segmento, ck.cluster, ck.status_conta
    FROM a_receber_turbo a
    JOIN clientes_turbo c ON a.cliente_nome = c.nome
    LEFT JOIN clientes_clickup ck ON c.cnpj = ck.cnpj
    WHERE c.cnpj = '00703697000167'
    LIMIT 3;
    """
    
    cursor.execute(query)
    result = cursor.fetchall()
    
    print("Resultado da consulta com JOIN:")
    if result:
        for r in result:
            print(f"Cliente: {r[0]}")
            print(f"Total: {r[1]}")
            print(f"Não Pago: {r[2]}")
            print(f"Responsável: {r[3]}")
            print(f"Segmento: {r[4]}")
            print(f"Cluster: {r[5]}")
            print(f"Status Conta: {r[6]}")
            print("---")
    else:
        print("Nenhum resultado encontrado")
    
    # Testar também uma busca por nome
    print("\nTestando busca por nome:")
    query2 = """
    SELECT a.cliente_nome, a.total, 
           ck.responsavel, ck.segmento
    FROM a_receber_turbo a
    LEFT JOIN clientes_turbo c ON a.cliente_nome = c.nome
    LEFT JOIN clientes_clickup ck ON c.cnpj = ck.cnpj
    WHERE a.cliente_nome ILIKE '%teste%'
    LIMIT 3;
    """
    
    cursor.execute(query2)
    result2 = cursor.fetchall()
    
    if result2:
        for r in result2:
            print(f"Cliente: {r[0]}, Total: {r[1]}, Responsável: {r[2]}, Segmento: {r[3]}")
    else:
        print("Nenhum resultado encontrado para busca por nome")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Erro: {e}")