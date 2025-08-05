import requests
import time
import psycopg2
from datetime import datetime, timedelta
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env
load_dotenv()

# Conectar ao banco de dados PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    dbname=os.getenv("PG_DBNAME"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    port=os.getenv("PG_PORT")
)

access_token = ("eyJraWQiOiJUa1BRbWs0UlR3M3RuWlZXcDdEanBURFhcL2RTajNvMU5SckI0R3I3ZzFTMD0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJkZGU5Y2YwMy04NTgyLTRmYzYtOGVjMi1jZDE2YzA2ZGExNjUiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuc2EtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3NhLWVhc3QtMV9WcDgzSjExd0EiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiIzcWMxdmxjaXNianJpOG9oYjI0MXYzMjk5NCIsIm9yaWdpbl9qdGkiOiJjZjI3ZjU1OS0xM2VhLTQxMzgtYmMzMi1kMDM0NmVlMWI3YmYiLCJldmVudF9pZCI6ImJiMWI4NmI0LWFjODYtNDdmNS1hYjNjLTI1NGY3YWYzNDBkMSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4gb3BlbmlkIHByb2ZpbGUiLCJhdXRoX3RpbWUiOjE3NTM5Njk1NjMsImV4cCI6MTc1NDMxNzIzNSwiaWF0IjoxNzU0MzEzNjM1LCJqdGkiOiJlMGQ5Mzc1Yy0yNWJkLTQ3M2UtOTkwNC01MjAxZDk3ODczNjMiLCJ1c2VybmFtZSI6Im1hcmxvbmNvLjEyOTdAZ21haWwuY29tIn0.XGqt6jVBQC7KC9xSKnKqYdJuIBSqzW6VZFBLH7wGeQSaCO6pIDcNkOPF2RvQcbl9G66bH5UBhdVcCOYUhbr6YivsrXCcv75ZCrnHiwWsfoiTGQ9uyNDaQlttLZHiGjGPIIUbfH-geHmGXXIUUd_65G_12T50pDqWwBnwvlyb4H5v1GT0Nu0ISdz-RzspM2lHpg1BZR2p8qwqwhSgizCcw6P8rwGsFV8PQHmSXCpjZpCeRo6Bn6jW30Cvow8jAYfn4sUxx7iByHi4GeM5mc4RjR79ryZGhg-lXtikFZi_wiB6DWxyvlFum8oOnPFPRb1o35MBkyt_7Agr4gp1Fy4j7A")

url = "https://api-v2.contaazul.com/v1/financeiro/eventos-financeiros/contas-a-receber/buscar"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

def buscar_todos_itens_dia(data, tamanho_pagina=50, max_retries=5):
    pagina = 1
    todos_itens_dia = []
    retries = 0
    
    while True:
        payload = {
            "pagina": str(pagina),
            "tamanho_pagina": str(tamanho_pagina),
            "status": [],  # Para pegar todos os status
            "data_vencimento_de": data,
            "data_vencimento_ate": data
        }
        response = requests.get(url, headers=headers, params=payload)
        
        if response.status_code == 200:
            dados = response.json()
            itens = dados.get("itens", [])
            if not itens:
                break
            todos_itens_dia.extend(itens)
            if len(itens) < tamanho_pagina:
                break
            pagina += 1
            retries = 0  # Reset retries on success
        elif response.status_code == 429:
            print(f"Limite de requisições atingido (429) no dia {data}. Tentando novamente...")
            retries += 1
            if retries > max_retries:
                print(f"Limite de requisições repetido {max_retries} vezes para o dia {data}. Abortando busca desse dia.")
                break
            # Sem sleep aqui, tenta imediatamente
            continue
        else:
            print(f"Erro ao buscar página {pagina} do dia {data}: {response.status_code} - {response.text}")
            break
        
        time.sleep(3)  # Espera 3 segundos entre requisições para evitar limites

    return todos_itens_dia

def gerar_datas(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current.strftime("%Y-%m-%d")
        current += timedelta(days=1)

# Configurar intervalo de datas
data_inicio = datetime.strptime("2025-02-20", "%Y-%m-%d")
data_fim = datetime.strptime("2026-05-20", "%Y-%m-%d")

todos_itens = []
ids_vistos = set()

for dia in gerar_datas(data_inicio, data_fim):
    print(f"Buscando dados do dia {dia}...")
    itens_dia = buscar_todos_itens_dia(dia, tamanho_pagina=50)
    novos_itens = 0
    for item in itens_dia:
        if item["id"] not in ids_vistos:
            todos_itens.append(item)
            ids_vistos.add(item["id"])
            novos_itens += 1
    print(f"Encontrados {len(itens_dia)} itens no dia, {novos_itens} novos.")
    time.sleep(0.15)

print(f"\nTotal único de itens coletados: {len(todos_itens)}")

if todos_itens:
    def achatar_item(item):
        item_copy = item.copy()
        if "cliente" in item_copy and isinstance(item_copy["cliente"], dict):
            for k, v in item_copy["cliente"].items():
                item_copy[f"cliente_{k}"] = v
            del item_copy["cliente"]
        return item_copy

    dados_achatados = [achatar_item(i) for i in todos_itens]

    with conn.cursor() as cursor:
       
        # Inserir dados na tabela
        query_insert = """
        INSERT INTO a_receber_turbo (id, status, total, descricao, data_vencimento, nao_pago, pago, data_criacao, data_alteracao, cliente_id, cliente_nome, link_pagamento)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """
        valores = [
            (
                item['id'],
                item['status'],
                item['total'],
                item['descricao'],
                item['data_vencimento'],
                item.get('nao_pago'),
                item.get('pago'),
                item.get('data_criacao'),
                item.get('data_alteracao'),
                item.get('cliente_id'),
                item.get('cliente_nome'),
                item.get('payment_url', None)  # Adicionando o link de pagamento, se disponível na API
            ) for item in dados_achatados
        ]
        try:
            execute_values(cursor, query_insert, valores)
            conn.commit()
            print(f"{cursor.rowcount} linhas inseridas com sucesso!")
        except Exception as e:
            conn.rollback()
            print("Erro ao inserir dados:", e)

        # Atualizar o status de pagamento (pago) dos clientes que já pagaram o boleto
        query_update_status = """
        UPDATE a_receber_turbo
        SET status = %s, pago = TRUE, data_alteracao = %s
        WHERE id = %s AND status != 'pago';
        """
        data_atualizacao = datetime.now()
        for item in dados_achatados:
            if item.get('status') == 'pago':  # Verifica se o status é 'pago'
                cursor.execute(query_update_status, ('pago', data_atualizacao, item['id']))

            # Commit após atualizar
            conn.commit()

conn.close()
print("Conexão com o banco fechada.")