import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

# Função para conectar ao banco de dados
def connect_to_db():
    return psycopg2.connect(
        host=os.getenv("PG_HOST"),
        dbname=os.getenv("PG_DBNAME"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        port=os.getenv("PG_PORT")
    )

try:
    # Conectar ao banco de dados PostgreSQL
    conn = connect_to_db()
    cursor = conn.cursor()

    # Deletar os dados antigos da tabela Faturas antes de adicionar os novos
    delete_query = "DELETE FROM Faturas;"
    cursor.execute(delete_query)

    # Confirmar a transação de deletação
    conn.commit()

    # Ler a planilha Uf_Revenues.xlsx
    file_path = 'Uf_Revenues.xlsx'
    df = pd.read_excel(file_path)

    # Extrair as colunas necessárias, incluindo 'dueDate' e 'lastAcquittanceDate'
    df_faturas = df[['financialEvent.negotiator.name', 'chargeRequest.url', 'dueDate', 'lastAcquittanceDate']]

    # Renomear as colunas para corresponder à tabela Faturas
    df_faturas.columns = ['negotiator_name', 'chargeRequest_url', 'Vencimento', 'data_pagamento']

    # Converter a coluna 'data_pagamento' para datetime e substituir NaT por NULL (None)
    df_faturas.loc[:, 'data_pagamento'] = pd.to_datetime(df_faturas['data_pagamento'], errors='coerce')
    df_faturas.loc[df_faturas['data_pagamento'].isna(), 'data_pagamento'] = None  # Substitui NaT por NULL

    # Comando SQL para inserir os dados na tabela Faturas, incluindo a coluna data_pagamento
    insert_query_faturas = """
        INSERT INTO Faturas (negotiator_name, chargeRequest_url, Vencimento, data_pagamento)
        VALUES (%s, %s, %s, %s)
    """

    # Inserir cada linha na tabela Faturas
    for index, row in df_faturas.iterrows():
        # Inserir na tabela Faturas
        cursor.execute(insert_query_faturas, (row['negotiator_name'], row['chargeRequest_url'], row['Vencimento'], row['data_pagamento']))

    # Confirmar a transação de inserção
    conn.commit()

    print("Dados antigos deletados e novos dados inseridos com sucesso na tabela Faturas!")

except (Exception, psycopg2.DatabaseError) as error:
    print(f"Erro ao realizar a operação no banco de dados: {error}")
    conn.rollback()  # Caso algo dê errado, faz rollback para não comprometer a integridade dos dados

finally:
    # Fechar o cursor e a conexão
    if cursor:
        cursor.close()
    if conn:
        conn.close()
