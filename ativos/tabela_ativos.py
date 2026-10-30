import tkinter as tk
from tkinter import messagebox, ttk

from algoritmos.cvss import formatar, nota_de_dict
from api.servicos_api import pegar_ativos
from config import COR_PAINEL, COR_TEXTO
from dominio.excecoes import ErroValidacao
from persistencia import estado


def texto_cvss(vul):
    try:
        return formatar(nota_de_dict(vul))
    except ErroValidacao:
        return "?"


def maior_cvss(ativo):
    notas = []
    for vul in ativo.get("vulnerabilidades", []):
        try:
            notas.append(nota_de_dict(vul))
        except ErroValidacao:
            continue
    return max(notas) if notas else None


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
    janela_lista.geometry("800x300")
    janela_lista.configure(bg=COR_PAINEL)
    tk.Label(
        janela_lista,
        text=ativo["nome"],
        font=("Arial", 12, "bold"),
        bg=COR_PAINEL,
        fg=COR_TEXTO
    ).pack(pady=10)
    pior = maior_cvss(ativo)
    if pior is not None:
        tk.Label(
            janela_lista,
            text="Maior CVSS: " + formatar(pior),
            bg=COR_PAINEL,
            fg=COR_TEXTO
        ).pack()
    colunas_vul = ("numero", "vulnerabilidade", "cvss", "responsavel", "tratamento", "progresso")
    tabela_vul = ttk.Treeview(janela_lista, columns=colunas_vul, show="headings")
    tabela_vul.heading("numero", text="")
    tabela_vul.heading("vulnerabilidade", text="Vulnerabilidades")
    tabela_vul.heading("cvss", text="CVSS")
    tabela_vul.heading("responsavel", text="Responsavel")
    tabela_vul.heading("tratamento", text="Tratamento")
    tabela_vul.heading("progresso", text="Progresso")
    tabela_vul.column("numero", width=40, anchor="center")
    tabela_vul.column("vulnerabilidade", width=180, anchor="w")
    tabela_vul.column("cvss", width=120, anchor="center")
    tabela_vul.column("responsavel", width=140, anchor="w")
    tabela_vul.column("tratamento", width=180, anchor="w")
    tabela_vul.column("progresso", width=80, anchor="center")
    numero = 1
    for vul in ativo["vulnerabilidades"]:
        tabela_vul.insert("", "end", values=(
            numero,
            vul["nome"],
            texto_cvss(vul),
            vul.get("responsavel", ""),
            vul.get("tratamento", ""),
            str(vul.get("progresso", 0)) + "/10"
        ))
        numero = numero + 1
    tabela_vul.pack(fill="both", expand=True, padx=10, pady=10)
