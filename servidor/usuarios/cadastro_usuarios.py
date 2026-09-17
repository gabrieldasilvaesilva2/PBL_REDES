import hashlib
import os
import json

# Garante que a pasta 'usuarios' exista 
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))# pega o diretorio atual do arquivo
DIRETORIO_USUARIOS = os.path.join(DIRETORIO_ATUAL, "jsons_pasageiros") # define o caminho pra pasta jsons dos usuarios
os.makedirs(DIRETORIO_USUARIOS, exist_ok=True)


def gerar_hash_email(email):
  email_limpo = email.strip().lower()
  return hashlib.sha256(email_limpo.encode("utf-8")).hexdigest() #gera a hash do email para ser usado como nome do arquivo
  
def cadastrar_passageiro(nome, email, senha):
  nome_arquivo = gerar_hash_email(email)
  caminho_arquivo = os.path.join(DIRETORIO_USUARIOS, f"{nome_arquivo}.json")#monta o caminho do arquivo com a hash do email

  
  if os.path.exists(caminho_arquivo):# ve se ja tem um arquivo com essa hash no directorio
    return False, "ERRO: Este e-mail já está cadastrado."

  # cria o dicionario com os dados basicos do usuario
  dados_usuario = {
    "perfil": {"nome": nome,"email": email,"senha": senha},
    "historico_corridas": [],"corridas_ativas":[]
    
  }

  # Cria e escreve os dados no arquivo JSON exclusivo deste usuário
  with open(caminho_arquivo, "w", encoding="utf-8") as f:
    json.dump(dados_usuario, f, indent=4, ensure_ascii=False)

  return True, "SUCESSO: Cadastro realizado!"