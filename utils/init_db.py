import os
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias."""
    # Obter a URL do banco de dados do Heroku ou usar as variáveis de ambiente locais
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
    
    # Criar um cursor
    cur = conn.cursor()
    
    # Criar tabelas se não existirem
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes_turbo (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(255) NOT NULL,
        cnpj VARCHAR(20) UNIQUE,
        email VARCHAR(255),
        telefone VARCHAR(20),
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS a_receber_turbo (
        id SERIAL PRIMARY KEY,
        status VARCHAR(50),
        total DECIMAL(10, 2),
        descricao TEXT,
        data_vencimento DATE,
        nao_pago DECIMAL(10, 2),
        pago DECIMAL(10, 2),
        data_criacao TIMESTAMP,
        data_alteracao TIMESTAMP,
        cliente_id VARCHAR(255),
        cliente_nome VARCHAR(255),
        link_pagamento TEXT
    );
    """)
    
    # Commit das alterações
    conn.commit()
    
    # Fechar cursor e conexão
    cur.close()
    conn.close()
    
    print("Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    init_db()