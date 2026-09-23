import tkinter as tk
from tkinter import messagebox, ttk
import persistencia.estado as estado
from config import COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_VIOLETA, COR_VIOLETA_CLARO
from api.servicos_api import atualizar_ativo_api_ou_txt
from ativos.tabela_ativos import atualizar_tabela


# Acao do Botao Editar
def abrir_janela_editar():
    selecionado = estado.tabela.selection()
    if not selecionado:
        messagebox.showerror("Erro", "Selecione um ativo na tabela para editar!")
        return

    ativo_atual = estado.ativos_salvos[selecionado[0]]

    janela_edit = tk.Toplevel(estado.root)
    janela_edit.title("Editar Ativo")
    janela_edit.geometry("780x760")
    janela_edit.configure(bg=COR_PAINEL)

    lbl_opts = {"bg": COR_PAINEL, "fg": COR_TEXTO}

    tk.Label(janela_edit, text="Nome:", **lbl_opts).pack(pady=(10, 0))
    entry_Nome = tk.Entry(janela_edit, width=40)
    entry_Nome.pack()
    entry_Nome.insert(0, ativo_atual["nome"])

    tk.Label(janela_edit, text="Tipo:", **lbl_opts).pack(pady=(10, 0))
    entry_Tipo = tk.Entry(janela_edit, width=40)
    entry_Tipo.pack()
    entry_Tipo.insert(0, ativo_atual.get("tipo", ""))

    tk.Label(janela_edit, text="Local:", **lbl_opts).pack(pady=(10, 0))
    entry_Local = tk.Entry(janela_edit, width=40)
    entry_Local.pack()
    entry_Local.insert(0, ativo_atual.get("local", ""))

    vulnerabilidades = list(ativo_atual["vulnerabilidades"])

    tk.Label(janela_edit, text="Vulnerabilidade(s)", font=("Arial", 12, "bold"),
             **lbl_opts).pack(pady=10)

    colunas_vul = ("numero", "vulnerabilidade", "severidade", "responsavel", "tratamento", "progresso")
    tabela_vul = ttk.Treeview(janela_edit, columns=colunas_vul, show="headings", height=6)
    tabela_vul.heading("numero", text="")
    tabela_vul.heading("vulnerabilidade", text="Vulnerabilidade")
    tabela_vul.heading("severidade", text="Severidade")
    tabela_vul.heading("responsavel", text="Responsavel")
    tabela_vul.heading("tratamento", text="Tratamento")
    tabela_vul.heading("progresso", text="Progresso")
    tabela_vul.column("numero", width=40, anchor="center")
    tabela_vul.column("vulnerabilidade", width=170, anchor="w")
    tabela_vul.column("severidade", width=90, anchor="center")
    tabela_vul.column("responsavel", width=140, anchor="w")
    tabela_vul.column("tratamento", width=170, anchor="w")
    tabela_vul.column("progresso", width=80, anchor="center")

    def recarregar_tabela_vul():
        for item in tabela_vul.get_children():
            tabela_vul.delete(item)
        for i, vul in enumerate(vulnerabilidades):
            tabela_vul.insert("", "end", values=(
                i + 1,
                vul["nome"],
                vul["severidade"],
                vul.get("responsavel", ""),
                vul.get("tratamento", ""),
                str(vul.get("progresso", 0)) + "/10"
            ))

    recarregar_tabela_vul()
    tabela_vul.pack(fill="both", expand=True, padx=10)

    def deletar_vulnerabilidade_selecionada():
        sel_v = tabela_vul.selection()
        if not sel_v:
            messagebox.showerror("Erro", "Selecione uma vulnerabilidade para deletar!")
            return
        idx = tabela_vul.index(sel_v[0])
        vulnerabilidades.pop(idx)
        recarregar_tabela_vul()

    tk.Button(janela_edit, text="Deletar Vulnerabilidade Selecionada",
              command=deletar_vulnerabilidade_selecionada,
              bg=COR_FUNDO, fg="#ff8080",
              activebackground=COR_VIOLETA_CLARO).pack(pady=5)

    tk.Label(janela_edit, text="Nova Vulnerabilidade:", **lbl_opts).pack(pady=(5, 0))
    entry_Vul = tk.Entry(janela_edit, width=40)
    entry_Vul.pack()

    tk.Label(janela_edit, text="Grau de severidade:", **lbl_opts).pack(pady=(5, 0))
    severidade = tk.StringVar()
    severidade.set("baixa")

    frame_severidade = tk.Frame(janela_edit, bg=COR_PAINEL)
    frame_severidade.pack()

    radio_opts = {
        "bg": COR_PAINEL,
        "fg": COR_TEXTO,
        "selectcolor": COR_FUNDO,
        "activebackground": COR_PAINEL,
        "activeforeground": COR_TEXTO,
    }

    tk.Radiobutton(frame_severidade, text="Baixa", variable=severidade, value="baixa",
                   **radio_opts).pack(side="left", padx=5)
    tk.Radiobutton(frame_severidade, text="Media", variable=severidade, value="media",
                   **radio_opts).pack(side="left", padx=5)
    tk.Radiobutton(frame_severidade, text="Alta", variable=severidade, value="alta",
                   **radio_opts).pack(side="left", padx=5)

    # responsavel pela vulnerabilidade
    tk.Label(janela_edit, text="Responsavel:", **lbl_opts).pack(pady=(5, 0))
    entry_Responsavel = tk.Entry(janela_edit, width=40)
    entry_Responsavel.pack()

    # tratamento + progresso do tratamento (vao juntos)
    tk.Label(janela_edit, text="Tratamento:", **lbl_opts).pack(pady=(5, 0))
    entry_Tratamento = tk.Entry(janela_edit, width=40)
    entry_Tratamento.pack()

    tk.Label(janela_edit, text="Progresso do tratamento (0 a 10):", **lbl_opts).pack(pady=(5, 0))

    progresso = tk.IntVar()
    progresso.set(0)

    frame_progresso = tk.Frame(janela_edit, bg=COR_PAINEL)
    frame_progresso.pack()

    tk.Scale(
        frame_progresso,
        variable=progresso,
        from_=0,
        to=10,
        orient="horizontal",
        length=300,
        tickinterval=1,
        resolution=1,
        bg=COR_PAINEL,
        fg=COR_TEXTO,
        troughcolor=COR_FUNDO,
        highlightthickness=0,
        activebackground=COR_VIOLETA_CLARO,
    ).pack(side="left", padx=5)

    def add_vulnerabilidade():
        if entry_Vul.get() == "":
            messagebox.showerror("Erro", "Escreva a vulnerabilidade!")
            return
        if entry_Responsavel.get() == "" or entry_Tratamento.get() == "":
            messagebox.showerror("Erro", "Preencha o responsavel e o tratamento!")
            return
        vulnerabilidades.append({
            "nome": entry_Vul.get(),
            "severidade": severidade.get(),
            "responsavel": entry_Responsavel.get(),
            "tratamento": entry_Tratamento.get(),
            "progresso": progresso.get()
        })
        recarregar_tabela_vul()
        entry_Vul.delete(0, "end")
        severidade.set("baixa")
        entry_Responsavel.delete(0, "end")
        entry_Tratamento.delete(0, "end")
        progresso.set(0)

    tk.Button(janela_edit, text="Adicionar Vulnerabilidade", command=add_vulnerabilidade,
              bg=COR_VIOLETA, fg=COR_TEXTO,
              activebackground=COR_VIOLETA_CLARO,
              activeforeground=COR_TEXTO).pack(pady=5)

    def salvar_edicao():
        if entry_Nome.get() == "" or entry_Tipo.get() == "" or entry_Local.get() == "":
            messagebox.showerror("Erro", "Preencha o nome, o tipo e o local!")
            return
        dados = {
            "nome": entry_Nome.get(),
            "tipo": entry_Tipo.get(),
            "local": entry_Local.get(),
            "vulnerabilidades": vulnerabilidades
        }
        if atualizar_ativo_api_ou_txt(ativo_atual["id"], dados):
            messagebox.showinfo("Sucesso", "Ativo atualizado com sucesso!")
            janela_edit.destroy()
            atualizar_tabela()
        else:
            messagebox.showerror("Erro", "Nao foi possivel atualizar o ativo.")

    tk.Button(janela_edit, text="Salvar Alteracoes", command=salvar_edicao,
              bg=COR_VIOLETA_CLARO, fg=COR_TEXTO,
              activebackground=COR_VIOLETA,
              activeforeground=COR_TEXTO,
              font=("Arial", 10, "bold")).pack(pady=15)
