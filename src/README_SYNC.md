# Sincronização de Dados - Conta Azul API

Este conjunto de scripts permite sincronizar dados da API do Conta Azul com o banco de dados PostgreSQL local.

## Scripts Disponíveis

### 1. `sync_vendas.py`
Sincroniza dados de vendas da API do Conta Azul.

**Tabela criada:** `vendas_conta_azul`

**Campos principais:**
- ID da venda
- Número da venda
- Data de emissão
- Status
- Cliente (ID, nome, CNPJ/CPF)
- Valores (total, produtos, serviços, descontos)
- Observações

### 2. `sync_produtos.py`
Sincroniza dados de produtos da API do Conta Azul.

**Tabela criada:** `produtos_conta_azul`

**Campos principais:**
- ID do produto
- Código
- Descrição
- Preço de venda
- Preço de custo
- Categoria
- Unidade de medida
- Estoque atual
- Informações fiscais (NCM, CEST, origem)

### 3. `sync_servicos.py`
Sincroniza dados de serviços da API do Conta Azul.

**Tabelas criadas:**
- `servicos_conta_azul` - Dados principais dos serviços
- `servicos_cenarios_tributarios` - Cenários tributários dos serviços

**Campos principais:**
- ID do serviço
- Código
- Descrição
- Preço
- Categoria
- Informações fiscais
- Cenários tributários

### 4. `sync_notas_fiscais.py`
Sincroniza dados de notas fiscais da API do Conta Azul.

**Tabelas criadas:**
- `notas_fiscais_conta_azul` - Dados principais das notas fiscais
- `notas_fiscais_itens` - Itens das notas fiscais

**Campos principais:**
- Número e série da nota
- Chave de acesso
- Dados do emitente e destinatário
- Valores e impostos
- Informações de transporte
- Itens detalhados

### 5. `sync_all.py`
Script principal que executa todas as sincronizações em sequência.

## Configuração

### 1. Variáveis de Ambiente
Configure as seguintes variáveis no arquivo `.env`:

```env
# Conta Azul API
CONTA_AZUL_ACCESS_TOKEN=seu_token_aqui

# PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_DBNAME=nome_do_banco
PG_USER=usuario
PG_PASSWORD=senha
```

### 2. Dependências
Instale as dependências necessárias:

```bash
pip install requests psycopg2-binary python-dotenv
```

## Como Usar

### Execução Completa
Para sincronizar todos os dados:

```bash
python sync_all.py
```

### Execução Individual
Para sincronizar apenas um tipo de dado:

```bash
# Sincronizar apenas vendas
python sync_all.py vendas

# Sincronizar apenas produtos
python sync_all.py produtos

# Sincronizar apenas serviços
python sync_all.py servicos

# Sincronizar apenas notas fiscais
python sync_all.py notas_fiscais
```

### Execução Direta
Também é possível executar cada script individualmente:

```bash
python sync_vendas.py
python sync_produtos.py
python sync_servicos.py
python sync_notas_fiscais.py
```

## Funcionalidades

### ✅ Criação Automática de Tabelas
- Os scripts criam automaticamente as tabelas necessárias
- Índices são criados para otimizar consultas
- Relacionamentos entre tabelas são estabelecidos

### ✅ Sincronização Incremental
- Utiliza `ON CONFLICT` para atualizar registros existentes
- Evita duplicação de dados
- Mantém histórico de criação e atualização

### ✅ Paginação Automática
- Processa todos os registros da API
- Controla automaticamente a paginação
- Otimiza o uso de memória

### ✅ Tratamento de Erros
- Logs detalhados de erros
- Continua processamento mesmo com falhas pontuais
- Relatório final de sucessos e falhas

### ✅ Flexibilidade
- Execução completa ou individual
- Configuração via variáveis de ambiente
- Fácil integração com outros sistemas

## Estrutura dos Dados

### Relacionamentos
- `vendas_conta_azul.cliente_id` → Cliente da venda
- `notas_fiscais_conta_azul.venda_id` → `vendas_conta_azul.id`
- `notas_fiscais_itens.nota_fiscal_id` → `notas_fiscais_conta_azul.id`
- `notas_fiscais_itens.produto_id` → `produtos_conta_azul.id`
- `notas_fiscais_itens.servico_id` → `servicos_conta_azul.id`

### Índices Criados
- Índices em campos de busca frequente (ID, número, data, status)
- Índices em chaves estrangeiras para otimizar JOINs
- Índices compostos para consultas complexas

## Monitoramento

### Logs
Todos os scripts geram logs detalhados:
- Início e fim de cada sincronização
- Número de registros processados
- Erros encontrados
- Tempo de execução

### Verificação de Dados
Após a sincronização, você pode verificar os dados:

```sql
-- Contar registros por tabela
SELECT 'vendas' as tabela, COUNT(*) as total FROM vendas_conta_azul
UNION ALL
SELECT 'produtos', COUNT(*) FROM produtos_conta_azul
UNION ALL
SELECT 'servicos', COUNT(*) FROM servicos_conta_azul
UNION ALL
SELECT 'notas_fiscais', COUNT(*) FROM notas_fiscais_conta_azul;

-- Verificar últimas atualizações
SELECT MAX(updated_at) as ultima_atualizacao FROM vendas_conta_azul;
```

## Agendamento

Para automatizar a sincronização, você pode:

### Windows (Task Scheduler)
1. Criar uma tarefa agendada
2. Executar: `python C:\caminho\para\sync_all.py`
3. Definir frequência (diária, semanal, etc.)

### Linux/Mac (Cron)
```bash
# Executar diariamente às 2h da manhã
0 2 * * * cd /caminho/para/scripts && python sync_all.py
```

## Troubleshooting

### Erro de Conexão com API
- Verifique se o token está correto
- Confirme se o token não expirou
- Teste a conectividade com a API

### Erro de Conexão com Banco
- Verifique as credenciais do PostgreSQL
- Confirme se o banco está rodando
- Teste a conectividade

### Erro de Permissões
- Verifique se o usuário tem permissão para criar tabelas
- Confirme permissões de INSERT/UPDATE

### Performance
- Para grandes volumes, considere executar em horários de menor uso
- Monitore o uso de CPU e memória
- Ajuste o tamanho das páginas se necessário

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs de erro
2. Consulte a documentação da API do Conta Azul
3. Teste a conectividade com banco e API
4. Verifique as configurações do `.env`