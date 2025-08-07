# Próximos Passos - Configurar GitHub e Deploy

## ✅ Status Atual
- ✅ Git instalado e funcionando
- ✅ Commit realizado com sucesso
- ⏳ Falta: Conectar ao repositório remoto (GitHub)

## Passo 1: Criar Repositório no GitHub

### 1.1 Acessar GitHub
1. Acesse: https://github.com
2. Faça login (ou crie conta se não tiver)

### 1.2 Criar Novo Repositório
1. Clique no botão **"+"** no canto superior direito
2. Selecione **"New repository"**
3. Configure:
   - **Repository name:** `sistema-clickup-contaazul`
   - **Description:** `Sistema de integração ClickUp + Conta Azul`
   - **Visibility:** ✅ Public (necessário para plano gratuito do Render)
   - **NÃO marque** "Add a README file"
   - **NÃO marque** "Add .gitignore"
   - **NÃO marque** "Choose a license"
4. Clique em **"Create repository"**

### 1.3 Copiar URL do Repositório
Após criar, você verá uma página com comandos. **Copie a URL** que aparece assim:
```
https://github.com/SEU_USUARIO/sistema-clickup-contaazul.git
```

## Passo 2: Conectar Projeto ao GitHub

No PowerShell (na pasta do projeto), execute estes comandos:

### 2.1 Adicionar Remote
```powershell
git remote add origin https://github.com/SEU_USUARIO/sistema-clickup-contaazul.git
```
**⚠️ SUBSTITUA** `SEU_USUARIO` pelo seu nome de usuário do GitHub!

### 2.2 Renomear Branch (se necessário)
```powershell
git branch -M main
```

### 2.3 Enviar Código
```powershell
git push -u origin main
```

**Nota:** Pode pedir login do GitHub. Use seu usuário e senha (ou token).

## Passo 3: Verificar Upload
1. Atualize a página do seu repositório no GitHub
2. Você deve ver todos os arquivos do projeto
3. ✅ Sucesso! Código está no GitHub

## Passo 4: Deploy no Render.com

Agora que o código está no GitHub:

### 4.1 Criar Conta no Render
1. Acesse: https://render.com
2. Clique em **"Get Started for Free"**
3. **Conecte com GitHub** (recomendado)

### 4.2 Criar Banco PostgreSQL
1. No dashboard, clique **"New +"**
2. Selecione **"PostgreSQL"**
3. Configure:
   - **Name:** `sistema-clickup-db`
   - **Database:** `sistema_clickup`
   - **User:** `sistema_user`
   - **Region:** Oregon (US West)
   - **Plan:** Free
4. Clique **"Create Database"**
5. **⚠️ IMPORTANTE:** Copie a **"External Database URL"**

### 4.3 Criar Web Service
1. Clique **"New +"** novamente
2. Selecione **"Web Service"**
3. **Conecte seu repositório GitHub**
4. Selecione: `sistema-clickup-contaazul`
5. Configure:
   - **Name:** `sistema-clickup-contaazul`
   - **Region:** Oregon (US West)
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free

### 4.4 Configurar Variáveis de Ambiente
1. Na seção **"Environment Variables"**
2. Adicione:
   ```
   FLASK_ENV=production
   DATABASE_URL=[Cole aqui a URL do banco PostgreSQL]
   ```

### 4.5 Deploy
1. Clique **"Create Web Service"**
2. Aguarde o build (3-5 minutos)
3. ✅ Aplicação estará em: `https://sistema-clickup-contaazul.onrender.com`

## Comandos Resumidos

Para facilitar, aqui estão os comandos que você precisa executar:

```powershell
# 1. Adicionar remote (SUBSTITUA a URL pela sua)
git remote add origin https://github.com/SEU_USUARIO/sistema-clickup-contaazul.git

# 2. Renomear branch
git branch -M main

# 3. Enviar código
git push -u origin main
```

## Próximo Passo Imediato

**👉 AGORA:** Crie o repositório no GitHub e execute os comandos acima!

Depois disso, siga para o Render.com conforme as instruções.