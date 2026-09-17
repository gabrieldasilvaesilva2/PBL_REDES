import json
import os
import socket
import threading
import networkx as nx
from usuarios.gerenciador_de_usuario import escrita_cliente
from usuarios.pegar_carona import pegar_carona
from usuarios.cadastro_motorista import cadastrar_motorista
from usuarios.cadastro_usuarios import cadastrar_passageiro
from usuarios.login import fazer_login
from usuarios.validar_cidades import validar_rota
from usuarios.cadastrar_carona import cadastrar_carona
from usuarios.listar_caronas import buscar_carona  
from usuarios.cancelar_viagem import cancelar_viagem


# Carrega o dicionario de cidades adjacentes pra converter em grafo e manter em memoria
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_json = os.path.join(diretorio_atual, "mapa_adjacencias.json")

grafo_bahia = nx.Graph()
try:
  with open(caminho_json, "r", encoding="utf-8") as f:
    dados_adjacencias = json.load(f)
    grafo_bahia = nx.Graph(dados_adjacencias)
    print("grafo de cidades carregado e globalizado com sucesso.")
except FileNotFoundError:
  print("erro no servidor: arquivo 'mapa_adjacencias.json' nao encontrado no diretorio.")


def main():
  host = ""  # Escuta em todas as interfaces da rede local automaticamente
  port = 12345
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #socket.AF_INET: Define que o servidor utilizará o protocolo IPv4
  server.bind((host, port))
  server.listen(5)

  print(f"Servidor escutando na porta {port}...")

  while True:
    client_socket, addr = server.accept() #sperando alguém se conectar.
    print(f"Conexão recebida de {addr}")

    client_handler = threading.Thread(
        target=handle_client, args=(client_socket,)
    )
    client_handler.start()


# Função para operações essenciais padronizadas via JSON (dicionário)
def handle_client(client_socket):
  print(f"[CONEXÃO] Atendido pela thread: {threading.current_thread().name}")
  while True:
    data = client_socket.recv(1024).decode("utf-8")
    if not data:
      break

    try:
      # Padronizado: lê tudo como um dicionário JSON enviado pelo cliente
      requisicao = json.loads(data)
      acao = requisicao.get("acao")
    except json.JSONDecodeError:
      client_socket.send("ERRO: Formato de dados inválido.".encode("utf-8"))
      continue

    if acao == "cadastro_passageiro":
      nome = requisicao.get("nome")
      email = requisicao.get("email")
      senha = requisicao.get("senha")

      sucesso, mensagem = cadastrar_passageiro(nome, email, senha)
      client_socket.send(mensagem.encode("utf-8"))

    elif acao == "CADASTRO_MOTORISTA":
      nome = requisicao.get("nome")
      email = requisicao.get("email")
      senha = requisicao.get("senha")
      carro = requisicao.get("carro")
      cor_carro = requisicao.get("cor_carro")

      sucesso, mensagem = cadastrar_motorista(
          nome, email, senha, carro, cor_carro
      )
      client_socket.send(mensagem.encode("utf-8"))

    elif acao == "LOGIN":
      tipo_usuario = requisicao.get("tipo_usuario")
      email = requisicao.get("email")
      senha = requisicao.get("senha")

      sucesso, dado1, dado2 = fazer_login(tipo_usuario, email, senha)
      
      if sucesso:
          resposta_cliente = json.dumps([True, dado1, dado2], ensure_ascii=False)
      else:
          # Mantém os 3 valores consistentes para o cliente não quebrar
          resposta_cliente = json.dumps([False, dado1, dado2], ensure_ascii=False)
          
      client_socket.send(resposta_cliente.encode("utf-8"))

    elif acao == "VALIDAR_CIDADE_ROTA":
      rota = requisicao.get("rota", [])
      sucesso, mensagem = validar_rota(rota, grafo_bahia)
      client_socket.send(mensagem.encode("utf-8"))

    elif acao == "CADASTRAR_VIAGEM":
      viagem_recebida = requisicao.get("viagem", {})

      sucesso, mensagem = cadastrar_carona(viagem_recebida)
      client_socket.send(mensagem.encode("utf-8"))

    elif acao == "PROCURAR_CARONA":
      sucesso, resultado = buscar_carona(requisicao, grafo_bahia)
      
      # Padroniza enviando [sucesso, resultado] em ambos os casos
      resposta_envio = json.dumps([sucesso, resultado], ensure_ascii=False)
      client_socket.send(resposta_envio.encode("utf-8"))
    elif acao == "PEGAR_VAGA":
     vaga=requisicao.get("vaga")
     usuario_logado=requisicao.get("usuario")
     nome_usuario =requisicao.get("nome")
     suceso,mensagem =pegar_carona(vaga,usuario_logado,nome_usuario)
     resposta_envio = json.dumps({"sucesso": sucesso, "mensagem": mensagem}, ensure_ascii=False)
     client_socket.send(resposta_envio.encode("utf-8"))

    elif acao == "RETORNAR_CARONAS_ATIVAS":
      try:
          sucesso, resultado = escrita_cliente("RETORNAR_CARONAS", requisicao)
          resposta_envio = json.dumps([sucesso, resultado], ensure_ascii=False)
      except Exception as e:
          print(f"[ERRO NO SERVIDOR - RETORNAR_CARONAS]: {str(e)}")
          resposta_envio = json.dumps([False, f"Erro interno no servidor: {str(e)}"], ensure_ascii=False)
          
      client_socket.send(resposta_envio.encode("utf-8"))

    elif acao == "CANCELAR_CARONA":
      id_carona_cliente = requisicao.get("id_carona")
      sucesso, ids_passageiros, id_carona_apagada = cancelar_viagem("CANCELAR_VIAGEM", id_carona_cliente)
      resposta_envio = json.dumps({"sucesso": sucesso,  "ids_passageiros": ids_passageiros, "id_carona": id_carona_apagada}, ensure_ascii=False)
      client_socket.send(resposta_envio.encode("utf-8"))

    elif acao == "CANCELAR_CARONA_PASSAGEIRO":
      sucesso, resultado = cancelar_viagem("CANCELAR_CARONA_PASSAGEIRO", requisicao)
      resposta_envio = json.dumps({"sucesso": sucesso, "mensagem": resultado}, ensure_ascii=False)
      client_socket.send(resposta_envio.encode("utf-8"))

    elif acao =="REMOVER_CORRIDA_ATIVA":
      sucesso, mensagem = escrita_cliente("REMOVER_CORRIDA_ATIVA", requisicao)
      resposta_envio = json.dumps({"sucesso": sucesso, "mensagem": mensagem}, ensure_ascii=False)
      client_socket.send(resposta_envio.encode("utf-8"))

    elif acao == "RETORNAR_HISTORICO_CARONA":
      suseso,mensagem = escrita_cliente("VER_HISTORICO",requisicao)
      resposta_envio = json.dumps({"sucesso": sucesso, "mensagem": mensagem}, ensure_ascii=False)
      client_socket.send(resposta_envio.encode("utf-8"))
      

    else:
      client_socket.send(
          "ERRO: Ação não reconhecida pelo servidor.".encode("utf-8")
      )

  client_socket.close()


if __name__ == "__main__":
  main()