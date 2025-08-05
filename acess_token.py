import requests
from base64 import b64encode

# Dados
client_id = "3qc1vlcisbjri8ohb241v32994"
client_secret = "4g0bedku8h4eo8tqg007h0o5n0np77c2jl43dmfvc1fveopm67e"
code = "897a7c41-9008-4d4a-8d4d-c10d0d5cfe17"
redirect_uri = "https://www.turbopartners.com.br/"

# Montar a string base64
basic_auth = b64encode(f"{client_id}:{client_secret}".encode('utf-8')).decode('utf-8')

# URL
url = "https://auth.contaazul.com/oauth2/token"

# Cabeçalhos
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {basic_auth}"
}

# Dados do body
data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": redirect_uri
}

# Requisição POST
response = requests.post(url, headers=headers, data=data)

# Verificar resposta
if response.status_code == 200:
    tokens = response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")
else:
    print(f"Erro ao obter token: {response.status_code} - {response.text}")
