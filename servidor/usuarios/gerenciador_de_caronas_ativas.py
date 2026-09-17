import json
import os
import threading

# Mutex global único para proteger o arquivo 
lock_caronas_ativas = threading.Lock()

def gerenciar_carona_global(acao, dados):
   
    # Caminho para o arquivo 
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_ativas = os.path.join(diretorio_atual, "..", "caronas_ativas.json")

    # toda escrita passa pelo mutex tratanto concorrencia 
    with lock_caronas_ativas:
        caronas_ativas = {}
        if os.path.exists(caminho_ativas):
            with open(caminho_ativas, "r", encoding="utf-8") as f:
                try:
                    caronas_ativas = json.load(f)
                except json.JSONDecodeError:
                    caronas_ativas = {}

        # Trata as ações suportadas no arquivo global
        if acao == "CADASTRAR":
            id_carona = dados.get("id_carona")
            if not id_carona:
                return False, "Erro: ID da carona não fornecido."
            
            caronas_ativas[id_carona] = dados
            
            # Salva as alterações no arquivo global
            with open(caminho_ativas, "w", encoding="utf-8") as f:
                json.dump(caronas_ativas, f, ensure_ascii=False, indent=4)
                
            return True, "Carona cadastrada com sucesso no arquivo global!"

        elif acao == "PEGAR_VAGA":
            tipo = dados.get("tipo")
            vaga_info = dados.get("vaga")
            email_hash = dados.get("email")  
            nome = dados.get("nome")         

            if not email_hash or not nome:
                return False, "Erro: Dados do usuário incompletos (nome ou identificador ausentes)."

            if tipo == "DIRETA":
                id_carona = vaga_info.get("id_carona")
                if id_carona not in caronas_ativas:
                    return False, "Erro: Esta carona não existe mais."
                
                carona = caronas_ativas[id_carona]
                rota = carona.get("rota", [])
                trecho_str = vaga_info.get("trecho_solicitado", "")
                
                partes = trecho_str.split(" até ")
                if len(partes) != 2:
                    return False, "Erro: Formato de trecho inválido na seleção."
                
                origem, destino = partes[0].strip(), partes[1].strip()
                if origem not in rota or destino not in rota:
                    return False, "Erro: Rota da carona foi alterada."
                
                idx_s = rota.index(origem)
                idx_c = rota.index(destino)
                
                # Validação de vagas sob o Mutex
                for i in range(idx_s, idx_c):
                    nome_trecho = f"{rota[i]} -> {rota[i+1]}"
                    if carona["vagas_por_trecho"].get(nome_trecho, 0) <= 0:
                        return False, f"Erro: O trecho {nome_trecho} lotou enquanto você escolhia!"
                
                # Efetivação: desconta vaga e adiciona o dicionário com nome e hash na lista
                for i in range(idx_s, idx_c):
                    nome_trecho = f"{rota[i]} -> {rota[i+1]}"
                    carona["vagas_por_trecho"][nome_trecho] -= 1
                    carona["passageiros_por_trecho"][nome_trecho].append({
                        "nome": nome,
                        "email_hash": email_hash
                    })

            elif tipo == "CONEXAO":
                t1 = vaga_info.get("trecho_1", {})
                t2 = vaga_info.get("trecho_2", {})
                
                id_c1 = t1.get("id_carona")
                id_c2 = t2.get("id_carona")
                
                if id_c1 not in caronas_ativas or id_c2 not in caronas_ativas:
                    return False, "Erro: Uma das caronas da conexão não está mais disponível."
                
                carona1 = caronas_ativas[id_c1]
                carona2 = caronas_ativas[id_c2]
                
                rota1 = carona1.get("rota", [])
                origem1, destino1 = t1.get("trecho").split(" até ")
                idx_s1, idx_c1 = rota1.index(origem1.strip()), rota1.index(destino1.strip())
                
                rota2 = carona2.get("rota", [])
                origem2, destino2 = t2.get("trecho").split(" até ")
                idx_s2, idx_c2 = rota2.index(origem2.strip()), rota2.index(destino2.strip())
                
                # Validação de vagas em ambos os carros
                for i in range(idx_s1, idx_c1):
                    nt = f"{rota1[i]} -> {rota1[i+1]}"
                    if carona1["vagas_por_trecho"].get(nt, 0) <= 0:
                        return False, f"Erro: O trecho {nt} da primeira carona lotou!"
                        
                for i in range(idx_s2, idx_c2):
                    nt = f"{rota2[i]} -> {rota2[i+1]}"
                    if carona2["vagas_por_trecho"].get(nt, 0) <= 0:
                        return False, f"Erro: O trecho {nt} da segunda carona lotou!"
                
                # Efetivação no Carro 1
                for i in range(idx_s1, idx_c1):
                    nt = f"{rota1[i]} -> {rota1[i+1]}"
                    carona1["vagas_por_trecho"][nt] -= 1
                    carona1["passageiros_por_trecho"][nt].append({
                        "nome": nome,
                        "email_hash": email_hash
                    })
                    
                # Efetivação no Carro 2
                for i in range(idx_s2, idx_c2):
                    nt = f"{rota2[i]} -> {rota2[i+1]}"
                    carona2["vagas_por_trecho"][nt] -= 1
                    carona2["passageiros_por_trecho"][nt].append({
                        "nome": nome,
                        "email_hash": email_hash
                    })
            else:
                return False, "Erro: Tipo de carona desconhecido."

            # Salva o estado atualizado no arquivo JSON global[cite: 2]
            with open(caminho_ativas, "w", encoding="utf-8") as f:
                json.dump(caronas_ativas, f, ensure_ascii=False, indent=4)
                
            return True, "Vaga reservada com sucesso em todos os trechos!"
           
        elif acao == "LEITURA":
            if not os.path.exists(caminho_ativas):
                return True, json.dumps({}, ensure_ascii=False)
            
            # Retorna o dicionário completo de caronas ativas serializado em string JSON
            return True, json.dumps(caronas_ativas, ensure_ascii=False)
        elif acao == "CANCELAR_VIAGEM":
            id_carona = dados.get("id_carona")
            if not id_carona:
                return False, "Erro: ID da carona não fornecido."

            if id_carona not in caronas_ativas:
                return False, "Erro: Carona não encontrada no sistema global."

            carona = caronas_ativas[id_carona]
            passageiros_por_trecho = carona.get("passageiros_por_trecho", {})
            
            # Varre todos os trechos e coleta o hash de email único de cada passageiro
            ids_passageiros = []
            for nome_trecho, lista_passageiros in passageiros_por_trecho.items():
                for p in lista_passageiros:
                    hash_email = p.get("email_hash")
                    if hash_email and hash_email not in ids_passageiros:
                        ids_passageiros.append(hash_email)

            # Remove a carona do dicionário global
            del caronas_ativas[id_carona]

            # Salva o arquivo global atualizado[cite: 2]
            with open(caminho_ativas, "w", encoding="utf-8") as f:
                json.dump(caronas_ativas, f, ensure_ascii=False, indent=4)
                
            # Retorna a lista de hashes dos passageiros e o id da carona apagada
            return True, {"ids_passageiros": ids_passageiros, "id_carona": id_carona}


        elif acao =="CANCELAR_CARONA_PASSAGEIRO":
            id_carona = dados.get("id_carona")
            email_hash = dados.get("hash_email")

            if not id_carona or not email_hash:
                return False, "Erro: ID da carona ou hash do usuário não fornecidos."

            if id_carona not in caronas_ativas:
                return False, "Erro: Carona não encontrada no sistema global."

            carona = caronas_ativas[id_carona]
            vagas_por_trecho = carona.get("vagas_por_trecho", {})
            passageiros_por_trecho = carona.get("passageiros_por_trecho", {})
            
            removido_algum = False

            # Varre todos os trechos da carona para retirar o passageiro e devolver a vaga
            for nome_trecho, lista_passageiros in passageiros_por_trecho.items():
                # Filtra a lista removendo o passageiro que tem o hash correspondente
                nova_lista = [p for p in lista_passageiros if p.get("email_hash") != email_hash]
                
                # Se o tamanho da lista diminuiu, significa que ele estava nesse trecho
                if len(nova_lista) < len(lista_passageiros):
                    removido_algum = True
                    passageiros_por_trecho[nome_trecho] = nova_lista
                    # Devolve +1 vaga para o trecho correspondente
                    vagas_por_trecho[nome_trecho] = vagas_por_trecho.get(nome_trecho, 0) + 1

            if not removido_algum:
                return False, "Erro: Você não está cadastrado como passageiro nesta carona."

            # Salva as alterações atualizadas no arquivo global de caronas ativas
            with open(caminho_ativas, "w", encoding="utf-8") as f:
                json.dump(caronas_ativas, f, ensure_ascii=False, indent=4)
                
            return True, "Vaga cancelada com sucesso e liberada no sistema global!"
        else:
            return False, f"Erro: Ação '{acao}' não reconhecida pelo gerenciador global."