import requests
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Carregar variáveis de ambiente
load_dotenv()

class ContaAzulNotasFiscaisSync:
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
        
    def create_notas_fiscais_table(self):
        """Cria a tabela de notas fiscais no banco de dados"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS notas_fiscais_conta_azul (
            id VARCHAR(50) PRIMARY KEY,
            numero INTEGER,
            serie VARCHAR(10),
            tipo VARCHAR(20),
            modelo VARCHAR(10),
            chave_acesso VARCHAR(50),
            data_emissao TIMESTAMP,
            data_vencimento TIMESTAMP,
            data_competencia TIMESTAMP,
            status VARCHAR(30),
            situacao VARCHAR(30),
            
            -- Dados do emitente
            emitente_id VARCHAR(50),
            emitente_nome VARCHAR(255),
            emitente_cnpj VARCHAR(20),
            emitente_ie VARCHAR(20),
            emitente_endereco TEXT,
            
            -- Dados do destinatário
            destinatario_id VARCHAR(50),
            destinatario_nome VARCHAR(255),
            destinatario_cnpj VARCHAR(20),
            destinatario_cpf VARCHAR(15),
            destinatario_ie VARCHAR(20),
            destinatario_endereco TEXT,
            
            -- Valores
            valor_total DECIMAL(15,2),
            valor_produtos DECIMAL(15,2),
            valor_servicos DECIMAL(15,2),
            valor_desconto DECIMAL(15,2),
            valor_frete DECIMAL(15,2),
            valor_seguro DECIMAL(15,2),
            valor_outras_despesas DECIMAL(15,2),
            valor_ipi DECIMAL(15,2),
            valor_icms DECIMAL(15,2),
            valor_pis DECIMAL(15,2),
            valor_cofins DECIMAL(15,2),
            valor_iss DECIMAL(15,2),
            valor_inss DECIMAL(15,2),
            valor_ir DECIMAL(15,2),
            valor_csll DECIMAL(15,2),
            
            -- Informações fiscais
            natureza_operacao VARCHAR(255),
            cfop VARCHAR(10),
            municipio_prestacao_servico VARCHAR(255),
            codigo_municipio_prestacao INTEGER,
            
            -- Transporte
            modalidade_frete INTEGER,
            transportadora_id VARCHAR(50),
            transportadora_nome VARCHAR(255),
            peso_bruto DECIMAL(10,3),
            peso_liquido DECIMAL(10,3),
            volume INTEGER,
            
            -- Observações e informações adicionais
            observacoes TEXT,
            informacoes_adicionais TEXT,
            
            -- Venda relacionada
            venda_id VARCHAR(50),
            
            -- Controle
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabela para itens das notas fiscais
        CREATE TABLE IF NOT EXISTS notas_fiscais_itens (
            id VARCHAR(50) PRIMARY KEY,
            nota_fiscal_id VARCHAR(50) REFERENCES notas_fiscais_conta_azul(id),
            produto_id VARCHAR(50),
            servico_id VARCHAR(50),
            codigo VARCHAR(100),
            descricao VARCHAR(500),
            quantidade DECIMAL(15,3),
            unidade VARCHAR(10),
            valor_unitario DECIMAL(15,2),
            valor_total DECIMAL(15,2),
            valor_desconto DECIMAL(15,2),
            
            -- Informações fiscais do item
            ncm VARCHAR(20),
            cest VARCHAR(20),
            cfop VARCHAR(10),
            origem INTEGER,
            
            -- Impostos
            icms_situacao_tributaria VARCHAR(10),
            icms_aliquota DECIMAL(5,2),
            icms_valor DECIMAL(15,2),
            ipi_situacao_tributaria VARCHAR(10),
            ipi_aliquota DECIMAL(5,2),
            ipi_valor DECIMAL(15,2),
            pis_situacao_tributaria VARCHAR(10),
            pis_aliquota DECIMAL(5,2),
            pis_valor DECIMAL(15,2),
            cofins_situacao_tributaria VARCHAR(10),
            cofins_aliquota DECIMAL(5,2),
            cofins_valor DECIMAL(15,2),
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_nf_numero ON notas_fiscais_conta_azul(numero);
        CREATE INDEX IF NOT EXISTS idx_nf_chave ON notas_fiscais_conta_azul(chave_acesso);
        CREATE INDEX IF NOT EXISTS idx_nf_data_emissao ON notas_fiscais_conta_azul(data_emissao);
        CREATE INDEX IF NOT EXISTS idx_nf_destinatario ON notas_fiscais_conta_azul(destinatario_id);
        CREATE INDEX IF NOT EXISTS idx_nf_status ON notas_fiscais_conta_azul(status);
        CREATE INDEX IF NOT EXISTS idx_nf_venda ON notas_fiscais_conta_azul(venda_id);
        CREATE INDEX IF NOT EXISTS idx_nf_itens_nota ON notas_fiscais_itens(nota_fiscal_id);
        """
        
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            print("Tabelas de notas fiscais criadas com sucesso!")
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_notas_fiscais_from_api(self, page=1, page_size=100):
        """Busca notas fiscais da API do Conta Azul"""
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
                f"{self.base_url}/v1/notas-fiscais",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro na API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro ao buscar notas fiscais da API: {e}")
            return None
    
    def insert_nota_fiscal(self, nf_data):
        """Insere uma nota fiscal no banco de dados"""
        insert_nf_sql = """
        INSERT INTO notas_fiscais_conta_azul (
            id, numero, serie, tipo, modelo, chave_acesso, data_emissao, data_vencimento, data_competencia,
            status, situacao, emitente_id, emitente_nome, emitente_cnpj, emitente_ie, emitente_endereco,
            destinatario_id, destinatario_nome, destinatario_cnpj, destinatario_cpf, destinatario_ie, destinatario_endereco,
            valor_total, valor_produtos, valor_servicos, valor_desconto, valor_frete, valor_seguro, valor_outras_despesas,
            valor_ipi, valor_icms, valor_pis, valor_cofins, valor_iss, valor_inss, valor_ir, valor_csll,
            natureza_operacao, cfop, municipio_prestacao_servico, codigo_municipio_prestacao,
            modalidade_frete, transportadora_id, transportadora_nome, peso_bruto, peso_liquido, volume,
            observacoes, informacoes_adicionais, venda_id
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id) DO UPDATE SET
            numero = EXCLUDED.numero,
            serie = EXCLUDED.serie,
            tipo = EXCLUDED.tipo,
            modelo = EXCLUDED.modelo,
            chave_acesso = EXCLUDED.chave_acesso,
            data_emissao = EXCLUDED.data_emissao,
            data_vencimento = EXCLUDED.data_vencimento,
            data_competencia = EXCLUDED.data_competencia,
            status = EXCLUDED.status,
            situacao = EXCLUDED.situacao,
            valor_total = EXCLUDED.valor_total,
            valor_produtos = EXCLUDED.valor_produtos,
            valor_servicos = EXCLUDED.valor_servicos,
            observacoes = EXCLUDED.observacoes,
            informacoes_adicionais = EXCLUDED.informacoes_adicionais,
            updated_at = CURRENT_TIMESTAMP
        """
        
        insert_item_sql = """
        INSERT INTO notas_fiscais_itens (
            id, nota_fiscal_id, produto_id, servico_id, codigo, descricao, quantidade, unidade,
            valor_unitario, valor_total, valor_desconto, ncm, cest, cfop, origem,
            icms_situacao_tributaria, icms_aliquota, icms_valor,
            ipi_situacao_tributaria, ipi_aliquota, ipi_valor,
            pis_situacao_tributaria, pis_aliquota, pis_valor,
            cofins_situacao_tributaria, cofins_aliquota, cofins_valor
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id) DO UPDATE SET
            quantidade = EXCLUDED.quantidade,
            valor_unitario = EXCLUDED.valor_unitario,
            valor_total = EXCLUDED.valor_total,
            valor_desconto = EXCLUDED.valor_desconto
        """
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Extrair dados da nota fiscal
            nf_id = nf_data.get('id')
            numero = nf_data.get('numero')
            serie = nf_data.get('serie')
            tipo = nf_data.get('tipo')
            modelo = nf_data.get('modelo')
            chave_acesso = nf_data.get('chave_acesso')
            data_emissao = nf_data.get('data_emissao')
            data_vencimento = nf_data.get('data_vencimento')
            data_competencia = nf_data.get('data_competencia')
            status = nf_data.get('status')
            situacao = nf_data.get('situacao')
            
            # Dados do emitente
            emitente = nf_data.get('emitente', {})
            emitente_id = emitente.get('id')
            emitente_nome = emitente.get('nome')
            emitente_cnpj = emitente.get('cnpj')
            emitente_ie = emitente.get('inscricao_estadual')
            emitente_endereco = json.dumps(emitente.get('endereco', {})) if emitente.get('endereco') else None
            
            # Dados do destinatário
            destinatario = nf_data.get('destinatario', {})
            destinatario_id = destinatario.get('id')
            destinatario_nome = destinatario.get('nome')
            destinatario_cnpj = destinatario.get('cnpj')
            destinatario_cpf = destinatario.get('cpf')
            destinatario_ie = destinatario.get('inscricao_estadual')
            destinatario_endereco = json.dumps(destinatario.get('endereco', {})) if destinatario.get('endereco') else None
            
            # Valores
            valores = nf_data.get('valores', {})
            valor_total = valores.get('total')
            valor_produtos = valores.get('produtos')
            valor_servicos = valores.get('servicos')
            valor_desconto = valores.get('desconto')
            valor_frete = valores.get('frete')
            valor_seguro = valores.get('seguro')
            valor_outras_despesas = valores.get('outras_despesas')
            
            # Impostos
            impostos = valores.get('impostos', {})
            valor_ipi = impostos.get('ipi')
            valor_icms = impostos.get('icms')
            valor_pis = impostos.get('pis')
            valor_cofins = impostos.get('cofins')
            valor_iss = impostos.get('iss')
            valor_inss = impostos.get('inss')
            valor_ir = impostos.get('ir')
            valor_csll = impostos.get('csll')
            
            # Informações fiscais
            natureza_operacao = nf_data.get('natureza_operacao')
            cfop = nf_data.get('cfop')
            municipio_prestacao_servico = nf_data.get('municipio_prestacao_servico')
            codigo_municipio_prestacao = nf_data.get('codigo_municipio_prestacao')
            
            # Transporte
            transporte = nf_data.get('transporte', {})
            modalidade_frete = transporte.get('modalidade_frete')
            transportadora = transporte.get('transportadora', {})
            transportadora_id = transportadora.get('id')
            transportadora_nome = transportadora.get('nome')
            peso_bruto = transporte.get('peso_bruto')
            peso_liquido = transporte.get('peso_liquido')
            volume = transporte.get('volume')
            
            # Outros
            observacoes = nf_data.get('observacoes')
            informacoes_adicionais = nf_data.get('informacoes_adicionais')
            venda_id = nf_data.get('venda_id')
            
            # Inserir nota fiscal
            cursor.execute(insert_nf_sql, (
                nf_id, numero, serie, tipo, modelo, chave_acesso, data_emissao, data_vencimento, data_competencia,
                status, situacao, emitente_id, emitente_nome, emitente_cnpj, emitente_ie, emitente_endereco,
                destinatario_id, destinatario_nome, destinatario_cnpj, destinatario_cpf, destinatario_ie, destinatario_endereco,
                valor_total, valor_produtos, valor_servicos, valor_desconto, valor_frete, valor_seguro, valor_outras_despesas,
                valor_ipi, valor_icms, valor_pis, valor_cofins, valor_iss, valor_inss, valor_ir, valor_csll,
                natureza_operacao, cfop, municipio_prestacao_servico, codigo_municipio_prestacao,
                modalidade_frete, transportadora_id, transportadora_nome, peso_bruto, peso_liquido, volume,
                observacoes, informacoes_adicionais, venda_id
            ))
            
            # Inserir itens da nota fiscal
            itens = nf_data.get('itens', [])
            for i, item in enumerate(itens):
                item_id = f"{nf_id}_{i+1}"
                
                # Dados do item
                produto_id = item.get('produto_id')
                servico_id = item.get('servico_id')
                codigo = item.get('codigo')
                descricao = item.get('descricao')
                quantidade = item.get('quantidade')
                unidade = item.get('unidade')
                valor_unitario = item.get('valor_unitario')
                valor_total_item = item.get('valor_total')
                valor_desconto_item = item.get('valor_desconto')
                
                # Informações fiscais
                ncm = item.get('ncm')
                cest = item.get('cest')
                cfop_item = item.get('cfop')
                origem = item.get('origem')
                
                # Impostos do item
                impostos_item = item.get('impostos', {})
                
                icms = impostos_item.get('icms', {})
                icms_situacao = icms.get('situacao_tributaria')
                icms_aliquota = icms.get('aliquota')
                icms_valor = icms.get('valor')
                
                ipi = impostos_item.get('ipi', {})
                ipi_situacao = ipi.get('situacao_tributaria')
                ipi_aliquota = ipi.get('aliquota')
                ipi_valor = ipi.get('valor')
                
                pis = impostos_item.get('pis', {})
                pis_situacao = pis.get('situacao_tributaria')
                pis_aliquota = pis.get('aliquota')
                pis_valor = pis.get('valor')
                
                cofins = impostos_item.get('cofins', {})
                cofins_situacao = cofins.get('situacao_tributaria')
                cofins_aliquota = cofins.get('aliquota')
                cofins_valor = cofins.get('valor')
                
                cursor.execute(insert_item_sql, (
                    item_id, nf_id, produto_id, servico_id, codigo, descricao, quantidade, unidade,
                    valor_unitario, valor_total_item, valor_desconto_item, ncm, cest, cfop_item, origem,
                    icms_situacao, icms_aliquota, icms_valor,
                    ipi_situacao, ipi_aliquota, ipi_valor,
                    pis_situacao, pis_aliquota, pis_valor,
                    cofins_situacao, cofins_aliquota, cofins_valor
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao inserir nota fiscal {nf_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def sync_notas_fiscais(self):
        """Sincroniza todas as notas fiscais da API com o banco de dados"""
        print("Iniciando sincronização de notas fiscais...")
        
        # Criar tabelas se não existirem
        self.create_notas_fiscais_table()
        
        page = 1
        total_notas = 0
        
        while True:
            print(f"Buscando página {page}...")
            
            notas_response = self.get_notas_fiscais_from_api(page=page)
            
            if not notas_response:
                break
            
            notas = notas_response.get('itens', [])
            
            if not notas:
                break
            
            for nota in notas:
                if self.insert_nota_fiscal(nota):
                    total_notas += 1
            
            # Verificar se há mais páginas
            paginacao = notas_response.get('paginacao', {})
            if page >= paginacao.get('total_paginas', 1):
                break
            
            page += 1
        
        print(f"Sincronização concluída! Total de notas fiscais processadas: {total_notas}")

if __name__ == "__main__":
    sync = ContaAzulNotasFiscaisSync()
    sync.sync_notas_fiscais()