from interface.janela_principal import carregar_pagina_ativos, criar_janela

# start
if __name__ == "__main__":
    root = criar_janela()
    carregar_pagina_ativos()
    root.mainloop()
