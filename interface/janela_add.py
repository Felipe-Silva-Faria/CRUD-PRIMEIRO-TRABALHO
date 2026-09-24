import tkinter as tk
from tkinter import messagebox
from persistencia import estado
from config import COR_PAINEL, COR_TEXTO, COR_VIOLETA, COR_VIOLETA_CLARO
from interface.janela_vulnerabilidade import abrir_janela_vulnerabilidade


# add
def abrir_janela_add():
    janela_add = tk.Toplevel(estado.root)
    janela_add.title("Novo Ativo")
    janela_add.geometry("320x300")
    janela_add.configure(bg=COR_PAINEL)

    lbl_opts = {"bg": COR_PAINEL, "fg": COR_TEXTO}

    tk.Label(janela_add, text="Nome:", **lbl_opts).pack(pady=(10, 0))
    entry_Nome = tk.Entry(janela_add)
    entry_Nome.pack()

    tk.Label(janela_add, text="Tipo:", **lbl_opts).pack(pady=(10, 0))
    entry_Tipo = tk.Entry(janela_add)
    entry_Tipo.pack()

    tk.Label(janela_add, text="Local:", **lbl_opts).pack(pady=(10, 0))
    entry_Local = tk.Entry(janela_add)
    entry_Local.pack()

    def salvar():
        if entry_Nome.get() == "" or entry_Tipo.get() == "" or entry_Local.get() == "":
            messagebox.showerror(
                "Erro",
                "Preencha o nome, o tipo e o local!"
            )
            return
        nome = entry_Nome.get()
        tipo = entry_Tipo.get()
        local = entry_Local.get()
        janela_add.destroy()
        abrir_janela_vulnerabilidade(nome, tipo, local)

    tk.Button(
        janela_add,
        text="Salvar",
        command=salvar,
        bg=COR_VIOLETA,
        fg=COR_TEXTO,
        activebackground=COR_VIOLETA_CLARO,
        activeforeground=COR_TEXTO,
        font=("Arial", 9, "bold")
    ).pack(pady=20)
