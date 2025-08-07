import requests
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Carregar variáveis de ambiente
load_dotenv()

class ContaAzulServicosSync:
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
        
    def create_servicos_table(self):
        """Cria a tabela de serviços no banco de dados"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS servicos_conta_azul (
            id VARCHAR(50) PRIMARY KEY,
            codigo VARCHAR(100),
            descricao VARCHAR(500),
            nome VARCHAR(255),
            tipo_servico VARCHAR(50),
            status VARCHAR(20),
            preco DECIMAL(15,2),
            custo DECIMAL(15,2),
            margem_lucro DECIMAL(5,2),
            codigo_cnae VARCHAR(20),
            codigo_municipio_servico VARCHAR(20),
            lei_116 VARCHAR(100),
            natureza_operacional_id VARCHAR(50),
            categoria_id VARCHAR(50),
            categoria_nome VARCHAR(255),
            subcategoria_id VARCHAR(50),
            subcategoria_nome VARCHAR(255),
            unidade_medida VARCHAR(10),
            tempo_execucao INTEGER,
            observacoes TEXT,
            ativo BOOLEAN DEFAULT TRUE,
            id_externo VARCHAR(100),
            id_servico INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabela para cenários tributários dos serviços
        CREATE TABLE IF NOT EXISTS servicos_cenarios_tributarios (
            id VARCHAR(50) PRIMARY KEY,
            servico_id VARCHAR(50) REFERENCES servicos_conta_azul(id),
            municipio_codigo INTEGER,
            municipio_nome VARCHAR(255),
            municipio_uf VARCHAR(2),
            inss_aliquota DECIMAL(5,2),
            iss_aliquota DECIMAL(5,2),
            iss_retido BOOLEAN DEFAULT FALSE,
            nome_usuario VARCHAR(255),
            ultima_atualizacao TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_servicos_codigo ON servicos_conta_azul(codigo);
        CREATE INDEX IF NOT EXISTS idx_servicos_categoria ON servicos_conta_azul(categoria_id);
        CREATE INDEX IF NOT EXISTS idx_servicos_status ON servicos_conta_azul(status);
        CREATE INDEX IF NOT EXISTS idx_servicos_cnae ON servicos_conta_azul(codigo_cnae);
        CREATE INDEX IF NOT EXISTS idx_cenarios_servico ON servicos_cenarios_tributarios(servico_id);
        """
        
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            print("Tabelas de serviços criadas com sucesso!")
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_servicos_from_api(self, page=1, page_size=100):
        """Busca serviços da API do Conta Azul"""
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
                f"{self.base_url}/v1/servicos",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro na API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro ao buscar serviços da API: {e}")
            return None
    
    def insert_servico(self, servico_data):
        """Insere um serviço no banco de dados"""
        insert_servico_sql = """
        INSERT INTO servicos_conta_azul (
            id, codigo, descricao, nome, tipo_servico, status, preco, custo, margem_lucro,
            codigo_cnae, codigo_municipio_servico, lei_116, natureza_operacional_id,
            categoria_id, categoria_nome, subcategoria_id, subcategoria_nome,
            unidade_medida, tempo_execucao, observacoes, ativo, id_externo, id_servico
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id) DO UPDATE SET
            codigo = EXCLUDED.codigo,
            descricao = EXCLUDED.descricao,
            nome = EXCLUDED.nome,
            tipo_servico = EXCLUDED.tipo_servico,
            status = EXCLUDED.status,
            preco = EXCLUDED.preco,
            custo = EXCLUDED.custo,
            margem_lucro = EXCLUDED.margem_lucro,
            codigo_cnae = EXCLUDED.codigo_cnae,
            codigo_municipio_servico = EXCLUDED.codigo_municipio_servico,
            lei_116 = EXCLUDED.lei_116,
            natureza_operacional_id = EXCLUDED.natureza_operacional_id,
            categoria_id = EXCLUDED.categoria_id,
            categoria_nome = EXCLUDED.categoria_nome,
            subcategoria_id = EXCLUDED.subcategoria_id,
            subcategoria_nome = EXCLUDED.subcategoria_nome,
            unidade_medida = EXCLUDED.unidade_medida,
            tempo_execucao = EXCLUDED.tempo_execucao,
            observacoes = EXCLUDED.observacoes,
            ativo = EXCLUDED.ativo,
            id_externo = EXCLUDED.id_externo,
            id_servico = EXCLUDED.id_servico,
            updated_at = CURRENT_TIMESTAMP
        """
        
        insert_cenario_sql = """
        INSERT INTO servicos_cenarios_tributarios (
            id, servico_id, municipio_codigo, municipio_nome, municipio_uf,
            inss_aliquota, iss_aliquota, iss_retido, nome_usuario, ultima_atualizacao
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id) DO UPDATE SET
            municipio_codigo = EXCLUDED.municipio_codigo,
            municipio_nome = EXCLUDED.municipio_nome,
            municipio_uf = EXCLUDED.municipio_uf,
            inss_aliquota = EXCLUDED.inss_aliquota,
            iss_aliquota = EXCLUDED.iss_aliquota,
            iss_retido = EXCLUDED.iss_retido,
            nome_usuario = EXCLUDED.nome_usuario,
            ultima_atualizacao = EXCLUDED.ultima_atualizacao
        """
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Extrair dados do serviço
            servico_id = servico_data.get('id')
            codigo = servico_data.get('codigo')
            descricao = servico_data.get('descricao')
            nome = servico_data.get('nome')
            tipo_servico = servico_data.get('tipo_servico')
            status = servico_data.get('status')
            preco = servico_data.get('preco')
            custo = servico_data.get('custo')
            margem_lucro = servico_data.get('margem_lucro')
            
            # Códigos fiscais
            codigo_cnae = servico_data.get('codigo_cnae')
            codigo_municipio_servico = servico_data.get('codigo_municipio_servico')
            lei_116 = servico_data.get('lei_116')
            
            # Natureza operacional
            natureza_operacional = servico_data.get('natureza_operacional', {})
            natureza_operacional_id = natureza_operacional.get('id')
            
            # Categoria
            categoria = servico_data.get('categoria', {})
            categoria_id = categoria.get('id')
            categoria_nome = categoria.get('nome')
            
            # Subcategoria
            subcategoria = servico_data.get('subcategoria', {})
            subcategoria_id = subcategoria.get('id')
            subcategoria_nome = subcategoria.get('nome')
            
            # Outros dados
            unidade_medida = servico_data.get('unidade_medida')
            tempo_execucao = servico_data.get('tempo_execucao')
            observacoes = servico_data.get('observacoes')
            ativo = servico_data.get('ativo', True)
            id_externo = servico_data.get('id_externo')
            id_servico = servico_data.get('id_servico')
            
            # Inserir serviço
            cursor.execute(insert_servico_sql, (
                servico_id, codigo, descricao, nome, tipo_servico, status, preco, custo, margem_lucro,
                codigo_cnae, codigo_municipio_servico, lei_116, natureza_operacional_id,
                categoria_id, categoria_nome, subcategoria_id, subcategoria_nome,
                unidade_medida, tempo_execucao, observacoes, ativo, id_externo, id_servico
            ))
            
            # Inserir cenários tributários
            cenarios = servico_data.get('lista_cenario_tributario', [])
            for cenario in cenarios:
                cenario_id = f"{servico_id}_{cenario.get('municipio', {}).get('codigo', '')}"
                municipio = cenario.get('municipio', {})
                
                cursor.execute(insert_cenario_sql, (
                    cenario_id,
                    servico_id,
                    municipio.get('codigo'),
                    municipio.get('nome'),
                    municipio.get('uf'),
                    cenario.get('inss_aliquota'),
                    cenario.get('iss_aliquota'),
                    cenario.get('iss_retido', False),
                    cenario.get('nome_usuario'),
                    cenario.get('ultima_atualizacao')
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao inserir serviço {servico_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def sync_servicos(self):
        """Sincroniza todos os serviços da API com o banco de dados"""
        print("Iniciando sincronização de serviços...")
        
        # Criar tabelas se não existirem
        self.create_servicos_table()
        
        page = 1
        total_servicos = 0
        
        while True:
            print(f"Buscando página {page}...")
            
            servicos_response = self.get_servicos_from_api(page=page)
            
            if not servicos_response:
                break
            
            servicos = servicos_response.get('itens', [])
            
            if not servicos:
                break
            
            for servico in servicos:
                if self.insert_servico(servico):
                    total_servicos += 1
            
            # Verificar se há mais páginas
            paginacao = servicos_response.get('paginacao', {})
            if page >= paginacao.get('total_paginas', 1):
                break
            
            page += 1
        
        print(f"Sincronização concluída! Total de serviços processados: {total_servicos}")

if __name__ == "__main__":
    sync = ContaAzulServicosSync()
    sync.sync_servicos()