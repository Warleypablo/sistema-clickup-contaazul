# Script PowerShell para facilitar o deploy no Heroku

# Verificar se o Heroku CLI está instalado
$herokuInstalled = $null
try {
    $herokuInstalled = Get-Command heroku -ErrorAction SilentlyContinue
} catch {}

if (-not $herokuInstalled) {
    Write-Host "Heroku CLI não encontrado. Por favor, instale-o primeiro:" -ForegroundColor Red
    Write-Host "https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Yellow
    exit 1
}

# Verificar se o Git está instalado
$gitInstalled = $null
try {
    $gitInstalled = Get-Command git -ErrorAction SilentlyContinue
} catch {}

if (-not $gitInstalled) {
    Write-Host "Git não encontrado. Por favor, instale-o primeiro:" -ForegroundColor Red
    Write-Host "https://git-scm.com/downloads" -ForegroundColor Yellow
    exit 1
}

# Verificar se já existe um repositório Git
$gitInitialized = Test-Path ".git"
if (-not $gitInitialized) {
    Write-Host "Inicializando repositório Git..." -ForegroundColor Cyan
    git init
}

# Verificar login no Heroku
Write-Host "Verificando login no Heroku..." -ForegroundColor Cyan
heroku whoami
if ($LASTEXITCODE -ne 0) {
    Write-Host "Por favor, faça login no Heroku:" -ForegroundColor Yellow
    heroku login
}

# Solicitar nome da aplicação
$appName = Read-Host "Digite o nome da sua aplicação no Heroku (deixe em branco para gerar um nome aleatório)"

# Criar aplicação no Heroku
if ([string]::IsNullOrWhiteSpace($appName)) {
    Write-Host "Criando aplicação no Heroku com nome aleatório..." -ForegroundColor Cyan
    heroku create
} else {
    Write-Host "Criando aplicação '$appName' no Heroku..." -ForegroundColor Cyan
    heroku create $appName
}

# Adicionar add-on do PostgreSQL
Write-Host "Adicionando banco de dados PostgreSQL..." -ForegroundColor Cyan
heroku addons:create heroku-postgresql:hobby-dev

# Configurar variáveis de ambiente
Write-Host "Configurando variáveis de ambiente..." -ForegroundColor Cyan
heroku config:set FLASK_ENV=production

# Perguntar se deseja usar banco de dados externo
$useExternalDb = Read-Host "Deseja usar um banco de dados PostgreSQL externo? (S/N)"
if ($useExternalDb -eq "S" -or $useExternalDb -eq "s") {
    $pgHost = Read-Host "Digite o host do PostgreSQL"
    $pgPort = Read-Host "Digite a porta do PostgreSQL (padrão: 5432)"
    if ([string]::IsNullOrWhiteSpace($pgPort)) { $pgPort = "5432" }
    $pgDbName = Read-Host "Digite o nome do banco de dados"
    $pgUser = Read-Host "Digite o usuário do PostgreSQL"
    $pgPassword = Read-Host "Digite a senha do PostgreSQL" -AsSecureString
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pgPassword)
    $pgPasswordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    
    heroku config:set PG_HOST=$pgHost
    heroku config:set PG_PORT=$pgPort
    heroku config:set PG_DBNAME=$pgDbName
    heroku config:set PG_USER=$pgUser
    heroku config:set PG_PASSWORD=$pgPasswordPlain
}

# Adicionar arquivos ao Git
Write-Host "Adicionando arquivos ao Git..." -ForegroundColor Cyan
git add .

# Commit
$commitMessage = Read-Host "Digite a mensagem de commit (padrão: 'Versão inicial para deploy')"
if ([string]::IsNullOrWhiteSpace($commitMessage)) { $commitMessage = "Versão inicial para deploy" }

git commit -m $commitMessage

# Push para o Heroku
Write-Host "Enviando aplicação para o Heroku..." -ForegroundColor Cyan
git push heroku master

# Inicializar banco de dados
Write-Host "Inicializando banco de dados..." -ForegroundColor Cyan
heroku run python init_db.py

# Abrir aplicação no navegador
Write-Host "Abrindo aplicação no navegador..." -ForegroundColor Cyan
heroku open

Write-Host "Deploy concluído com sucesso!" -ForegroundColor Green
Write-Host "Sua aplicação está disponível em: https://$(if ([string]::IsNullOrWhiteSpace($appName)) { (heroku info -s | Select-String -Pattern "^web_url=") -replace "web_url=", "" -replace "https://", "" } else { "$appName.herokuapp.com" })" -ForegroundColor Green