import hashlib
import json
import os

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))  # pega o diretorio atual do arquivo
DIRETORIO_USUARIO_PASSAGEIRO = os.path.join(DIRETORIO_ATUAL, "jsons_pasageiros")  # define o caminho pra pasta jsons dos usuarios
os.makedirs(DIRETORIO_USUARIO_PASSAGEIRO, exist_ok=True)
#################################################################################################################
DIRETORIO_USUARIO_MOTORISTA = os.path.join(DIRETORIO_ATUAL, "jsons_motoristas")  # define o caminho pra pasta jsons dos usuarios
os.makedirs(DIRETORIO_USUARIO_MOTORISTA, exist_ok=True)


def gerar_hash_email(email):
  email_limpo = email.strip().lower()
  return hashlib.sha256(email_limpo.encode("utf-8")).hexdigest()


def fazer_login(tipo_usuario, email, senha):
  if tipo_usuario.lower() == "motorista":
    diretorio = DIRETORIO_USUARIO_MOTORISTA
  elif tipo_usuario.lower() == "passageiro":
    diretorio = DIRETORIO_USUARIO_PASSAGEIRO
  else:
    return False, None, "ERRO: Tipo de usuário inválido."  

  nome_arquivo = gerar_hash_email(email)
  caminho = os.path.join(diretorio, f"{nome_arquivo}.json")

  if not os.path.exists(caminho):
    return False, None, "ERRO: Usuário não encontrado."  
  with open(caminho, "r", encoding="utf-8") as f:
    dados = json.load(f)

  if dados["perfil"]["senha"] == senha:
      nome_usuario = dados["perfil"].get("nome", "Usuário")
      return True, email, nome_usuario

  return False, None, "ERRO: Senha ou email incorretos."