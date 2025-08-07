import requests
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Carregar variáveis de ambiente
load_dotenv()

class ContaAzulVendasSync:
    def __init__(self):
        # Configurações da API do Conta Azul
        self.base_url = "https://api-v2.contaazul.com"
        self.access_token = os.getenv('CONTA_AZUL_ACCESS_TOKEN')
        
        # Configurações do banco de dados
        self.db_config = {
            'host': os.getenv('PG_HOST'),
            'port': os.getenv('PG_PORT'),
            'database': os.getenv('PG_DBNAME'),
            'user': os.getenv('PG_USER'),
            'password': os.getenv('PG_PASSWORD')
        }
        
    def create_vendas_table(self):
        """Cria a tabela de vendas no banco de dados"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS vendas_conta_azul (
            id VARCHAR(50) PRIMARY KEY,
            numero INTEGER,
            data_venda TIMESTAMP,
            data_vencimento TIMESTAMP,
            cliente_id VARCHAR(50),
            cliente_nome VARCHAR(255),
            cliente_cnpj VARCHAR(20),
            vendedor_id VARCHAR(50),
            vendedor_nome VARCHAR(255),
            status VARCHAR(20),
            tipo VARCHAR(20),
            valor_total DECIMAL(15,2),
            valor_desconto DECIMAL(15,2),
            valor_liquido DECIMAL(15,2),
            observacoes TEXT,
            forma_pagamento VARCHAR(100),
            condicao_pagamento VARCHAR(100),
            transportadora_id VARCHAR(50),
            transportadora_nome VARCHAR(255),
            peso_bruto DECIMAL(10,3),
            peso_liquido DECIMAL(10,3),
            volume INTEGER,
            especie VARCHAR(100),
            marca VARCHAR(100),
            numero_volumes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_vendas_data_venda ON vendas_conta_azul(data_venda);
        CREATE INDEX IF NOT EXISTS idx_vendas_cliente_id ON vendas_conta_azul(cliente_id);
        CREATE INDEX IF NOT EXISTS idx_vendas_status ON vendas_conta_azul(status);
        """
        
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            print("Tabela vendas_conta_azul criada com sucesso!")
        except Exception as e:
            print(f"Erro ao criar tabela: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_vendas_from_api(self, page=1, page_size=100):
        """Busca vendas da API do Conta Azul"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'page': page,
            'size': page_size
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/v1/vendas",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro na API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro ao buscar vendas da API: {e}")
            return None
    
    def insert_venda(self, venda_data):
        """Insere uma venda no banco de dados"""
        insert_sql = """
        INSERT INTO vendas_conta_azul (
            id, numero, data_venda, data_vencimento, cliente_id, cliente_nome, cliente_cnpj,
            vendedor_id, vendedor_nome, status, tipo, valor_total, valor_desconto, valor_liquido,
            observacoes, forma_pagamento, condicao_pagamento, transportadora_id, transportadora_nome,
            peso_bruto, peso_liquido, volume, especie, marca, numero_volumes
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id) DO UPDATE SET
            numero = EXCLUDED.numero,
            data_venda = EXCLUDED.data_venda,
            data_vencimento = EXCLUDED.data_vencimento,
            cliente_id = EXCLUDED.cliente_id,
            cliente_nome = EXCLUDED.cliente_nome,
            cliente_cnpj = EXCLUDED.cliente_cnpj,
            vendedor_id = EXCLUDED.vendedor_id,
            vendedor_nome = EXCLUDED.vendedor_nome,
            status = EXCLUDED.status,
            tipo = EXCLUDED.tipo,
            valor_total = EXCLUDED.valor_total,
            valor_desconto = EXCLUDED.valor_desconto,
            valor_liquido = EXCLUDED.valor_liquido,
            observacoes = EXCLUDED.observacoes,
            forma_pagamento = EXCLUDED.forma_pagamento,
            condicao_pagamento = EXCLUDED.condicao_pagamento,
            transportadora_id = EXCLUDED.transportadora_id,
            transportadora_nome = EXCLUDED.transportadora_nome,
            peso_bruto = EXCLUDED.peso_bruto,
            peso_liquido = EXCLUDED.peso_liquido,
            volume = EXCLUDED.volume,
            especie = EXCLUDED.especie,
            marca = EXCLUDED.marca,
            numero_volumes = EXCLUDED.numero_volumes,
            updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Extrair dados da venda
            venda_id = venda_data.get('id')
            numero = venda_data.get('numero')
            data_venda = venda_data.get('data_venda')
            data_vencimento = venda_data.get('data_vencimento')
            
            # Dados do cliente
            cliente = venda_data.get('cliente', {})
            cliente_id = cliente.get('id')
            cliente_nome = cliente.get('nome')
            cliente_cnpj = cliente.get('cnpj')
            
            # Dados do vendedor
            vendedor = venda_data.get('vendedor', {})
            vendedor_id = vendedor.get('id')
            vendedor_nome = vendedor.get('nome')
            
            # Dados da venda
            status = venda_data.get('status')
            tipo = venda_data.get('tipo')
            valor_total = venda_data.get('valor_total')
            valor_desconto = venda_data.get('valor_desconto')
            valor_liquido = venda_data.get('valor_liquido')
            observacoes = venda_data.get('observacoes')
            
            # Dados de pagamento
            forma_pagamento = venda_data.get('forma_pagamento')
            condicao_pagamento = venda_data.get('condicao_pagamento')
            
            # Dados de transporte
            transportadora = venda_data.get('transportadora', {})
            transportadora_id = transportadora.get('id')
            transportadora_nome = transportadora.get('nome')
            
            peso_bruto = venda_data.get('peso_bruto')
            peso_liquido = venda_data.get('peso_liquido')
            volume = venda_data.get('volume')
            especie = venda_data.get('especie')
            marca = venda_data.get('marca')
            numero_volumes = venda_data.get('numero_volumes')
            
            cursor.execute(insert_sql, (
                venda_id, numero, data_venda, data_vencimento, cliente_id, cliente_nome, cliente_cnpj,
                vendedor_id, vendedor_nome, status, tipo, valor_total, valor_desconto, valor_liquido,
                observacoes, forma_pagamento, condicao_pagamento, transportadora_id, transportadora_nome,
                peso_bruto, peso_liquido, volume, especie, marca, numero_volumes
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao inserir venda {venda_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def sync_vendas(self):
        """Sincroniza todas as vendas da API com o banco de dados"""
        print("Iniciando sincronização de vendas...")
        
        # Criar tabela se não existir
        self.create_vendas_table()
        
        page = 1
        total_vendas = 0
        
        while True:
            print(f"Buscando página {page}...")
            
            vendas_response = self.get_vendas_from_api(page=page)
            
            if not vendas_response:
                break
            
            vendas = vendas_response.get('itens', [])
            
            if not vendas:
                break
            
            for venda in vendas:
                if self.insert_venda(venda):
                    total_vendas += 1
            
            # Verificar se há mais páginas
            paginacao = vendas_response.get('paginacao', {})
            if page >= paginacao.get('total_paginas', 1):
                break
            
            page += 1
        
        print(f"Sincronização concluída! Total de vendas processadas: {total_vendas}")

if __name__ == "__main__":
    sync = ContaAzulVendasSync()
    sync.sync_vendas()