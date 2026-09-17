import json
import os
from datetime import datetime
import networkx as nx
from .gerenciador_de_caronas_ativas import gerenciar_carona_global


def buscar_carona(procurar_carona, grafo):
    try:
        saida = procurar_carona.get("cidade_saida")
        chegada = procurar_carona.get("cidade_chegada")

        # Leitura segura via gerenciador global com Mutex
        sucesso, resposta = gerenciar_carona_global("LEITURA", {})
        if not sucesso:
            return False, f"Erro ao ler caronas ativas: {resposta}"

        try:
            caronas_ativas = json.loads(resposta)
        except json.JSONDecodeError:
            caronas_ativas = {}

        if not caronas_ativas:
            return True, []

        caronas_diretas = []
        caronas_conexao = []

        # 1. Busca por Caronas DIRETAS
        for id_carona, dados in caronas_ativas.items():
            rota = dados.get("rota", [])
            
            if saida in rota and chegada in rota:
                idx_saida = rota.index(saida)
                idx_chegada = rota.index(chegada)

                if idx_saida < idx_chegada:
                    tem_vagas = True
                    preco_total = 0.0

                    for i in range(idx_saida, idx_chegada):
                        nome_trecho = f"{rota[i]} -> {rota[i+1]}"
                        vagas_trecho = dados.get("vagas_por_trecho", {}).get(nome_trecho, 0)
                        if vagas_trecho <= 0:
                            tem_vagas = False
                            break
                        
                        preco_total += dados.get("precos_trechos", {}).get(nome_trecho, 0.0)

                    if tem_vagas:
                        horarios_trecho = {c: dados["horarios_trechos"].get(c) for c in rota[idx_saida:idx_chegada+1]}
                        pontos_trecho = {c: dados["pontos_parada"].get(c) for c in rota[idx_saida:idx_chegada+1]}

                        caronas_diretas.append({
                            "tipo": "DIRETA",
                            "id_carona": id_carona,
                            "motorista": dados.get("motorista"),
                            "carro": dados.get("carro"),
                            "cor_carro": dados.get("cor_carro"),
                            "data": dados.get("data"),
                            "trecho_solicitado": f"{saida} até {chegada}",
                            "horarios": horarios_trecho,
                            "pontos_parada": pontos_trecho,
                            "preco_total": preco_total
                        })

        if caronas_diretas:
            return True, caronas_diretas

        # 2. Auxílio do Grafo para encontrar cidades de conexão válidas fisicamente
        cidades_conexao_validas = set()
        if grafo:
            try:
                for path in nx.all_simple_paths(grafo, source=saida, target=chegada, cutoff=3):
                    for cidade in path[1:-1]:
                        cidades_conexao_validas.add(cidade)
            except nx.NetworkXNoPath:
                pass

        # 3. Busca por CONEXÃO (Validando Data, Horário e Vagas por trecho)
        for id_c1, dados1 in caronas_ativas.items():
            rota1 = dados1.get("rota", [])
            if saida not in rota1:
                continue
            idx_s = rota1.index(saida)
            data_c1 = dados1.get("data")

            for i in range(idx_s + 1, len(rota1)):
                cidade_conexao = rota1[i] 

                if cidades_conexao_validas and cidade_conexao not in cidades_conexao_validas:
                    continue

                for id_c2, dados2 in caronas_ativas.items():
                    if id_c1 == id_c2:
                        continue
                    
                    rota2 = dados2.get("rota", [])
                    if cidade_conexao not in rota2 or chegada not in rota2:
                        continue
                    
                    idx_cx = rota2.index(cidade_conexao)
                    idx_c = rota2.index(chegada)

                    if idx_cx < idx_c:
                        # VALIDAÇÃO 1: A data da carona 2 deve ser exatamente a mesma da carona 1
                        data_c2 = dados2.get("data")
                        if data_c1 != data_c2:
                            continue

                        # VALIDAÇÃO 2: Valida vagas na Carona 1 (todos os trechos do trajeto parcial)
                        vagas_c1_ok = True
                        for t in range(idx_s, rota1.index(cidade_conexao)):
                            nome_t = f"{rota1[t]} -> {rota1[t+1]}"
                            if dados1.get("vagas_por_trecho", {}).get(nome_t, 0) <= 0:
                                vagas_c1_ok = False
                                break
                        if not vagas_c1_ok:
                            continue

                        # VALIDAÇÃO 3: Valida vagas na Carona 2 (todos os trechos do trajeto parcial)
                        vagas_c2_ok = True
                        for t in range(idx_cx, idx_c):
                            nome_t = f"{rota2[t]} -> {rota2[t+1]}"
                            if dados2.get("vagas_por_trecho", {}).get(nome_t, 0) <= 0:
                                vagas_c2_ok = False
                                break
                        if not vagas_c2_ok:
                            continue

                        # VALIDAÇÃO 4: Validação de Horário (chegada da C1 vs partida da C2 na cidade de conexão)
                        hora_chegada_c1_str = dados1.get("horarios_trechos", {}).get(cidade_conexao)
                        hora_partida_c2_str = dados2.get("horarios_trechos", {}).get(cidade_conexao)

                        if hora_chegada_c1_str and hora_partida_c2_str:
                            try:
                                t_chegada = datetime.strptime(hora_chegada_c1_str, "%H:%M")
                                t_partida = datetime.strptime(hora_partida_c2_str, "%H:%M")

                                # A partida da segunda carona precisa ser posterior à chegada da primeira
                                if t_partida > t_chegada:
                                    preco_c1 = sum(dados1.get("precos_trechos", {}).get(f"{rota1[t]} -> {rota1[t+1]}", 0.0) for t in range(idx_s, rota1.index(cidade_conexao)))
                                    preco_c2 = sum(dados2.get("precos_trechos", {}).get(f"{rota2[t]} -> {rota2[t+1]}", 0.0) for t in range(idx_cx, idx_c))
                                    preco_total = preco_c1 + preco_c2

                                    caronas_conexao.append({
                                        "tipo": "CONEXAO",
                                        "ids_caronas": [id_c1, id_c2],
                                        "trecho_1": {
                                            "id_carona": id_c1,
                                            "motorista": dados1.get("motorista"),
                                            "trecho": f"{saida} até {cidade_conexao}",
                                            "chegada_conexao": hora_chegada_c1_str
                                        },
                                        "trecho_2": {
                                            "id_carona": id_c2,
                                            "motorista": dados2.get("motorista"),
                                            "trecho": f"{cidade_conexao} até {chegada}",
                                            "partida_conexao": hora_partida_c2_str
                                        },
                                        "data": data_c1,
                                        "preco_total": preco_total
                                    })
                            except ValueError:
                                continue

        if caronas_conexao:
            return True, caronas_conexao

        return True, []

    except Exception as e:
        return False, f"Erro interno ao buscar caronas: {str(e)}"