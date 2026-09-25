import tkinter as tk
from tkinter import messagebox, ttk
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

    lbl_vul = tk.Label(resultado_frame, text="", justify="left", anchor="nw",
                       bg=COR_FUNDO, fg=COR_VIOLETA_CLARO,
                       cursor="hand2", font=("Arial", 9, "underline"))
    lbl_vul.pack(fill="x")

    def mostrar_vulnerabilidades(ativo):
        if len(ativo["vulnerabilidades"]) == 0:
            messagebox.showinfo("Vulnerabilidades", "Esse ativo nao tem vulnerabilidades!")
            return

        janela_lista = tk.Toplevel(estado.root)
        janela_lista.title("Vulnerabilidades")
        janela_lista.geometry("760x300")
        janela_lista.configure(bg=COR_PAINEL)

        tk.Label(
            janela_lista,
            text=ativo["nome"],
            font=("Arial", 12, "bold"),
            bg=COR_PAINEL,
            fg=COR_TEXTO
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
                f"Local: {ativo_encontrado.get('local', '')}"
            )
            lbl_resultado.config(text=texto, fg=COR_TEXTO)

            lbl_vul.config(
                text=f"Total de Vulnerabilidades: {len(ativo_encontrado['vulnerabilidades'])}"
            )
            lbl_vul.bind("<Button-1>", lambda e, a=ativo_encontrado: mostrar_vulnerabilidades(a))
        else:
            lbl_resultado.config(text="Ativo nao encontrado com este ID.", fg="#ff8080")
            lbl_vul.config(text="")
            lbl_vul.unbind("<Button-1>")

    tk.Button(janela_ver, text="Pesquisar", command=pesquisar, width=15,
              bg=COR_VIOLETA, fg=COR_TEXTO,
              activebackground=COR_VIOLETA_CLARO,
              activeforeground=COR_TEXTO).pack(pady=5)
