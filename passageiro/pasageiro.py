import json
import socket
import hashlib


def main():
  # Conecta ao servidor na porta 12345
  host = "localhost"
  port = 12345
  #host = "host.docker.internal"   #com docker local 
  #host = "ip_do_servidor" em outra maquina 

  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    client.connect((host, port))
  except ConnectionRefusedError:
    print("ERRO: Não foi possível conectar ao servidor.")
    return

  while True:
    usuario_logado = None
    nome = None

   # tela de autenticação 
    while usuario_logado is None:
      print("\n=== AUTENTICAÇÃO DE PASSAGEIRO ===")
      print("[1] Login")
      print("[2] Cadastrar")
      print("[0] Sair do Programa")
      resposta_auth = input("Escolha uma opção: ").strip()

      if resposta_auth == "1":
        email = input("Digite seu email: ")
        senha = input("Digite sua senha: ")

        # Envia o login do passageiro como dicionário JSON
        dados_login = {
            "acao": "LOGIN",
            "tipo_usuario": "passageiro",
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

        # Envia o cadastro do passageiro como dicionário JSON
        dados_cadastro = {
            "acao": "cadastro_passageiro",
            "nome": nome_cad,
            "email": email_cad,
            "senha": senha_cad,
        }
        client.send(json.dumps(dados_cadastro).encode("utf-8"))

        # Aguarda a resposta do servidor e exibe na tela
        resposta_servidor = client.recv(1024).decode("utf-8")
        print(f"\nServidor: {resposta_servidor}")

      elif resposta_auth == "0":
        client.close()
        return
      else:
        print("\n[ERRO] Opção inválida. Digite 1, 2 ou 0.")

    # menu do sistema 
    while usuario_logado is not None:
      print(f"\n=== MENU PRINCIPAL (Logado: {nome}) ===")
      print("[1] Procurar e Pegar Carona")
      print("[2] Logout (Trocar de conta)")
      print("[3] cancelar carona")
      print("[4] ver minhas caronas")
      print("[5] ver hiistorico de caronas")
      print("[0] Sair do Sistema")
      
      resposta_menu = input("Escolha uma opção: ").strip()

      if resposta_menu == "1":
        # Loop de validação de cidades de saída e chegada
        while True:
          saida = input("Digite a cidade de saída: ")
          chegada = input("Digite a cidade de chegada: ")

          dados_validacao = {
              "acao": "VALIDAR_CIDADE_ROTA",
              "rota": [saida, chegada],
          }

          client.send(json.dumps(dados_validacao).encode("utf-8"))
          resposta_servidor = client.recv(1024).decode("utf-8")

          if "sucesso" in resposta_servidor.lower():
            print(f"\n[SUCESSO] {resposta_servidor}")
            break
          else:
            print(f"\n[ERRO] {resposta_servidor}")
            print("Por favor, digite as cidades novamente.\n")

        procurar_carona = {
            "acao": "PROCURAR_CARONA",
            "cidade_chegada": chegada,
            "cidade_saida": saida,
        }
        client.send(json.dumps(procurar_carona).encode("utf-8"))
        resposta_bruta = client.recv(4096).decode("utf-8")
        try:
          sucesso, dados = json.loads(resposta_bruta)
        except json.JSONDecodeError:
          print("\n[ERRO] Resposta inválida recebida do servidor.")
          continue

        if not sucesso:
          print(f"\n[ERRO] {dados}")
        elif not dados:
          print("\n[INFO] Nenhuma carona encontrada para este trecho no momento.")
        else:
          print("\n=== CARONAS ENCONTRADAS ===")
          for idx, carona in enumerate(dados, 1):
            print(f"\n[{idx}] Tipo: {carona.get('tipo')}")
            if carona.get('tipo') == 'DIRETA':
              print(f"    - ID: {carona.get('id_carona')}")
              print(f"    - Motorista: {carona.get('motorista')} (Carro: {carona.get('carro')} - {carona.get('cor_carro')})")
              print(f"    - Trecho: {carona.get('trecho_solicitado')}")
              print(f"    - Data: {carona.get('data')}")
              print(f"    - Preço Total: R$ {carona.get('preco_total'):.2f}")
            else:
              print(f"    - IDs Envolvidos: {carona.get('ids_caronas')}")
              print(f"    - Trecho 1: {carona.get('trecho_1', {}).get('trecho')} (Motorista: {carona.get('trecho_1', {}).get('motorista')})")
              print(f"    - Trecho 2: {carona.get('trecho_2', {}).get('trecho')} (Motorista: {carona.get('trecho_2', {}).get('motorista')})")
              print(f"    - Data: {carona.get('data')}")
              print(f"    - Preço Total: R$ {carona.get('preco_total', 0.0):.2f}")

          caronas_disponiveis = dados      
          opcao = input("Digite o número da carona desejada (ou 0 para cancelar): ").strip()
          
          if opcao.isdigit():
              idx_escolhido = int(opcao)
              
              if idx_escolhido == 0:
                  print("\n[INFO] Operação cancelada.")
                  continue
                  
              if 1 <= idx_escolhido <= len(caronas_disponiveis):
                  carona_selecionada = caronas_disponiveis[idx_escolhido - 1]
                  
                  pegar_vaga = {
                      "acao": "PEGAR_VAGA",
                      "vaga": carona_selecionada, 
                      "usuario": usuario_logado, 
                      "nome": nome               
                  }

                  client.send(json.dumps(pegar_vaga).encode("utf-8"))
                  resposta_servidor = client.recv(4096).decode("utf-8")
                  
                  print(f"\n[SERVIDOR] {resposta_servidor}")
              else:
                  print("\n[ERRO] Número da carona inválido.")
          else:
              print("\n[ERRO] Entrada inválida. Digite apenas números.")

      elif resposta_menu == "2":
        print(f"\n[INFO] Logout realizado. Retornando à tela de login...")
        usuario_logado = None
        nome = None
        break  # Quebra o menu principal e volta para o loop de autenticação


      elif resposta_menu == "3":
        hash_do_usuario_logado = hashlib.sha256(usuario_logado.strip().lower().encode("utf-8")).hexdigest()
        dado = {
            "acao": "RETORNAR_CARONAS_ATIVAS",
            "tipo_usuario": "passageiro", 
            "hash_email": hash_do_usuario_logado
        }
        client.send(json.dumps(dado).encode("utf-8"))
        resposta_servidor = client.recv(4096).decode("utf-8")
        try:
            # O servidor empacota como: [sucesso, resultado]
            sucesso, caronas = json.loads(resposta_servidor)
            
            if sucesso:
                if not caronas:
                    print("\n[INFO] Você não possui nenhuma carona ativa no momento.")
                else:
                    print("\n=== SUAS CARONAS ATIVAS ===")
                    for idx, c in enumerate(caronas, 1):
                        print(f"[{idx}] ID da Carona: {c.get('id_carona')} | Rota: {c.get('rota')} | Data: {c.get('data')}")
                    
                    escolha = input("\nDigite o número da carona que deseja cancelar (ou 0 para voltar): ").strip()
                    
                    if escolha.isdigit():
                        escolha_idx = int(escolha)
                        if escolha_idx == 0:
                            print("\n[INFO] Operação cancelada.")
                        elif 1 <= escolha_idx <= len(caronas):
                            carona_selecionada = caronas[escolha_idx - 1]
                            id_carona_escolhida = carona_selecionada.get("id_carona")
                            
                            # 1. Remove do arquivo pessoal do passageiro
                            dado_cancelamento = {
                                "acao": "REMOVER_CORRIDA_ATIVA",
                                "tipo_usuario": "passageiro",
                                "id_carona": id_carona_escolhida,
                                "hash_email": hash_do_usuario_logado
                            }
                            
                            client.send(json.dumps(dado_cancelamento).encode("utf-8"))
                            resposta_remocao = client.recv(4096).decode("utf-8")
                            
                            try: 
                                # A função escrita_cliente para REMOVER_CORRIDA_ATIVA retorna um booleano e uma string/mensagem
                                sucesso_rem, msg_rem = json.loads(resposta_remocao)
                                
                                if sucesso_rem:
                                    print(f"\n[SUCESSO] Carona {id_carona_escolhida} removida das suas ativas com sucesso!")
                                    
                                    # 2. Cancela globalmente liberando a vaga para o motorista/sistema
                                    dado_global_cancelamento = {
                                        "acao": "CANCELAR_CARONA_PASSAGEIRO",
                                        "id_carona": id_carona_escolhida,
                                        "hash_email": hash_do_usuario_logado
                                    }
                                    
                                    client.send(json.dumps(dado_global_cancelamento).encode("utf-8"))
                                    resposta_global = client.recv(4096).decode("utf-8")
                                    
                                    print(f"\n[SERVIDOR - GLOBAL]: {resposta_global}")
                                else:
                                    print(f"\n[ERRO] {msg_rem}")
                            except json.JSONDecodeError:
                                print(f"\n[ERRO] Resposta inesperada ao remover: {resposta_remocao}")
                        else:
                            print("\n[ERRO] Número inválido.")
                    else:
                        print("\n[ERRO] Digite apenas um número válido.")
            else:
                print(f"\n[ERRO] {caronas}")
        except json.JSONDecodeError:
            print(f"\n[ERRO] Resposta inesperada do servidor: {resposta_servidor}")


      elif resposta_menu == "4":
         hash_do_usuario_logado = hashlib.sha256(usuario_logado.strip().lower().encode("utf-8")).hexdigest()
         dado = {
             "acao": "RETORNAR_CARONAS_ATIVAS",
             "tipo_usuario": "passageiro",
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
                 print("\n=== SUAS CARONAS ATIVAS ===")
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


      elif resposta_menu == "5":
       hash_do_usuario_logado = hashlib.sha256(usuario_logado.strip().lower().encode("utf-8")).hexdigest()
       dado = {
                "acao": "RETORNAR_HISTORICO_CARONA",
                "tipo_usuario": "passageiro",
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