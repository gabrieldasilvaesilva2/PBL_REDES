#  Sistema de Caronas Compartilhadas (PBL - Redes de Computadores)

Aplicação cliente-servidor desenvolvida em **Python** utilizando **Sockets TCP**, estruturada com arquitetura distribuída e containerizada via **Docker**. O sistema permite o cadastro de usuários (passageiros e motoristas), gerenciamento de caronas ativas, validação de rotas utilizando grafos e cancelamento de viagens.
Mas vale ressaltar que algumas funções estão inconsistentes devido a erro na estrutura de passagem de arquivo, o que acarreta em retornos vazios ou erros de execução.
# conexão multi threads ,
 ou seja, cada conexão do usuario gera uma nova threads (pode ser vuneravel em questão de escalabilidade)
 usanodo "import threading" nativo do Python 

Os usuários atuais rodam em host = "localhost" que só é visível na própria máquina, então é preferível rodar com Docker usando host = "host.docker.internal"  
 ou com o IP do servidor em questão: host = "ip_do_servidor" em outra máquina. 
 port = 12345


#Tecnologias Utilizadas
 **Python 3.11 / 3.13** (Linguagem principal)
* **Sockets TCP** (Comunicação de rede cliente-servidor baseada em JSON)
* **NetworkX** (Biblioteca para manipulação e validação de rotas em grafos baseados em adjacências)
* **Docker / Docker Desktop** (Isolamento e containerização da aplicação)

---

## Estrutura do Projeto
```text
PBL/
├── README.md               # Manual de instruções geral do projeto
├── requirements.txt        # Dependências globais (networkx==3.4.2)
│
├── servidor/
│   ├── servidor.py         # Código principal do servidor TCP
│   ├── Dockerfile          # Dockerfile do servidor
│   ├── mapa_adjacencias.json # Base de dados para o servidor gerar o  grafo que verifica existência de cidades/
|   |                           conexões entre elas antes de deixar cadastrar ou buscar carona 
│   ├── caronas_ativas.json # Armazenamento de caronas ativas globais
│   └── usuarios/           # Pasta com lógicas, validações e JSONs de usuários gerenciados pelo servidor
│       ├── cadastrar_carona.py      # recebe dados do tipo chave-valor para escrever em arquivo referente a 
|       |                             cadastro de usauario
│       ├── cadastrar_motorista.py   # recebe chave-valor, estrutura o arquivo e para escrita 
|       |                             para o arquivo responsável (formato JSON, nome é a hash do email)
│       ├── cadastro_usuarios.py     # recebe os dados do passageiro, estrutura em chave-valor 
|       |                               para o arquivo responsável (formato JSON, nome é a hash do email)
│       ├── cancelar_viagem.py       # tem chave-valor do id da viagem e o id do dono, que é a hash do email
│       ├── gerenciador_de_caronas_ativas.py # para tratar concorrência, toda escrita é feita no JSON geral. Passa
|       |                                      o mutex só libera um por vez, então ele gerencia a escrita,
|       |                                       tem vários if ação == "condição" e faz sua escrita segura 
│       ├── gerenciador_de_usuario.py # gerencia a escrita no JSON dos usuários, onde ficam as caronas, usando
|       |                               mutex também
│       ├── listar_caronas.py # lista as caronas encontradas para o usuario 
│       ├── login.py # autentica o usuário que tem nome e usuário logado, que é o próprio e-mail atribuído.
│       ├── pegar_carona.py #faz o passageiro se bincular a vaga por trecho
│       ├── validar_cidades.py # valida se a cidade existe com auxilio do grafo 
│       ├── jsons_motoristas/ # pasta onde os jsnos do motorista dicam salvos 
│       └── jsons_passageiros/ #pasta onde o jsom dos motoristas ficam salvos
│
├── passageiro/
│   ├── passageiro.py       # Script interativo do passageiro
│   └── Dockerfile.cliente  # Dockerfile do cliente passageiro
│
└── motorista/
    ├── motorista.py        # Script interativo do motorista
    └── Dockerfile.cliente  # Dockerfile do cliente motorista