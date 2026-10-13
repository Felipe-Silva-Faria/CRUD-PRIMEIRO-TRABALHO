from interface.janela_principal import carregar_pagina_ativos, criar_janela
from utilitarios.log import configurar_logs

if __name__ == "__main__":
    configurar_logs()
    root = criar_janela()
    carregar_pagina_ativos()
    root.mainloop()
