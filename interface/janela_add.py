import tkinter as tk
from tkinter import messagebox
from persistencia import estado
from config import COR_PAINEL, COR_TEXTO, COR_VIOLETA, COR_VIOLETA_CLARO
from interface.janela_vulnerabilidade import abrir_janela_vulnerabilidade
import re


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
        nome = entry_Nome.get().strip()
        tipo = entry_Tipo.get().strip()
        local = entry_Local.get().strip()

        # Nome
        if not nome:
            messagebox.showerror("Erro", "O nome é obrigatório!")
            return

        if len(nome) < 3:
            messagebox.showerror("Erro", "O nome deve possuir pelo menos 3 caracteres!")
            return

        if not re.fullmatch(r"[A-Za-zÀ-ÿ0-9\s\-_]+", nome) or not re.search(r"[A-Za-zÀ-ÿ]", nome):
            messagebox.showerror("Erro", "O nome contém caracteres inválidos!")
            return

        # Tipo
        if not tipo:
            messagebox.showerror("Erro", "O tipo é obrigatório!")
            return

        if len(tipo) < 3:
            messagebox.showerror("Erro", "O tipo deve possuir pelo menos 3 caracteres!")
            return

        if not re.fullmatch(r"[A-Za-zÀ-ÿ0-9\s\-_]+", nome) or not re.search(r"[A-Za-zÀ-ÿ]", nome):
            messagebox.showerror("Erro", "O nome contém caracteres inválidos!")
            return

        # Local
        if not local:
            messagebox.showerror("Erro", "O local é obrigatório!")
            return

        if len(local) < 3:
            messagebox.showerror("Erro", "O local deve possuir pelo menos 3 caracteres!")
            return

        if not re.fullmatch(r"[A-Za-zÀ-ÿ0-9\s\-_]+", nome) or not re.search(r"[A-Za-zÀ-ÿ]", nome):
            messagebox.showerror("Erro", "O nome contém caracteres inválidos!")
            return

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
