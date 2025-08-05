#!/bin/bash
# Script para facilitar o deploy no Heroku

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Verificar se o Heroku CLI está instalado
if ! command -v heroku &> /dev/null; then
    echo -e "${RED}Heroku CLI não encontrado. Por favor, instale-o primeiro:${NC}"
    echo -e "${YELLOW}https://devcenter.heroku.com/articles/heroku-cli${NC}"
    exit 1
fi

# Verificar se o Git está instalado
if ! command -v git &> /dev/null; then
    echo -e "${RED}Git não encontrado. Por favor, instale-o primeiro:${NC}"
    echo -e "${YELLOW}https://git-scm.com/downloads${NC}"
    exit 1
fi

# Verificar se já existe um repositório Git
if [ ! -d ".git" ]; then
    echo -e "${CYAN}Inicializando repositório Git...${NC}"
    git init
fi

# Verificar login no Heroku
echo -e "${CYAN}Verificando login no Heroku...${NC}"
heroku whoami &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Por favor, faça login no Heroku:${NC}"
    heroku login
fi

# Solicitar nome da aplicação
echo -e "${CYAN}Digite o nome da sua aplicação no Heroku (deixe em branco para gerar um nome aleatório):${NC}"
read app_name

# Criar aplicação no Heroku
if [ -z "$app_name" ]; then
    echo -e "${CYAN}Criando aplicação no Heroku com nome aleatório...${NC}"
    heroku create
else
    echo -e "${CYAN}Criando aplicação '$app_name' no Heroku...${NC}"
    heroku create "$app_name"
fi

# Adicionar add-on do PostgreSQL
echo -e "${CYAN}Adicionando banco de dados PostgreSQL...${NC}"
heroku addons:create heroku-postgresql:hobby-dev

# Configurar variáveis de ambiente
echo -e "${CYAN}Configurando variáveis de ambiente...${NC}"
heroku config:set FLASK_ENV=production

# Perguntar se deseja usar banco de dados externo
echo -e "${CYAN}Deseja usar um banco de dados PostgreSQL externo? (S/N)${NC}"
read use_external_db
if [[ "$use_external_db" == "S" || "$use_external_db" == "s" ]]; then
    echo -e "${CYAN}Digite o host do PostgreSQL:${NC}"
    read pg_host
    
    echo -e "${CYAN}Digite a porta do PostgreSQL (padrão: 5432):${NC}"
    read pg_port
    if [ -z "$pg_port" ]; then pg_port="5432"; fi
    
    echo -e "${CYAN}Digite o nome do banco de dados:${NC}"
    read pg_dbname
    
    echo -e "${CYAN}Digite o usuário do PostgreSQL:${NC}"
    read pg_user
    
    echo -e "${CYAN}Digite a senha do PostgreSQL:${NC}"
    read -s pg_password
    echo ""
    
    heroku config:set PG_HOST="$pg_host"
    heroku config:set PG_PORT="$pg_port"
    heroku config:set PG_DBNAME="$pg_dbname"
    heroku config:set PG_USER="$pg_user"
    heroku config:set PG_PASSWORD="$pg_password"
fi

# Adicionar arquivos ao Git
echo -e "${CYAN}Adicionando arquivos ao Git...${NC}"
git add .

# Commit
echo -e "${CYAN}Digite a mensagem de commit (padrão: 'Versão inicial para deploy'):${NC}"
read commit_message
if [ -z "$commit_message" ]; then commit_message="Versão inicial para deploy"; fi

git commit -m "$commit_message"

# Push para o Heroku
echo -e "${CYAN}Enviando aplicação para o Heroku...${NC}"
git push heroku master

# Inicializar banco de dados
echo -e "${CYAN}Inicializando banco de dados...${NC}"
heroku run python init_db.py

# Abrir aplicação no navegador
echo -e "${CYAN}Abrindo aplicação no navegador...${NC}"
heroku open

echo -e "${GREEN}Deploy concluído com sucesso!${NC}"
if [ -z "$app_name" ]; then
    app_url=$(heroku info -s | grep web_url | cut -d= -f2 | sed 's/https:\/\///')
else
    app_url="$app_name.herokuapp.com"
fi
echo -e "${GREEN}Sua aplicação está disponível em: https://$app_url${NC}"