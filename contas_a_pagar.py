import requests
import time
import psycopg2
from datetime import datetime, timedelta
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    dbname=os.getenv("PG_DBNAME"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    port=os.getenv("PG_PORT")
)

access_token = "eyJraWQiOiJUa1BRbWs0UlR3M3RuWlZXcDdEanBURFhcL2RTajNvMU5SckI0R3I3ZzFTMD0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI5ZjAyY2MwZS0wY2ViLTQyOWUtYmE1NS03YmEyZGEwZTE4ZTYiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuc2EtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3NhLWVhc3QtMV9WcDgzSjExd0EiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiI2NnNnbWRhdHFxM24wcWtmNGNva3JqODlpZSIsIm9yaWdpbl9qdGkiOiJjNmNiODMyYi1lNDJhLTRmYWEtYmM5OC1kZmU3OGVjNDIxNGYiLCJldmVudF9pZCI6ImY0ODliOGJjLTA0NTAtNDliMi1iNmI2LTk4NWRhMDZlYTBjYSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4gb3BlbmlkIHByb2ZpbGUiLCJhdXRoX3RpbWUiOjE3NTI2Njk5MDIsImV4cCI6MTc1MzM3NzkwMSwiaWF0IjoxNzUzMzc0MzAxLCJqdGkiOiI0MzlkMjZkOS1mZmM0LTQ0YzQtYTg0OS04ZDQ5OWM3N2Y3MTAiLCJ1c2VybmFtZSI6Im1hcmxvbi5jYXJuZWlyb0B0dXJib3BhcnRuZXJzLmNvbS5iciJ9.kwd9xJxHjy-m-h9s7sY0UGeJLEDFoHDzWfduVtCVGscOn39UmgCnNOJVXTTcstfo87lh-F6-JAJ1PaGpfKyMx4U3B_Fo1RgUEnCLosPzfaPXn6_dGJZQyM3I-h44spnPvU2NgsQyJOLcnwYWMJQ0Di74F9GFCUfWTPMUVFvaBrPZMejQ2H2rByQA-hlMjlIXGuuEUCn6S-Z5CxpsUJ5iAcw_EQq-xi5l2BGLyPmNbi1YedS-CYVpzk9OJolE9LcaOMBYX_hBPpLcrTo2r3mP_7WSlm3voxnA-kgts2_r5yGh0W_fU2_gsyQvHGFzXCdEY1BtC_Wqw3PYB5Mw7FnF6w"  # coloque seu token real

url = "https://api-v2.contaazul.com/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar"

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
            "status": [],
            "data_vencimento_de": data.strftime("%Y-%m-%d"),
            "data_vencimento_ate": data.strftime("%Y-%m-%d")
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
            retries = 0
        elif response.status_code == 429:
            print(f"Limite de requisições atingido para o dia {data.strftime('%d/%m/%Y')}, tentando novamente...")
            retries += 1
            if retries > max_retries:
                print(f"Abortando após várias tentativas no dia {data.strftime('%d/%m/%Y')}.")
                break
            continue
        else:
            print(f"Erro {response.status_code} para o dia {data.strftime('%d/%m/%Y')}: {response.text}")
            break
        time.sleep(1)
    return todos_itens_dia

def gerar_datas(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)

data_inicio = datetime.strptime("2025-07-25", "%Y-%m-%d")
data_fim = datetime.strptime("2025-07-25", "%Y-%m-%d")

todos_itens = []
ids_vistos = set()

for dia_atual in gerar_datas(data_inicio, data_fim):
    print(f"Buscando dados do dia {dia_atual.strftime('%d/%m/%Y')}...")
    itens_dia = buscar_todos_itens_dia(dia_atual, tamanho_pagina=50)
    novos_itens = 0
    for item in itens_dia:
        if item["id"] not in ids_vistos:
            todos_itens.append(item)
            ids_vistos.add(item["id"])
            novos_itens += 1
    print(f"{len(itens_dia)} itens encontrados, {novos_itens} novos.")
    time.sleep(0.15)

print(f"Total único coletado: {len(todos_itens)}")

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
        query = """
        INSERT INTO a_pagar_turbo (
            id, status, total, descricao, data_vencimento,
            nao_pago, pago, data_criacao, data_alteracao,
            fornecedor, nome
        ) VALUES %s
        ON CONFLICT (id) DO NOTHING
        """
        valores = []
        for item in dados_achatados:
            linha = []
            for coluna in ['id', 'status', 'total', 'descricao', 'data_vencimento', 'nao_pago', 'pago', 'data_criacao', 'data_alteracao']:
                valor = item.get(coluna)
                linha.append(valor)
            fornecedor = item.get('fornecedor', {})
            if isinstance(fornecedor, dict):
                fornecedor_id = fornecedor.get('id')
                fornecedor_nome = fornecedor.get('nome')
            else:
                fornecedor_id = None
                fornecedor_nome = None
            linha.append(fornecedor_id)
            linha.append(fornecedor_nome)
            valores.append(tuple(linha))

        try:
            execute_values(cursor, query, valores)
            conn.commit()
            print(f"{cursor.rowcount} linhas inseridas com sucesso!")
        except Exception as e:
            conn.rollback()
            print("Erro ao inserir dados:", e)

conn.close()
print("Conexão com o banco fechada.")
