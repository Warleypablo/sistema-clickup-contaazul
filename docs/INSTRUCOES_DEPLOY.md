# Instruções para Deploy no Render.com

## ⚠️ Pré-requisito: Instalar Git

O Git não foi encontrado no seu sistema. Para fazer o deploy, você precisa instalar o Git primeiro:

### Instalação do Git no Windows:

1. **Baixe o Git:**
   - Acesse: https://git-scm.com/download/win
   - Baixe a versão mais recente

2. **Instale o Git:**
   - Execute o arquivo baixado
   - Use as configurações padrão (Next, Next, Next...)
   - **IMPORTANTE:** Marque a opção "Git from the command line and also from 3rd-party software"

3. **Reinicie o PowerShell/Terminal** após a instalação

4. **Teste a instalação:**
   ```powershell
   git --version
   ```

## Opção 1: Deploy Automático (Após instalar Git)

Após instalar o Git, execute:
```powershell
.\deploy_render.ps1
```

## Opção 2: Deploy Manual (Sem Git)

Se preferir não instalar o Git agora, você pode fazer o deploy manual:

### Passo 1: Criar conta no Render.com
1. Acesse https://render.com
2. Clique em "Get Started for Free"
3. Crie sua conta (pode usar GitHub, Google ou email)

### Passo 2: Preparar o código
1. **Compacte todos os arquivos** do projeto em um arquivo ZIP
2. **Exclua** a pasta `.env` se existir (dados sensíveis)
3. **Inclua** todos estes arquivos:
   - `app.py`
   - `requirements.txt`
   - `Procfile`
   - `render.yaml`
   - `templates/` (pasta)
   - `.env.example`
   - `check_db.py`

### Passo 3: Criar Banco de Dados PostgreSQL
1. No painel do Render, clique em "New +"
2. Selecione "PostgreSQL"
3. Configure:
   - **Name:** `sistema-clickup-db`
   - **Database:** `sistema_clickup`
   - **User:** `sistema_user`
   - **Region:** Oregon (US West)
   - **Plan:** Free
4. Clique em "Create Database"
5. **IMPORTANTE:** Copie a "External Database URL" (você vai precisar)

### Passo 4: Fazer Upload do Código
1. Crie um repositório no GitHub:
   - Acesse https://github.com
   - Clique em "New repository"
   - Nome: `sistema-clickup-contaazul`
   - Marque "Public" (para plano gratuito)
   - Clique "Create repository"

2. Faça upload dos arquivos:
   - Clique em "uploading an existing file"
   - Arraste todos os arquivos do projeto
   - **NÃO inclua** arquivos `.env`
   - Commit: "Deploy inicial - Sistema ClickUp + Conta Azul"

### Passo 5: Criar Web Service no Render
1. No painel do Render, clique em "New +"
2. Selecione "Web Service"
3. Conecte seu repositório GitHub
4. Configure:
   - **Name:** `sistema-clickup-contaazul`
   - **Region:** Oregon (US West)
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free

### Passo 6: Configurar Variáveis de Ambiente
1. Na página do seu Web Service, vá para "Environment"
2. Adicione estas variáveis:
   ```
   FLASK_ENV=production
   DATABASE_URL=[Cole aqui a URL do banco PostgreSQL do Passo 3]
   ```

### Passo 7: Deploy
1. Clique em "Create Web Service"
2. Aguarde o build (pode levar alguns minutos)
3. Sua aplicação estará disponível em: `https://sistema-clickup-contaazul.onrender.com`

## Configuração do Banco de Dados

Após o deploy, você precisa configurar o banco:

1. **Teste a conexão:**
   - Acesse: `https://sua-app.onrender.com/check-db`
   - Ou execute localmente: `python check_db.py`

2. **Importe seus dados:**
   - Use um cliente PostgreSQL (como pgAdmin)
   - Conecte usando a URL do banco
   - Importe suas tabelas e dados

## Limitações do Plano Gratuito

- **750 horas/mês** de uso
- **Suspensão após 15 minutos** de inatividade
- **Inicialização lenta** após suspensão (30-60 segundos)
- **500MB** de armazenamento no banco

## Atualizações Futuras

Para atualizar a aplicação:
1. Modifique os arquivos localmente
2. Faça upload no GitHub (substitua os arquivos)
3. O Render fará deploy automaticamente

## Suporte

Se tiver problemas:
1. Verifique os logs no painel do Render
2. Consulte: https://render.com/docs
3. Use o arquivo `check_db.py` para testar conexões

---

**Próximo passo recomendado:** Instalar Git e usar o script automático `deploy_render.ps1`