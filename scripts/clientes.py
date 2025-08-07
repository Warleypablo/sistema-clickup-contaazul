import requests
import time
import psycopg2
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

access_token = "eyJraWQiOiJUa1BRbWs0UlR3M3RuWlZXcDdEanBURFhcL2RTajNvMU5SckI0R3I3ZzFTMD0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI5ZjAyY2MwZS0wY2ViLTQyOWUtYmE1NS03YmEyZGEwZTE4ZTYiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuc2EtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3NhLWVhc3QtMV9WcDgzSjExd0EiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiI2NnNnbWRhdHFxM24wcWtmNGNva3JqODlpZSIsIm9yaWdpbl9qdGkiOiIxYzM4ZTY2OS03YzYxLTQ0NzUtYThkNi1mM2FkNGQxMTEwYzEiLCJldmVudF9pZCI6ImVmODFjNmMzLWQ5Y2EtNDczYi1hNmZiLWJmNTIwNzI1MmM5YiIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4gb3BlbmlkIHByb2ZpbGUiLCJhdXRoX3RpbWUiOjE3NTEyODYyOTIsImV4cCI6MTc1MTMxMTk0OCwiaWF0IjoxNzUxMzA4MzQ5LCJqdGkiOiI4ZGMwZTBiOS05OTE2LTQ1MzktYTU2NS0xYTM2ZTQ5NjgwYzUiLCJ1c2VybmFtZSI6Im1hcmxvbi5jYXJuZWlyb0B0dXJib3BhcnRuZXJzLmNvbS5iciJ9.tEfCDpj7cqkknbzwa39Rl-PzIYR0LzNwxhj5BiNhfkoXeWygNKor8XBp1r4Egglu1xXtTSMYT5iI7hIJGpOA4c3IHLfMbdxmx2GuWdvNA-k2zhAQ3cq30jPFGKDe3zE8O6dLwjkTqqqzwXXzIO8YkGAtXoe6cg5i3x6zRn1041jbHFGtQAW3Y78z4G5QmZtREqi5qj5Ama70mfZc-0Udr-JBNrNZCM8nwlfEJ965TNDOk6dtx7jSLqZwX8TVsXrbjqOqN8fnaCQ-NGJF1307w_gwQq7om1pIcGNkOLH-I-N9rpxnkKWucpkX4d8Hwu6Nupo19XcJnkPhbo5FN5BLYQ"  # Certifique-se de usar o token correto
url = "https://api-v2.contaazul.com/v1/pessoa"

# Definir parâmetros para consulta de clientes (sem filtros)
query = {
    "pagina": "1",
    "tamanho_pagina": "50"  # Ajuste o tamanho da página conforme necessário
}

headers = {"Authorization": f"Bearer {access_token}"}

def remover_dados_antigos():
    """Função para remover dados antigos da tabela de clientes_turbo"""
    with conn.cursor() as cursor:
        query_delete = "DELETE FROM clientes_turbo;"
        try:
            cursor.execute(query_delete)
            conn.commit()
            print("Dados antigos removidos com sucesso!")
        except Exception as e:
            conn.rollback()
            print("Erro ao remover dados antigos:", e)

def buscar_clientes():
    todos_clientes = []
    pagina = 1
    max_retries = 5  # Definir limite máximo de tentativas em caso de erro 429 (limite de requisição)

    while True:
        print(f"\n--- Requisição para a página {pagina} ---")
        print(f"Parâmetros da consulta: {query}")

        query["pagina"] = str(pagina)  # Atualizar a página na consulta

        # Realizar a requisição GET à API
        response = requests.get(url, headers=headers, params=query)

        print(f"Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Resposta da API: {data}")

            clientes = data.get('itens', [])

            if not clientes:
                print(f"Nenhum cliente encontrado para a página {pagina}.")
                break  # Não há mais clientes para buscar

            # Armazenar todos os dados disponíveis dos clientes
            for cliente in clientes:
                nome = cliente.get('nome', 'Não disponível')
                documento = cliente.get('documento', None)  # CNPJ ou CPF
                email = cliente.get('email', None)  # Email
                telefone = cliente.get('telefone', 'Não disponível')

                # Se o cliente não tiver documento, vamos puxar o que tiver disponível
                if documento is None:
                    documento = 'Documento não disponível'

                # Se o email estiver ausente, atribuímos um valor padrão
                if email is None:
                    email = 'email@exemplo.com'

                # Verificar se o endereço existe e não é None
                endereco = cliente.get('endereco', {})
                if endereco is not None:
                    endereco_completo = f"{endereco.get('logradouro', '')}, {endereco.get('numero', '')} - {endereco.get('bairro', '')}, {endereco.get('cidade', '')}/{endereco.get('estado', '')}, {endereco.get('cep', '')}"
                else:
                    endereco_completo = "Endereço não disponível"  # Valor padrão caso o endereço seja None
                
                # Verificar se o nome já existe no banco
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM clientes_turbo WHERE nome = %s", (nome,))
                    if cursor.fetchone():
                        print(f"Cliente {nome} já existe no banco. Ignorando inserção.")
                    else:
                        todos_clientes.append((nome, documento, email, telefone, endereco_completo))

            # Verificar se há mais páginas
            if len(clientes) < int(query["tamanho_pagina"]):
                print(f"Menos clientes do que o tamanho da página. Finalizando busca.")
                break  # Não há mais clientes, encerrar a busca
            pagina += 1
            time.sleep(1)  # Pausa para evitar sobrecarga da API

        elif response.status_code == 429:
            print(f"Limite de requisições atingido para a página {pagina}. Tentando novamente...")
            retries = 0
            while retries < max_retries:
                retries += 1
                print(f"Tentando novamente após {retries} tentativas...")
                time.sleep(10)  # Espera antes de tentar novamente
                response = requests.get(url, headers=headers, params=query)
                if response.status_code == 200:
                    break  # Sucesso ao tentar novamente
            else:
                print(f"Limite de requisições repetido {max_retries} vezes. Abortando busca da página {pagina}.")
                break

        else:
            print(f"Erro ao buscar dados da página {pagina}: {response.status_code} - {response.text}")
            break

    return todos_clientes

# Executar a busca e listar os clientes
remover_dados_antigos()  # Remover dados antigos antes de adicionar os novos
clientes = buscar_clientes()
print(f"Total de clientes encontrados: {len(clientes)}")

# Inserir no banco de dados
if clientes:
    print(f"Iniciando a inserção de {len(clientes)} clientes no banco...")
    with conn.cursor() as cursor:
        query = """
        INSERT INTO clientes_turbo (nome, cnpj, email, telefone, endereco) 
        VALUES %s
        ON CONFLICT (cnpj) DO NOTHING;  -- Ignorar se o cliente já existe no banco
        """
        
        try:
            execute_values(cursor, query, clientes)  # Inserir todos os clientes de uma vez
            conn.commit()
            print(f"{cursor.rowcount} clientes inseridos com sucesso!")
        except Exception as e:
            conn.rollback()
            print("Erro ao inserir dados:", e)

conn.close()
print("Conexão com o banco fechada.")
