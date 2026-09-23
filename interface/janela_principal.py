import tkinter as tk
from tkinter import ttk
import persistencia.estado as estado
from ativos.acoes_ativos import deletar_ativo_selecionado
from config import COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_VIOLETA, COR_VIOLETA_CLARO
from janela_add import abrir_janela_add
from janela_editar import abrir_janela_editar
from janela_ver import abrir_janela_ver
from ativos.tabela_ativos import atualizar_tabela, clicou_no_numero


# Config janela
def criar_janela():
    root = tk.Tk()
    root.title("Primeiro Trabalho")
    root.geometry("900x650")
    root.configure(bg=COR_FUNDO)

    # estilo violeta da tabela
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure(
        "Treeview",
        background="#f3e9ff",
        fieldbackground="#f3e9ff",
        foreground="#1a001f",
        rowheight=24,
    )
    estilo.configure(
        "Treeview.Heading",
        background=COR_VIOLETA,
        foreground=COR_TEXTO,
        font=("Arial", 9, "bold"),
    )
    estilo.map("Treeview", background=[("selected", COR_VIOLETA_CLARO)])

    # Container
    coisa_frame = tk.Frame(root, bg=COR_PAINEL, bd=2, relief="groove")
    coisa_frame.place(
        relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.85
    )

    estado.root = root
    estado.coisa_frame = coisa_frame
    return root


def limpar_coisa():
    for widget in estado.coisa_frame.winfo_children():
        widget.destroy()


# Pagina principal
def carregar_pagina_ativos():
    limpar_coisa()

    # titulo
    top_frame = tk.Frame(estado.coisa_frame, bg=COR_PAINEL)
    top_frame.pack(fill="x", padx=15, pady=15)

    estado.titulo_box = tk.Label(
        top_frame,
        text="Ativos TI",
        font=("Arial", 14, "bold"),
        bg=COR_VIOLETA,
        fg=COR_TEXTO,
        padx=15,
        pady=5,
        relief="solid",
        bd=1,
    )
    estado.titulo_box.pack(side="left")

    # parte dbaixo
    bottom_frame = tk.Frame(estado.coisa_frame, bg=COR_PAINEL)
    bottom_frame.pack(side="bottom", fill="x", padx=15, pady=15)

    btn_opts = {
        "width": 10,
        "font": ("Arial", 9, "bold"),
        "bg": COR_VIOLETA,
        "fg": COR_TEXTO,
        "activebackground": COR_VIOLETA_CLARO,
        "activeforeground": COR_TEXTO,
        "relief": "raised",
    }

    tk.Button(
        bottom_frame,
        text="Add",
        command=abrir_janela_add,
        **btn_opts
    ).pack(side="left", padx=5)

    tk.Button(
        bottom_frame,
        text="Ver",
        command=abrir_janela_ver,
        **btn_opts
    ).pack(side="left", padx=5)

    tk.Button(
        bottom_frame,
        text="Editar",
        command=abrir_janela_editar,
        **btn_opts
    ).pack(side="left", padx=5)

    tk.Button(
        bottom_frame,
        text="DELETAR",
        command=deletar_ativo_selecionado,
        **btn_opts
    ).pack(side="left", padx=5)

    # tabela
    table_frame = tk.Frame(estado.coisa_frame, bg=COR_PAINEL)
    table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    colunas = ("id", "nome", "tipo", "local", "vulnerabilidade")
    estado.tabela = ttk.Treeview(
        table_frame, columns=colunas, show="headings", selectmode="browse"
    )

    estado.tabela.heading("id", text="ID")
    estado.tabela.heading("nome", text="NOME")
    estado.tabela.heading("tipo", text="TIPO")
    estado.tabela.heading("local", text="LOCAL")
    estado.tabela.heading("vulnerabilidade", text="VULNERABILIDADES")

    estado.tabela.column("id", width=70, anchor="center")
    estado.tabela.column("nome", width=170, anchor="w")
    estado.tabela.column("tipo", width=140, anchor="center")
    estado.tabela.column("local", width=170, anchor="center")
    estado.tabela.column("vulnerabilidade", width=130, anchor="center")

    # click no numero de vulnerabilidades
    estado.tabela.bind("<Button-1>", clicou_no_numero)

    # scroll
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=estado.tabela.yview)
    estado.tabela.configure(yscroll=scrollbar.set)

    estado.tabela.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    atualizar_tabela()
