# Script de Deploy para Render.com
# Execute este script no PowerShell para preparar o deploy

Write-Host "Preparando deploy para Render.com..." -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

# Verificar se estamos em um repositorio Git
if (-not (Test-Path ".git")) {
    Write-Host "Este diretorio nao e um repositorio Git!" -ForegroundColor Red
    Write-Host "Inicializando repositorio Git..." -ForegroundColor Yellow
    git init
    Write-Host "Repositorio Git inicializado!" -ForegroundColor Green
}

# Verificar se os arquivos necessarios existem
$requiredFiles = @("requirements.txt", "app.py", "Procfile", "render.yaml")
$missingFiles = @()

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "Arquivos necessarios nao encontrados:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Todos os arquivos necessarios estao presentes!" -ForegroundColor Green

# Verificar se .env esta no .gitignore
if (Test-Path ".env") {
    $gitignoreContent = Get-Content ".gitignore" -ErrorAction SilentlyContinue
    if ($gitignoreContent -notcontains ".env") {
        Write-Host "ATENCAO: Arquivo .env nao esta no .gitignore!" -ForegroundColor Yellow
        Write-Host "Isso pode expor informacoes sensiveis!" -ForegroundColor Yellow
    } else {
        Write-Host "Arquivo .env esta protegido no .gitignore" -ForegroundColor Green
    }
}

# Adicionar todos os arquivos ao Git
Write-Host "Adicionando arquivos ao Git..." -ForegroundColor Cyan
git add .

# Verificar se ha mudancas para commit
$status = git status --porcelain
if ($status) {
    Write-Host "Fazendo commit das mudancas..." -ForegroundColor Cyan
    $commitMessage = Read-Host "Digite a mensagem do commit (ou pressione Enter para usar padrao)"
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
        $commitMessage = "Deploy: Sistema ClickUp + Conta Azul - $timestamp"
    }
    git commit -m "$commitMessage"
    Write-Host "Commit realizado!" -ForegroundColor Green
} else {
    Write-Host "Nenhuma mudanca para commit" -ForegroundColor Blue
}

# Verificar se ha remote configurado
$remotes = git remote
if (-not $remotes) {
    Write-Host "Nenhum repositorio remoto configurado!" -ForegroundColor Yellow
    Write-Host "Voce precisa:" -ForegroundColor Yellow
    Write-Host "1. Criar um repositorio no GitHub/GitLab/Bitbucket" -ForegroundColor Yellow
    Write-Host "2. Executar: git remote add origin <URL_DO_SEU_REPOSITORIO>" -ForegroundColor Yellow
    Write-Host "3. Executar: git push -u origin main" -ForegroundColor Yellow
} else {
    Write-Host "Enviando para repositorio remoto..." -ForegroundColor Cyan
    try {
        git push
        Write-Host "Codigo enviado para o repositorio!" -ForegroundColor Green
    } catch {
        Write-Host "Erro ao enviar codigo. Verifique sua conexao e permissoes." -ForegroundColor Red
        Write-Host "Tente: git push -u origin main" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Preparacao concluida!" -ForegroundColor Green
Write-Host "=" * 30 -ForegroundColor Green
Write-Host "Proximos passos:" -ForegroundColor Cyan
Write-Host "1. Acesse https://render.com e faca login" -ForegroundColor White
Write-Host "2. Siga as instrucoes no arquivo README_DEPLOY.md" -ForegroundColor White
Write-Host "3. Crie o banco PostgreSQL primeiro" -ForegroundColor White
Write-Host "4. Depois crie o Web Service" -ForegroundColor White
Write-Host "5. Configure as variaveis de ambiente" -ForegroundColor White
Write-Host ""
Write-Host "Documentacao completa: README_DEPLOY.md" -ForegroundColor Blue