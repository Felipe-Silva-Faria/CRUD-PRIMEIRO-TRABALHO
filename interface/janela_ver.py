import tkinter as tk
from tkinter import messagebox
from api.servicos_api import pegar_ativos
from config import COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_VIOLETA, COR_VIOLETA_CLARO
from persistencia import estado

# Acao do Botao Ver (Pesquisa por ID usando estrutura de dicionario)
def abrir_janela_ver():
    janela_ver = tk.Toplevel(estado.root)
    janela_ver.title("Pesquisar Ativo por ID")
    janela_ver.geometry("450x350")
    janela_ver.configure(bg=COR_PAINEL)

    tk.Label(janela_ver, text="Digite o ID do Ativo:", font=("Arial", 10, "bold"),
             bg=COR_PAINEL, fg=COR_TEXTO).pack(pady=10)
    entry_id = tk.Entry(janela_ver, width=20, font=("Arial", 11))
    entry_id.pack(pady=5)

    resultado_frame = tk.Frame(janela_ver, bd=1, relief="solid", padx=10, pady=10,
                               bg=COR_FUNDO)
    resultado_frame.pack(fill="both", expand=True, padx=15, pady=15)

    lbl_resultado = tk.Label(resultado_frame, text="Nenhum ativo pesquisado.",
                             justify="left", font=("Arial", 9), anchor="nw",
                             bg=COR_FUNDO, fg=COR_TEXTO)
    lbl_resultado.pack(fill="both", expand=True)

    def pesquisar():
        pesquisa_id_str = entry_id.get().strip()
        if not pesquisa_id_str.isdigit():
            messagebox.showerror("Erro", "Digite um ID valido (numero inteiro)!")
            return
        pesquisa_id = int(pesquisa_id_str)

        # Criando a estrutura simples de dicionario para mapear ID -> Ativo
        dicionario_ativos = {}
        for item in pegar_ativos():
            dicionario_ativos[item["id"]] = item

        # Busca rapida baseada em dicionario (Chave: ID)
        ativo_encontrado = dicionario_ativos.get(pesquisa_id)

        if ativo_encontrado:
            texto = (
                f"ID: {ativo_encontrado['id']}\n"
                f"Nome: {ativo_encontrado['nome']}\n"
                f"Tipo: {ativo_encontrado.get('tipo', '')}\n"
                f"Local: {ativo_encontrado.get('local', '')}\n"
                f"Total de Vulnerabilidades: {len(ativo_encontrado['vulnerabilidades'])}"
            )
            lbl_resultado.config(text=texto, fg=COR_TEXTO)
        else:
            lbl_resultado.config(text="Ativo nao encontrado com este ID.", fg="#ff8080")

    tk.Button(janela_ver, text="Pesquisar", command=pesquisar, width=15,
              bg=COR_VIOLETA, fg=COR_TEXTO,
              activebackground=COR_VIOLETA_CLARO,
              activeforeground=COR_TEXTO).pack(pady=5)
