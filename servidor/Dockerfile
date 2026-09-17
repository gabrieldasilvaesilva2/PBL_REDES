# Usa uma imagem oficial do Python limpa e leve
FROM python:3.11-slim

# Define o diretório de trabalho principal dentro do container
WORKDIR /app

# Copia primeiro o arquivo de dependências para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as bibliotecas necessárias (como o networkx) (so pra gerar o grafo a partir da lista de adjacencias e operar nele)
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o restante do seu projeto (pastas de usuários, JSONs, servidor.py, etc.) para dentro do container
COPY . /app

# Expõe a porta 12345 que é a que eu escolhi pro servidor TCP 
EXPOSE 12345

# Comando para iniciar o servidor executando o seu arquivo servidor_2.py
CMD ["python", "servidor.py"]