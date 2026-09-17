import networkx as nx  # biblioteca para grafos


def validar_rota(rota, grafo):
   # verificar se a cidade é válida no grafo de cidades
  for cidade in rota:
    if cidade not in grafo:
      return (
          False,
          f"A cidade '{cidade}' informada na rota não existe no mapa da Bahia. Verifique a ortografia e primeira letra maiúscula.",
      )

  # 2. Validação de Trechos (Continuidade rodoviária)
  for i in range(len(rota) - 1):
    origem_trecho = rota[i]
    destino_trecho = rota[i + 1]

    # Utiliza o NetworkX para verificar se existe caminho entre o trecho atual e o próximo
    if not nx.has_path(grafo, origem_trecho, destino_trecho):
      return (
          False,
          f"Não há estradas conectando '{origem_trecho}' a '{destino_trecho}'"
          f" no trecho {i+1}.",
      )

  return True, "Rota válida com sucesso!"