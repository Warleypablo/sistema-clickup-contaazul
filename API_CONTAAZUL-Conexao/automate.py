import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Carregar variáveis de ambiente
load_dotenv()

# Conectar ao banco de dados
conn = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    dbname=os.getenv("PG_DBNAME"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    port=os.getenv("PG_PORT")
)

cursor = conn.cursor()

# Criação da tabela de inadimplentes
cursor.execute("""
CREATE TABLE IF NOT EXISTS inadimplentes (
    id SERIAL PRIMARY KEY,
    cliente_id VARCHAR(255),
    nome_cliente VARCHAR(255),
    cnpj_cliente VARCHAR(20),
    valor_nao_pago DECIMAL,
    data_vencimento DATE,
    status VARCHAR(50)
);
""")

# Definir o intervalo de 30 dias atrás até hoje
data_inicio = datetime.now() - timedelta(days=30)
data_fim = datetime.now()

# Excluir dados antigos da tabela de inadimplentes
cursor.execute("DELETE FROM inadimplentes;")
conn.commit()

# Consulta SQL para pegar inadimplentes com vencimento entre os últimos 30 dias e hoje
cursor.execute("""
SELECT cliente_id, cliente_nome, cnpj, nao_pago, data_vencimento, status
FROM a_receber_turbo
WHERE data_vencimento BETWEEN %s AND %s
  AND nao_pago > 0;
""", (data_inicio, data_fim))

inadimplentes = cursor.fetchall()

# Inserir dados na tabela inadimplentes
query_insert = """
INSERT INTO inadimplentes (cliente_id, nome_cliente, cnpj_cliente, valor_nao_pago, data_vencimento, status)
VALUES %s
ON CONFLICT DO NOTHING;
"""

execute_values(cursor, query_insert, inadimplentes)

conn.commit()
cursor.close()
conn.close()

print(f"{len(inadimplentes)} inadimplentes inseridos com sucesso!")
