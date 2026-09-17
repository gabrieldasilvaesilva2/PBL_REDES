import hashlib
import json
import os
import threading
from .gerenciador_de_caronas_ativas import gerenciar_carona_global
from .gerenciador_de_usuario import escrita_cliente


# Dicionário de locks individuais para cada motorista (evita conflito por motorista)
locks_motoristas = {}
lock_global_locks = threading.Lock()


def obter_lock_motorista(hash_email):
  with lock_global_locks:
    if hash_email not in locks_motoristas:
      locks_motoristas[hash_email] = threading.Lock()
    return locks_motoristas[hash_email]


def gerar_hash_email(email):
  email_limpo = email.strip().lower()
  return hashlib.sha256(email_limpo.encode("utf-8")).hexdigest()


def cadastrar_carona(viagem):
  try:
    # 1. Identifica o email do motorista logado
    usuario_info = viagem.get("motorista")
    if isinstance(usuario_info, dict):
      email_motorista = usuario_info.get("email")
    else:
      email_motorista = str(usuario_info) if usuario_info else ""

    if not email_motorista:
      return False, "Erro: E-mail do motorista não identificado na sessão."

    hash_email = gerar_hash_email(email_motorista)

    # Caminho do diretório do motorista
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_motorista = os.path.join(
        diretorio_atual, "jsons_motoristas", f"{hash_email}.json"
    )

    # 2. Verifica se o arquivo do motorista existe antes de fazer qualquer coisa pesada
    lock_mot = obter_lock_motorista(hash_email)

    with lock_mot:
      if not os.path.exists(caminho_motorista):
        return (
            False,
            "Erro: Arquivo de cadastro do motorista não encontrado na pasta"
            " jsons_motoristas.",
        )

      with open(caminho_motorista, "r", encoding="utf-8") as f:
        dados_motorista = json.load(f)

      perfil = dados_motorista.get("perfil", {})
      nome_motorista = perfil.get("nome", "Motorista")
      carro_motorista = perfil.get("carro", "Não informado")
      cor_carro_motorista = perfil.get("cor_carro", "Não informada")

    # 3. Monta a estrutura por trecho
    rota = viagem["rota"]
    vagas_iniciais = viagem["vagas"]

    vagas_por_trecho = {}
    passageiros_por_trecho = {}

    for i in range(len(rota) - 1):
      origem = rota[i]
      destino = rota[i + 1]
      nome_trecho = f"{origem} -> {destino}"

      vagas_por_trecho[nome_trecho] = vagas_iniciais
      passageiros_por_trecho[nome_trecho] = []

    id_carona = viagem["id_carona"]
    data_viagem = viagem["data"]

    # 4. Estrutura completa da carona para o JSON geral
    carona_estruturada = {
        "id_carona": id_carona,
        "motorista": nome_motorista,
        "email_motorista": email_motorista,
        "carro": carro_motorista,
        "cor_carro": cor_carro_motorista,
        "data": data_viagem,
        "rota": rota,
        "horarios_trechos": viagem.get("horarios_trechos", {}),
        "pontos_parada": viagem.get("pontos_parada", {}),
        "precos_trechos": viagem.get("precos_trechos", {}),
        "vagas_por_trecho": vagas_por_trecho,
        "passageiros_por_trecho": passageiros_por_trecho,
    }

    # Tenta salvar no arquivo global através do gerenciador
    sucesso_global, mensagem_global = gerenciar_carona_global("CADASTRAR", carona_estruturada)
    
    # Se falhar no global, cai no return e não mexe no arquivo do motorista
    if not sucesso_global:
      return False, f"Erro ao registrar carona no sistema global: {mensagem_global}"

    # Prepara as informações para atualizar o JSON individual do motorista de forma segura
    info_historico = {
        "id_carona": id_carona,
        "rota": rota,
        "data": data_viagem,
    }
    
    dado_escrita = {
        "tipo_usuario": "motorista",
        "hash_email": hash_email,
        "registro": info_historico
    }

    # Delega a escrita segura para o gerenciador de usuários
    sucesso_escrita, mensagem_escrita = escrita_cliente("ADICIONAR_HISTORICO_E_ATIVAS", dado_escrita)
    if not sucesso_escrita:
        return False, f"Erro ao atualizar o arquivo do motorista: {mensagem_escrita}"

    return True, "Carona cadastrada com sucesso!"

  except Exception as e:
    return False, f"Erro ao processar o cadastro da carona: {str(e)}"