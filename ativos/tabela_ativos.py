import tkinter as tk
from tkinter import messagebox, ttk
from persistencia import estado
from config import COR_PAINEL, COR_TEXTO
from api.servicos_api import pegar_ativos


# atualiza tabela
def atualizar_tabela():
    estado.ativos_salvos.clear()
    for item in estado.tabela.get_children():
        estado.tabela.delete(item)
    for item in pegar_ativos():
        linha = estado.tabela.insert(
            "", "end",
            values=(
                item["id"],
                item["nome"],
                item.get("tipo", ""),
                item.get("local", ""),
                len(item["vulnerabilidades"])
            )
        )
        estado.ativos_salvos[linha] = item
    if estado.modo_offline is True:
        estado.titulo_box.config(text="Ativos TI  (offline - txt)")


# mostra as vulnerabilidades quando clica no numero (agora e a coluna 5)
def clicou_no_numero(event):
    if estado.tabela.identify_column(event.x) != "#5":
        return
    linha = estado.tabela.identify_row(event.y)
    if linha == "":
        return
    ativo = estado.ativos_salvos[linha]
    if len(ativo["vulnerabilidades"]) == 0:
        messagebox.showinfo(
            "Vulnerabilidades",
            "Esse ativo nao tem vulnerabilidades!"
        )
        return

    janela_lista = tk.Toplevel(estado.root)
    janela_lista.title("Vulnerabilidades")
    janela_lista.geometry("760x300")
    janela_lista.configure(bg=COR_PAINEL)

    tk.Label(
        janela_lista, text=ativo["nome"], font=("Arial", 12, "bold"),
        bg=COR_PAINEL, fg=COR_TEXTO
    ).pack(pady=10)

    colunas_vul = ("numero", "vulnerabilidade", "severidade", "responsavel", "tratamento", "progresso")
    tabela_vul = ttk.Treeview(janela_lista, columns=colunas_vul, show="headings")
    tabela_vul.heading("numero", text="")
    tabela_vul.heading("vulnerabilidade", text="Vulnerabilidades")
    tabela_vul.heading("severidade", text="Severidade")
    tabela_vul.heading("responsavel", text="Responsavel")
    tabela_vul.heading("tratamento", text="Tratamento")
    tabela_vul.heading("progresso", text="Progresso")
    tabela_vul.column("numero", width=40, anchor="center")
    tabela_vul.column("vulnerabilidade", width=180, anchor="w")
    tabela_vul.column("severidade", width=90, anchor="center")
    tabela_vul.column("responsavel", width=140, anchor="w")
    tabela_vul.column("tratamento", width=180, anchor="w")
    tabela_vul.column("progresso", width=80, anchor="center")

    numero = 1
    for vul in ativo["vulnerabilidades"]:
        tabela_vul.insert("", "end", values=(
            numero,
            vul["nome"],
            vul["severidade"],
            vul.get("responsavel", ""),
            vul.get("tratamento", ""),
            str(vul.get("progresso", 0)) + "/10"
        ))
        numero = numero + 1

    tabela_vul.pack(fill="both", expand=True, padx=10, pady=10)
