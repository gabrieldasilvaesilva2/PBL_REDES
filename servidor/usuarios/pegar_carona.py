import hashlib
import json
import os
import threading
from .gerenciador_de_caronas_ativas import gerenciar_carona_global
from .gerenciador_de_usuario import escrita_cliente

# Dicionário de locks individuais para cada passageiro (evita conflito concorrente)
locks_passageiros = {}
lock_global_passageiros = threading.Lock()

def obter_lock_passageiro(hash_email):
    with lock_global_passageiros:
        if hash_email not in locks_passageiros:
            locks_passageiros[hash_email] = threading.Lock()
        return locks_passageiros[hash_email]

def gerar_hash_email(email):
  email_limpo = email.strip().lower()
  return hashlib.sha256(email_limpo.encode("utf-8")).hexdigest()

def pegar_carona(vaga, email, nome):
  try:
      email_limpo = gerar_hash_email(email)
      dados_requisicao = {
            "tipo": vaga.get("tipo"),  
            "vaga": vaga,
            "email": email_limpo,
            "nome": nome
        }
        
      # 1. Tenta reservar a vaga no sistema global protegido por Mutex
      sucesso, mensagem = gerenciar_carona_global("PEGAR_VAGA", dados_requisicao)
      
      # Se a reserva falhar no global, retorna sem registrar vaga no usuario
      if not sucesso:
          return False, mensagem

      # 2. Se deu certo, atualiza o JSON individual do passageiro existente
      tipo_vaga = vaga.get("tipo")
      if tipo_vaga == "DIRETA":
          info_viagem = {
              "tipo": "DIRETA",
              "id_carona": vaga.get("id_carona"),
              "motorista": vaga.get("motorista"),
              "trecho": vaga.get("trecho_solicitado"),
              "data": vaga.get("data"),
              "preco_total": vaga.get("preco_total")
          }
      elif tipo_vaga == "CONEXAO":
          info_viagem = {
              "tipo": "CONEXAO",
              "ids_caronas": vaga.get("ids_caronas"),
              "trecho_1": vaga.get("trecho_1"),
              "trecho_2": vaga.get("trecho_2"),
              "data": vaga.get("data"),
              "preco_total": vaga.get("preco_total")
          }
      else:
          info_viagem = {"vaga": vaga}

      dado_escrita = {
          "tipo_usuario": "passageiro",
          "hash_email": email_limpo,
          "registro": info_viagem
      }

      sucesso_escrita, mensagem_escrita = escrita_cliente("ADICIONAR_HISTORICO_E_ATIVAS", dado_escrita)
      if not sucesso_escrita:
          return False, f"Erro ao atualizar o arquivo do passageiro: {mensagem_escrita}"

      return True, mensagem

  except Exception as e:
      return False, f"Erro interno ao registrar carona para o passageiro: {str(e)}"