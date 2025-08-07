import requests
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Carregar variáveis de ambiente
load_dotenv()

class ContaAzulProdutosSync:
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
        
    def create_produtos_table(self):
        """Cria a tabela de produtos no banco de dados"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS produtos_conta_azul (
            id VARCHAR(50) PRIMARY KEY,
            codigo VARCHAR(100),
            descricao VARCHAR(500),
            nome VARCHAR(255),
            tipo VARCHAR(50),
            status VARCHAR(20),
            unidade_medida VARCHAR(10),
            preco_venda DECIMAL(15,2),
            preco_custo DECIMAL(15,2),
            preco_compra DECIMAL(15,2),
            margem_lucro DECIMAL(5,2),
            categoria_id VARCHAR(50),
            categoria_nome VARCHAR(255),
            subcategoria_id VARCHAR(50),
            subcategoria_nome VARCHAR(255),
            marca VARCHAR(255),
            modelo VARCHAR(255),
            peso_bruto DECIMAL(10,3),
            peso_liquido DECIMAL(10,3),
            altura DECIMAL(10,3),
            largura DECIMAL(10,3),
            profundidade DECIMAL(10,3),
            codigo_barras VARCHAR(50),
            codigo_ncm VARCHAR(20),
            origem INTEGER,
            cest VARCHAR(20),
            controla_estoque BOOLEAN DEFAULT FALSE,
            estoque_atual DECIMAL(15,3),
            estoque_minimo DECIMAL(15,3),
            estoque_maximo DECIMAL(15,3),
            localizacao VARCHAR(255),
            observacoes TEXT,
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_produtos_codigo ON produtos_conta_azul(codigo);
        CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos_conta_azul(categoria_id);
        CREATE INDEX IF NOT EXISTS idx_produtos_status ON produtos_conta_azul(status);
        CREATE INDEX IF NOT EXISTS idx_produtos_codigo_barras ON produtos_conta_azul(codigo_barras);
        """
        
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            print("Tabela de produtos criada com sucesso!")
        except Exception as e:
            print(f"Erro ao criar tabela: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_produtos(self, page=1, page_size=50):
        """Busca produtos da API do Conta Azul"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Buscar todos os produtos usando paginação real da API
            if not hasattr(self, '_all_produtos_loaded'):
                print("Carregando todos os produtos da API...")
                all_products = []
                produtos_ids = set()
                api_page = 1
                
                while True:
                    response = requests.get(
                        f"{self.base_url}/v1/produtos?page={api_page}",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('items', [])
                        if not items:
                            break
                        
                        # Verificar se há produtos duplicados (problema de paginação da API)
                        novos_produtos = []
                        produtos_duplicados = 0
                        
                        for item in items:
                            produto_id = item.get('id')
                            if produto_id not in produtos_ids:
                                produtos_ids.add(produto_id)
                                novos_produtos.append(item)
                            else:
                                produtos_duplicados += 1
                        
                        if novos_produtos:
                            all_products.extend(novos_produtos)
                            print(f"Página {api_page}: {len(novos_produtos)} produtos novos carregados")
                            if produtos_duplicados > 0:
                                print(f"   ({produtos_duplicados} produtos duplicados ignorados)")
                        else:
                            print(f"Página {api_page}: Todos os produtos já foram carregados (paginação não funcional)")
                            break
                        
                        api_page += 1
                        
                        # Limite de segurança para evitar loop infinito
                        if api_page > 100:
                            print("Limite de páginas atingido (100)")
                            break
                        
                        # Se retornou menos de 10 produtos novos, provavelmente é a última página
                        if len(novos_produtos) < 10:
                            print(f"Última página detectada (apenas {len(novos_produtos)} produtos novos)")
                            break
                    else:
                        print(f"Erro na API página {api_page}: {response.status_code} - {response.text}")
                        break
                
                self._all_produtos = all_products
                self._total_produtos = len(all_products)
                self._all_produtos_loaded = True
                print(f"Total de produtos únicos carregados: {len(all_products)}")
            
            # Paginar localmente os produtos já carregados
            if hasattr(self, '_all_produtos'):
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_items = self._all_produtos[start_idx:end_idx]
                
                return {
                    'itens': paginated_items,
                    'paginacao': {
                        'pagina_atual': page,
                        'tamanho_pagina': len(paginated_items),
                        'total_itens': len(self._all_produtos),
                        'total_paginas': (len(self._all_produtos) + page_size - 1) // page_size
                    }
                }
            
            return None
                
        except Exception as e:
            print(f"Erro ao buscar produtos da API: {e}")
            return None
    
    def insert_produto(self, produto_data):
        """Insere um produto no banco de dados"""
        insert_sql = """
        INSERT INTO produtos_conta_azul (
            id, codigo, descricao, nome, tipo, status, unidade_medida, preco_venda, preco_custo, preco_compra,
            margem_lucro, categoria_id, categoria_nome, subcategoria_id, subcategoria_nome, marca, modelo,
            peso_bruto, peso_liquido, altura, largura, profundidade, codigo_barras, codigo_ncm, origem, cest,
            controla_estoque, estoque_atual, estoque_minimo, estoque_maximo, localizacao, observacoes, ativo
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id) DO UPDATE SET
            codigo = EXCLUDED.codigo,
            descricao = EXCLUDED.descricao,
            nome = EXCLUDED.nome,
            tipo = EXCLUDED.tipo,
            status = EXCLUDED.status,
            unidade_medida = EXCLUDED.unidade_medida,
            preco_venda = EXCLUDED.preco_venda,
            preco_custo = EXCLUDED.preco_custo,
            preco_compra = EXCLUDED.preco_compra,
            margem_lucro = EXCLUDED.margem_lucro,
            categoria_id = EXCLUDED.categoria_id,
            categoria_nome = EXCLUDED.categoria_nome,
            subcategoria_id = EXCLUDED.subcategoria_id,
            subcategoria_nome = EXCLUDED.subcategoria_nome,
            marca = EXCLUDED.marca,
            modelo = EXCLUDED.modelo,
            peso_bruto = EXCLUDED.peso_bruto,
            peso_liquido = EXCLUDED.peso_liquido,
            altura = EXCLUDED.altura,
            largura = EXCLUDED.largura,
            profundidade = EXCLUDED.profundidade,
            codigo_barras = EXCLUDED.codigo_barras,
            codigo_ncm = EXCLUDED.codigo_ncm,
            origem = EXCLUDED.origem,
            cest = EXCLUDED.cest,
            controla_estoque = EXCLUDED.controla_estoque,
            estoque_atual = EXCLUDED.estoque_atual,
            estoque_minimo = EXCLUDED.estoque_minimo,
            estoque_maximo = EXCLUDED.estoque_maximo,
            localizacao = EXCLUDED.localizacao,
            observacoes = EXCLUDED.observacoes,
            ativo = EXCLUDED.ativo,
            updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Extrair dados do produto (mapeando campos da API v2)
            produto_id = produto_data.get('id')
            codigo = produto_data.get('código')  # API usa 'código' com acento
            descricao = produto_data.get('descricao')  # Pode não existir
            nome = produto_data.get('nome')
            tipo = produto_data.get('tipo')
            status = produto_data.get('status')
            unidade_medida = produto_data.get('unidade_medida')  # Pode não existir
            
            # Preços (mapeando campos reais da API)
            preco_venda = produto_data.get('valor_venda')  # API usa 'valor_venda'
            preco_custo = produto_data.get('custo_medio')  # API usa 'custo_medio'
            preco_compra = produto_data.get('preco_compra')  # Pode não existir
            margem_lucro = produto_data.get('margem_lucro')  # Pode não existir
            
            # Categoria (pode não existir na API v2)
            categoria = produto_data.get('categoria', {})
            categoria_id = categoria.get('id') if categoria else None
            categoria_nome = categoria.get('nome') if categoria else None
            
            # Subcategoria (pode não existir na API v2)
            subcategoria = produto_data.get('subcategoria', {})
            subcategoria_id = subcategoria.get('id') if subcategoria else None
            subcategoria_nome = subcategoria.get('nome') if subcategoria else None
            
            # Características físicas (podem não existir)
            marca = produto_data.get('marca')
            modelo = produto_data.get('modelo')
            peso_bruto = produto_data.get('peso_bruto')
            peso_liquido = produto_data.get('peso_liquido')
            
            # Dimensões (podem não existir)
            dimensoes = produto_data.get('dimensoes', {})
            altura = dimensoes.get('altura') if dimensoes else None
            largura = dimensoes.get('largura') if dimensoes else None
            profundidade = dimensoes.get('profundidade') if dimensoes else None
            
            # Códigos
            codigo_barras = produto_data.get('ean')  # API usa 'ean'
            codigo_ncm = produto_data.get('codigo_ncm')
            origem = produto_data.get('origem')
            cest = produto_data.get('cest')
            
            # Estoque (mapeando campos reais)
            controla_estoque = produto_data.get('controla_estoque', False)
            estoque_atual = produto_data.get('saldo')  # API usa 'saldo'
            estoque_minimo = produto_data.get('estoque_minimo')
            estoque_maximo = produto_data.get('estoque_maximo')
            localizacao = produto_data.get('localizacao')
            
            # Outros
            observacoes = produto_data.get('observacoes')
            ativo = produto_data.get('status') == 'ATIVO'  # Derivar de status
            
            cursor.execute(insert_sql, (
                produto_id, codigo, descricao, nome, tipo, status, unidade_medida, preco_venda, preco_custo, preco_compra,
                margem_lucro, categoria_id, categoria_nome, subcategoria_id, subcategoria_nome, marca, modelo,
                peso_bruto, peso_liquido, altura, largura, profundidade, codigo_barras, codigo_ncm, origem, cest,
                controla_estoque, estoque_atual, estoque_minimo, estoque_maximo, localizacao, observacoes, ativo
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao inserir produto {produto_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def sync_produtos(self):
        """Sincroniza todos os produtos da API com o banco de dados"""
        print("Iniciando sincronização de produtos...")
        
        # Criar tabela se não existir
        self.create_produtos_table()
        
        page = 1
        total_produtos = 0
        
        while True:
            print(f"Buscando página {page}...")
            
            produtos_response = self.get_produtos(page=page)
            
            if not produtos_response:
                break
            
            produtos = produtos_response.get('itens', [])
            
            if not produtos:
                break
            
            for produto in produtos:
                if self.insert_produto(produto):
                    total_produtos += 1
            
            # Verificar se há mais páginas
            paginacao = produtos_response.get('paginacao', {})
            if page >= paginacao.get('total_paginas', 1):
                break
            
            page += 1
        
        print(f"Sincronização concluída! Total de produtos processados: {total_produtos}")

if __name__ == "__main__":
    sync = ContaAzulProdutosSync()
    sync.sync_produtos()