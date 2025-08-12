from database.db import init
from interface.janela_principal import iniciar_sistema

if __name__ == "__main__":
    init()            # cria tabelas e semeia catálogos
    iniciar_sistema() # abre a UI

