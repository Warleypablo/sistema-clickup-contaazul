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

access_token = "eyJraWQiOiJUa1BRbWs0UlR3M3RuWlZXcDdEanBURFhcL2RTajNvMU5SckI0R3I3ZzFTMD0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJkZGU5Y2YwMy04NTgyLTRmYzYtOGVjMi1jZDE2YzA2ZGExNjUiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuc2EtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3NhLWVhc3QtMV9WcDgzSjExd0EiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiIzcWMxdmxjaXNianJpOG9oYjI0MXYzMjk5NCIsIm9yaWdpbl9qdGkiOiJkMDc5MjU0ZS00ZmVjLTQ0OTEtODE1Yy0zMzYxMzJlNmFiNWQiLCJldmVudF9pZCI6ImZjMTUyYWM5LTc5MzgtNDA5MC1hMGRiLTJlNTQ0YWM3ODZjNCIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4gb3BlbmlkIHByb2ZpbGUiLCJhdXRoX3RpbWUiOjE3NTA4NTcyNDAsImV4cCI6MTc1MTMxMjIxNCwiaWF0IjoxNzUxMzA4NjE0LCJqdGkiOiI5ZTNkZTdmMC0wN2QyLTRlMzUtOWFmNi1mNWVkZTQwNDIwN2YiLCJ1c2VybmFtZSI6Im1hcmxvbmNvLjEyOTdAZ21haWwuY29tIn0.v8lMPeB9ZDmKs42tXGdSoZAas63w6-YxNUPMs3UaVaNBToFDPZKrbMLVoKJYq5tOU0RbtEowHsQjVkMocCIneINzeq1RCTC5R0y7S0Q1IXg1P_mrT5JDJP1uhZb-Uxa7pLLt3yjleTQQrhX9oWRrHFNkvpk_Fg-GraMIY5ANMwdorR-74Tlovs7aHPWVQgLIRzW6iIctK5X45hVw9zxa_YEEAGQI9Z1OaZrY2JdoMaAUb6IqNafYFqL2JIY3AOxUMWoYSLdqbY9ZJjalLaFRInS3n7Inb5AqepQ4PitpDd7CfcL244FQXTt_vmJnPT2l6WcDxJH0sPfOqeIw-aJ2cA"  # Certifique-se de usar o token correto
url = "https://api-v2.contaazul.com/v1/pessoa"

# Definir parâmetros para consulta de clientes (sem filtros)
query = {
    "pagina": "1",
    "tamanho_pagina": "50"  # Ajuste o tamanho da página conforme necessário
}

headers = {"Authorization": f"Bearer {access_token}"}

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
