import json
import os
import threading

# Dicionários de locks individuais por usuário
locks_usuarios = {}
lock_global_locks = threading.Lock()

def obter_lock_usuario(hash_email):
    with lock_global_locks:
        if hash_email not in locks_usuarios:
            locks_usuarios[hash_email] = threading.Lock()
        return locks_usuarios[hash_email]

def escrita_cliente(acao, dado):
    """
    alteração protegida por mutex por usuário.
    """
    tipo_usuario = dado.get("tipo_usuario")  # "motorista", "passageiro" ou "mutiplo"
    hash_email = dado.get("hash_email")

    # Validação inicial flexível para aceitar o modo múltiplo sem o hash_email único obrigatório
    if not tipo_usuario:
        return False, "Erro: tipo_usuario não informado."

    if tipo_usuario.lower() != "mutiplo" and not hash_email:
        return False, "Erro: hash_email não informado."

    diretorio_atual = os.path.dirname(os.path.abspath(__file__))

    # Preparação dos caminhos dos arquivos com base no cenário
    if tipo_usuario.lower() == "mutiplo":
        hash_motorista = dado.get("hash_motorista")
        hashes_passageiros = dado.get("ids_passageiros", [])
        
        # Define os caminhos dos diretórios para o motorista e para os passageiros
        caminho_motorista = os.path.join(diretorio_atual, "jsons_motoristas", f"{hash_motorista}.json") if hash_motorista else None
        caminhos_passageiros = [
            os.path.join(diretorio_atual, "jsons_pasageiros", f"{h_pass}.json") 
            for h_pass in hashes_passageiros
        ]
    else:
        if tipo_usuario.lower() == "motorista":
            caminho_arquivo = os.path.join(diretorio_atual, "jsons_motoristas", f"{hash_email}.json")
        else:
            caminho_arquivo = os.path.join(diretorio_atual, "jsons_pasageiros", f"{hash_email}.json")

    # Fluxo normal para ações individuais
    if tipo_usuario.lower() != "mutiplo":
        lock_usr = obter_lock_usuario(hash_email)

        with lock_usr:
            if not os.path.exists(caminho_arquivo):
                return False, f"Erro: Arquivo do usuário não encontrado."

            try:
                with open(caminho_arquivo, "r", encoding="utf-8") as f:
                    dados_usuario = json.load(f)
            except json.JSONDecodeError:
                dados_usuario = {}

            if acao == "ADICIONAR_HISTORICO_E_ATIVAS":
                if "historico_corridas" not in dados_usuario:
                    dados_usuario["historico_corridas"] = []
                if "corridas_ativas" not in dados_usuario:
                    dados_usuario["corridas_ativas"] = []

                info_historico = dado.get("registro")
                if not info_historico:
                    return False, "Erro: Registro não fornecido."

                dados_usuario["historico_corridas"].append(info_historico)
                dados_usuario["corridas_ativas"].append(info_historico)

                with open(caminho_arquivo, "w", encoding="utf-8") as f:
                    json.dump(dados_usuario, f, ensure_ascii=False, indent=4)

                return True, "Escrita realizada com sucesso!"

            elif acao == "REMOVER_CARONA_ATIVA":
                # Caso alguém chame individualmente por engano, tratamos aqui também
                id_carona = dado.get("id_carona")
                if not id_carona:
                    return False, "Erro: ID da carona não fornecido."
                
                if "corridas_ativas" not in dados_usuario:
                    return True, "Nenhuma corrida ativa encontrada."

                lista_original = dados_usuario["corridas_ativas"]
                nova_lista = []
                alterado = False

                for item in lista_original:
                    id_direto = item.get("id_carona")
                    ids_conexao = item.get("ids_caronas", [])
                    if id_direto == id_carona or id_carona in ids_conexao:
                        alterado = True
                    else:
                        nova_lista.append(item)

                if alterado:
                    dados_usuario["corridas_ativas"] = nova_lista
                    with open(caminho_arquivo, "w", encoding="utf-8") as f:
                        json.dump(dados_usuario, f, ensure_ascii=False, indent=4)
                    return True, "Carona ativa removida com sucesso!"
                return True, "A carona não estava nas ativas."

            elif acao == "RETORNAR_CARONAS":
                corridas_ativas = dados_usuario.get("corridas_ativas", [])
                return True, corridas_ativas

            elif acao == "VER_HISTORICO":
                ver_histirico = dados_usuario.get("historico_corridas", [])
                return True, ver_histirico
            else:
                return False, f"Erro: Ação '{acao}' não reconhecida."

    # Cenário Múltiplo (Motorista + Passageiros afetados)
    else:
        if acao == "REMOVER_CARONA_ATIVA":
            id_carona = dado.get("id_carona")
            if not id_carona:
                return False, "Erro: ID da carona não fornecido para remoção."

            # Função interna auxiliar para limpar as corridas ativas de um arquivo de forma segura
            def limpar_arquivo_usuario(caminho):
                if not caminho or not os.path.exists(caminho):
                    return

                nome_arquivo = os.path.basename(caminho)
                hash_usuario = os.path.splitext(nome_arquivo)[0]
                lock_usr = obter_lock_usuario(hash_usuario)

                with lock_usr:
                    try:
                        with open(caminho, "r", encoding="utf-8") as f:
                            dados_usuario = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        return

                    if "corridas_ativas" not in dados_usuario:
                        return

                    lista_original = dados_usuario["corridas_ativas"]
                    nova_lista = []
                    alterado = False

                    for item in lista_original:
                        id_direto = item.get("id_carona")
                        ids_conexao = item.get("ids_caronas", [])

                        if id_direto == id_carona or id_carona in ids_conexao:
                            alterado = True
                        else:
                            nova_lista.append(item)

                    if alterado:
                        dados_usuario["corridas_ativas"] = nova_lista
                        with open(caminho, "w", encoding="utf-8") as f:
                            json.dump(dados_usuario, f, ensure_ascii=False, indent=4)

            # 1. Primeiro: Abre, limpa e reescreve o arquivo do MOTORISTA
            if caminho_motorista:
                limpar_arquivo_usuario(caminho_motorista)

            # 2. Segundo: Pega a lista pronta de caminhos dos passageiros e limpa um por um
            for caminho_passageiro in caminhos_passageiros:
                limpar_arquivo_usuario(caminho_passageiro)

            return True, "Carona ativa removida com sucesso do motorista e de todos os passageiros!"
            
        else:
            return False, f"Erro: Ação '{acao}' não reconhecida para tipo múltiplo."