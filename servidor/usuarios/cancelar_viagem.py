from .gerenciador_de_caronas_ativas import gerenciar_carona_global
from .gerenciador_de_usuario import escrita_cliente

def cancelar_viagem(acao, dado):# 
    if acao == "CANCELAR_VIAGEM":# aqui o dao é o id da carona 
        dados_requisicao = {"id_carona": dado}
        sucesso, resultado = gerenciar_carona_global("CANCELAR_VIAGEM", dados_requisicao)
        
        if not sucesso:
            return False, resultado
        #pegando id da carona e a lista dos pasageiros afetados  
        ids_passageiros = resultado.get("ids_passageiros", [])
        id_carona_apagada = resultado.get("id_carona")
        
        print(f"Carona {id_carona_apagada} removida. Passageiros afetados: {ids_passageiros}")
        
        return True, ids_passageiros, id_carona_apagada
    elif acao =="APAGAR_ID_ATIVO":
     sucesso, mensagem = escrita_cliente("REMOVER_CARONA_ATIVA",dado)#aqui o dado é o id de corida,usuario, mas dados necesarios
     return sucesso,mensagem
    elif acao == "CANCELAR_CARONA_PASSAGEIRO":
       sucesso,mensagem=gerenciar_carona_global("CANCELAR_CARONA_PASSAGEIRO",dado)
       return sucesso,mensagem