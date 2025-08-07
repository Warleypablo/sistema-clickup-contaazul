# Deploy no Render.com - Sistema ClickUp + Conta Azul

## 📋 Pré-requisitos

1. Conta no [Render.com](https://render.com) (gratuita)
2. Repositório Git (GitHub, GitLab ou Bitbucket)
3. Código fonte commitado no repositório

## 🚀 Passo a Passo para Deploy

### 1. Preparar o Repositório Git

```bash
# Inicializar repositório (se ainda não foi feito)
git init

# Adicionar todos os arquivos
git add .

# Fazer commit
git commit -m "Deploy inicial - Sistema ClickUp + Conta Azul"

# Adicionar repositório remoto (substitua pela sua URL)
git remote add origin https://github.com/SEU_USUARIO/API_CONTAAZUL-Conexao.git

# Enviar para o repositório
git push -u origin main
```

### 2. Criar Banco de Dados no Render

1. Acesse [Render Dashboard](https://dashboard.render.com)
2. Clique em **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `sistema-clickup-db`
   - **Database**: `sistema_clickup`
   - **User**: `sistema_user`
   - **Region**: `Oregon (US West)`
   - **Plan**: `Free`
4. Clique em **"Create Database"**
5. **IMPORTANTE**: Anote a **External Database URL** (será usada depois)

### 3. Criar Web Service no Render

1. No Dashboard, clique em **"New +"** → **"Web Service"**
2. Conecte seu repositório Git
3. Configure:
   - **Name**: `sistema-clickup-contaazul`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: `Free`

### 4. Configurar Variáveis de Ambiente

Na seção **Environment Variables**, adicione:

```
FLASK_ENV=production
DATABASE_URL=[Cole aqui a External Database URL do passo 2]
```

### 5. Deploy

1. Clique em **"Create Web Service"**
2. O Render fará o deploy automaticamente
3. Aguarde alguns minutos até aparecer "Live" no status
4. Sua aplicação estará disponível em: `https://sistema-clickup-contaazul.onrender.com`

## 🔧 Configuração do Banco de Dados

Após o primeiro deploy, você precisará popular o banco com seus dados:

1. Use um cliente PostgreSQL (como pgAdmin ou DBeaver)
2. Conecte usando a External Database URL
3. Execute seus scripts de criação de tabelas e inserção de dados

## 📝 Notas Importantes

- **Hibernação**: No plano gratuito, a aplicação hiberna após 15 minutos de inatividade
- **Limitações**: 750 horas/mês no plano gratuito
- **SSL**: Certificado SSL automático incluído
- **Domínio**: Você pode configurar um domínio personalizado

## 🔄 Atualizações

Para atualizar a aplicação:

```bash
git add .
git commit -m "Descrição da atualização"
git push
```

O Render fará o redeploy automaticamente.

## 🆘 Troubleshooting

- **Erro de build**: Verifique o arquivo `requirements.txt`
- **Erro de conexão DB**: Verifique a variável `DATABASE_URL`
- **Aplicação não inicia**: Verifique os logs no Dashboard do Render

## 📞 Suporte

Se precisar de ajuda, verifique:
- [Documentação do Render](https://render.com/docs)
- Logs da aplicação no Dashboard
- Status do banco de dados no Dashboard