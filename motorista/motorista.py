import hashlib
import json
import socket
import uuid
from datetime import datetime


def main():
  #host = "host.docker.internal" com docker 
  #host = "ip_doservidor"
  host = "localhost"
  port = 12345


  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    client.connect((host, port))
  except ConnectionRefusedError:
    print("ERRO: Não foi possível conectar ao servidor.")
    return

  while True:
    usuario_logado = None
    nome = None

   # lop de autenticação 
    while usuario_logado is None:
      print("\n=== AUTENTICAÇÃO DE MOTORISTA ===")
      print("[1] Login")
      print("[2] Cadastrar")
      print("[0] Sair do Programa")
      resposta_auth = input("Escolha uma opção: ").strip()

      if resposta_auth == "1":
        email = input("Digite seu email: ")
        senha = input("Digite sua senha: ")
        
        # Envia o login do motorista como dicionário JSON
        dados_login = {
            "acao": "LOGIN",
            "tipo_usuario": "motorista",
            "email": email,
            "senha": senha,
        }
        client.send(json.dumps(dados_login).encode("utf-8"))
        resposta_servidor = client.recv(1024).decode("utf-8")
        try:
            resposta_dados = json.loads(resposta_servidor)
            boleano, email_retornado, nome_usuario = resposta_dados
            if boleano:
                usuario_logado = email
                nome = nome_usuario
                print(f"\n[SUCESSO] Login bem-sucedido! Bem-vindo, {nome}!")
                break  # Quebra o loop de autenticação e libera o menu principal
            else:
                # Altere aqui para receber os 3 valores (pegando a mensagem no terceiro)
                _, _, mensagem_erro = resposta_dados
                print(f"\n[ERRO] {mensagem_erro}")
                
        except (json.JSONDecodeError, IndexError):
            print(f"\n[ERRO] Resposta inesperada do servidor: {resposta_servidor}")      

      elif resposta_auth == "2":
        nome_cad = input("Digite seu nome: ")
        email_cad = input("Digite seu email: ")
        senha_cad = input("Digite sua senha: ")
        carro = input("Digite o modelo do carro: ")
        cor_carro = input("Digite a cor do carro: ")

        dados_cadastro = {
            "acao": "CADASTRO_MOTORISTA",
            "nome": nome_cad,
            "email": email_cad,
            "senha": senha_cad,
            "carro": carro,
            "cor_carro": cor_carro,
        }

        mensagem_json = json.dumps(dados_cadastro)
        client.send(mensagem_json.encode("utf-8"))

        resposta_servidor = client.recv(1024).decode("utf-8")
        print(f"\nServidor: {resposta_servidor}")

      elif resposta_auth == "0":
        client.close()
        return
      else:
        print("\n[ERRO] Opção inválida. Digite 1, 2 ou 0.")

    # menu 
    while usuario_logado is not None:
      print(f"\n=== MENU PRINCIPAL (Motorista: {nome}) ===")
      print("[1] Ofertar carona")
      print("[2] Cancelar viagem")
      print("[3] Logout (Trocar de conta)")
      print("[4] Ver viagen ativas ")
      print("[5] Ver historico de viagens")
      print("[0] Sair do Sistema")
      
      resposta_menu = input("Escolha uma opção: ").strip()

      if resposta_menu == "1":
        id_carona = str(uuid.uuid4())

        # LOOP DE VALIDAÇÃO DAS CIDADES E ROTAS PELO GRAFO 
        while True:
          rota = []
          origem = input("Digite a cidade de partida: ")
          destino = input("Digite a cidade de destino: ")
          paradas = input("Deseja fazer paradas? (s/n): ")
          rota.append(origem)

          if paradas.lower() == "s":
            while True:
              parada = input(
                  "Digite o nome da cidade que deseja parar (ou 'fim' para"
                  " encerrar): "
              )
              if parada.lower() == "fim":
                break
              rota.append(parada)
          rota.append(destino)

          # Envia a rota para o servidor validar
          dados_validacao = {"acao": "VALIDAR_CIDADE_ROTA", "rota": rota}
          client.send(json.dumps(dados_validacao).encode("utf-8"))
          resposta_servidor = client.recv(1024).decode("utf-8")

          if "válida" in resposta_servidor.lower():
            print(f"\n[SUCESSO] {resposta_servidor}")
            break
          else:
            print(f"\n[ERRO] {resposta_servidor}")
            print("Por favor, digite a rota novamente.\n")

        # validação de data e horário
        while True:
          dia = input("Digite a data da carona (ex: 25/12/2026): ")
          try:
            datetime.strptime(f"{dia}", "%d/%m/%Y")
            break
          except ValueError:
            print("Formato de data inválido. Tente novamente.")

        while True:
          try:
            vagas = int(input("Digite o número de vagas disponíveis: "))
            if vagas >= 1:
              break
            print("O número de vagas deve ser no mínimo 1.")
          except ValueError:
            print("Por favor, digite apenas números inteiros válidos.")

        horario_trechos = {}
        pontos_parada = {}
        
        for i, cidade in enumerate(rota):
          ponto = input(f"Digite o ponto de referência/parada em {cidade} (ex: Rua X, Câmara de Vereadores): ")
          pontos_parada[cidade] = ponto

        while True:
          partida = input(f"Digite o horário de partida em {rota[0]} (ex: 14:30): ")
          try:
            datetime.strptime(f"{partida}", "%H:%M")
            horario_trechos[rota[0]] = partida
            break
          except ValueError:
            print("Formato de horário inválido. Tente novamente.")

        for i in range(1, len(rota)):
          cidade_anterior = rota[i - 1]
          cidade_atual = rota[i]

          while True:
            chegada = input(
                f"Digite o horário de chegada em {cidade_atual} (saindo de"
                f" {cidade_anterior}) (ex: 16:30): "
            )
            try:
              datetime.strptime(chegada, "%H:%M")
              horario_trechos[cidade_atual] = chegada
              break
            except ValueError:
              print("Formato de horário inválido. Tente novamente.")

        precos_trechos = {}
        for i in range(len(rota) - 1):
          cidade_anterior = rota[i]
          cidade_atual = rota[i + 1]
          nome_trecho = f"{cidade_anterior} -> {cidade_atual}"
          
          while True:
            try:
              preco = float(input(f"Digite o preço para o trecho [{nome_trecho}] (ex: 25.00): R$ "))
              if preco >= 0:
                precos_trechos[nome_trecho] = preco
                break
              print("O preço não pode ser negativo.")
            except ValueError:
              print("Por favor, digite um valor numérico válido.")

        viagem = {
            "id_carona": id_carona,
            "rota": rota,
            "horarios_trechos": horario_trechos,
            "pontos_parada": pontos_parada,
            "precos_trechos": precos_trechos,
            "vagas": vagas,
            "motorista": usuario_logado,
            "data": dia,
        }
        print("\nCarona estruturada e validada com sucesso!")
        dados_cadastro_viagem = {
            "acao": "CADASTRAR_VIAGEM",
            "viagem": viagem
        }
        client.send(json.dumps(dados_cadastro_viagem).encode("utf-8"))
        resposta_servidor = client.recv(1024).decode("utf-8")
        print(f"\nServidor: {resposta_servidor}")

      elif resposta_menu == "2":
        hash_email_motorista = hashlib.sha256(usuario_logado.strip().lower().encode("utf-8")).hexdigest()
        
        dados_consulta = {
            "acao": "RETORNAR_CARONAS_ATIVAS",
            "tipo_usuario": "motorista",
            "hash_email": hash_email_motorista
        }
        
        client.send(json.dumps(dados_consulta).encode("utf-8"))
        resposta_servidor = client.recv(4096).decode("utf-8")

        try:
          sucesso, caronas = json.loads(resposta_servidor)
          
          if sucesso:
            if not caronas:
              print("\n[INFO] Você não possui nenhuma viagem ativa no momento.")
            else:
              print("\n=== SUAS VIAGENS ATIVAS ===")
              for idx, c in enumerate(caronas, 1):
                print(f"[{idx}] ID: {c.get('id_carona')} | Rota: {c.get('rota')} | Data: {c.get('data')}")
              
              # Lógica para o usuário escolher qual deseja apagar
              escolha = input("\nDigite o número da viagem que deseja cancelar (ou 0 para voltar): ").strip()
              
              if escolha.isdigit():
                escolha_idx = int(escolha)
                if escolha_idx == 0:
                  print("\n[INFO] Operação cancelada.")
                elif 1 <= escolha_idx <= len(caronas):
                  carona_selecionada = caronas[escolha_idx - 1]
                  id_para_cancelar = carona_selecionada.get("id_carona")
                  
                  print(f"\n[INFO] Viagem selecionada com ID: {id_para_cancelar}")
                  # Envia a requisição de cancelamento para o servidor
                  dados_cancelamento = {
                      "acao": "CANCELAR_CARONA",
                      "id_carona": id_para_cancelar
                  }
                  
                  client.send(json.dumps(dados_cancelamento).encode("utf-8"))
                  resposta_cancelamento = client.recv(4096).decode("utf-8")
                  
                  try:
                    res_canc_json = json.loads(resposta_cancelamento)
                    if res_canc_json.get("sucesso"):
                      ids_afetados = res_canc_json.get("ids_passageiros", [])
                      id_apagado = res_canc_json.get("id_carona")
                      print(f"\n[SUCESSO] Viagem {id_apagado} cancelada com sucesso!")
                      print(f"[INFO] Passageiros afetados (hashes): {ids_afetados}")
                      hash_email_motorista = hashlib.sha256(usuario_logado.strip().lower().encode("utf-8")).hexdigest()
                      dados = {
                          "acao": "REMOVER_CORRIDA_ATIVA",
                          "tipo_usuario":"mutiplo",
                          "id_carona": id_apagado,
                          "hash_motorista": hash_email_motorista,
                          "ids_passageiros": ids_afetados
                      }
                      client.send(json.dumps(dados).encode("utf-8"))
                      resposta_limpeza = client.recv(4096).decode("utf-8")

                    else:
                      print(f"\n[ERRO] Não foi possível cancelar: {res_canc_json.get('mensagem', 'Erro desconhecido')}")
                  except json.JSONDecodeError:
                    print(f"\n[ERRO] Resposta inesperada do servidor: {resposta_cancelamento}")
                else:
                  print("\n[ERRO] Número inválido.")
              else:
                print("\n[ERRO] Digite apenas um número válido.")
          else:
            print(f"\n[ERRO] {resposta_json.get('mensagem', 'Erro ao buscar caronas.')}")
        except json.JSONDecodeError:
          print(f"\n[ERRO] Resposta inesperada do servidor: {resposta_servidor}")


      elif resposta_menu == "3":
        print(f"\n[INFO] Logout realizado. Retornando à tela de login...")
        usuario_logado = None
        nome = None
        break  # Quebra o menu principal e volta para o loop de autenticação


      elif resposta_menu == "4":
               hash_do_usuario_logado = hashlib.sha256(usuario_logado.strip().lower().encode("utf-8")).hexdigest()
               dado = {
                   "acao": "RETORNAR_CARONAS_ATIVAS",
                   "tipo_usuario": "motorista",
                   "hash_email": hash_do_usuario_logado
               }
               
               client.send(json.dumps(dado).encode("utf-8"))
               resposta_servidor = client.recv(4096).decode("utf-8")
               try:
                   # O servidor geralmente retorna uma lista: [sucesso, dados/lista_de_corridas]
                   sucesso, corridas_ativas = json.loads(resposta_servidor)
                   
                   if not sucesso:
                       print(f"\n[ERRO] {corridas_ativas}")
                   elif not corridas_ativas:
                       print("\n[INFO] Você não possui nenhuma carona ativa no momento.")
                   else:
                       print("\n=== SUAS VIAGENS ATIVAS ===")
                       for idx, carona in enumerate(corridas_ativas, 1):
                           print(f"\n[{idx}] ID da Carona: {carona.get('id_carona', 'N/A')}")
                           print(f"    - Trecho/Rota: {carona.get('trecho_solicitado') or carona.get('rota')}")
                           print(f"    - Data: {carona.get('data', 'N/A')}")
                           if carona.get('motorista'):
                               print(f"    - Motorista: {carona.get('motorista')}")
                           if carona.get('preco_total'):
                               print(f"    - Preço: R$ {carona.get('preco_total'):.2f}")
               
               except json.JSONDecodeError:
                   print(f"\n[ERRO] Resposta inesperada do servidor: {resposta_servidor}")




      elif resposta_menu =="5":
        hash_do_usuario_logado = hashlib.sha256(usuario_logado.strip().lower().encode("utf-8")).hexdigest()
        dado = {
                "acao": "RETORNAR_HISTORICO_CARONA",
                "tipo_usuario": "motorista",
                "hash_email": hash_do_usuario_logado
              }
        
        client.send(json.dumps(dado).encode("utf-8"))
        resposta_servidor = client.recv(4096).decode("utf-8")
        try:
            resposta_json = json.loads(resposta_servidor)
            if resposta_json.get("sucesso"):
                historico = resposta_json.get("mensagem", [])
                
                if not historico:
                    print("\n[INFO] Você não possui corridas no histórico.")
                else:
                    print("\n=== SEU HISTÓRICO DE CORRIDAS ===")
                    for idx, c in enumerate(historico, 1):
                        print(f"[{idx}] ID: {c.get('id_carona', 'N/A')} | Trecho: {c.get('trecho_solicitado') or c.get('rota')} | Data: {c.get('data', 'N/A')}")
            else:
                print(f"\n[ERRO] {resposta_json.get('mensagem', 'Erro ao buscar histórico.')}")
        except json.JSONDecodeError:
            print(f"\n[ERRO] Resposta inesperada do servidor: {resposta_servidor}")             
      elif resposta_menu == "0":
        client.close()
        return
      else:
        print("\n[ERRO] Opção inválida.")


if __name__ == "__main__":
  main()