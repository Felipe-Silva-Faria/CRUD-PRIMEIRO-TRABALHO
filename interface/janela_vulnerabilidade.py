import tkinter as tk
from tkinter import messagebox, ttk
from api.servicos_api import mandar_ativo
from ativos.tabela_ativos import atualizar_tabela, texto_cvss
from config import ARQUIVO_TXT, COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_VIOLETA, COR_VIOLETA_CLARO
from dominio.excecoes import ErroValidacao
from interface.campo_cvss import CampoCVSS
from persistencia import estado


def abrir_janela_vulnerabilidade(nome, tipo, local):
    janela_vul = tk.Toplevel(estado.root)
    janela_vul.title("Vulnerabilidade(s)")
    janela_vul.geometry("900x760")
    janela_vul.configure(bg=COR_PAINEL)
    vulnerabilidades = []
    lbl_opts = {"bg": COR_PAINEL, "fg": COR_TEXTO}
    tk.Label(
        janela_vul, text="Vulnerabilidade(s)", font=("Arial", 12, "bold"), **lbl_opts
    ).pack(pady=10)
    colunas_vul = ("numero", "vulnerabilidade", "cvss", "responsavel", "tratamento", "progresso")
    tabela_vul = ttk.Treeview(janela_vul, columns=colunas_vul, show="headings", height=8)
    tabela_vul.heading("numero", text="")
    tabela_vul.heading("vulnerabilidade", text="Vulnerabilidade")
    tabela_vul.heading("cvss", text="CVSS")
    tabela_vul.heading("responsavel", text="Responsavel")
    tabela_vul.heading("tratamento", text="Tratamento")
    tabela_vul.heading("progresso", text="Progresso")
    tabela_vul.column("numero", width=40, anchor="center")
    tabela_vul.column("vulnerabilidade", width=180, anchor="w")
    tabela_vul.column("cvss", width=110, anchor="center")
    tabela_vul.column("responsavel", width=140, anchor="w")
    tabela_vul.column("tratamento", width=180, anchor="w")
    tabela_vul.column("progresso", width=80, anchor="center")
    tabela_vul.pack(fill="both", expand=True, padx=10)

    def mostrar_tratamento_completo(event):
        sel_v = tabela_vul.selection()
        if not sel_v:
            return
        idx = tabela_vul.index(sel_v[0])
        janela_texto = tk.Toplevel(janela_vul)
        janela_texto.title("Tratamento completo")
        janela_texto.geometry("520x320")
        janela_texto.configure(bg=COR_PAINEL)
        caixa = tk.Text(janela_texto, wrap="word", bg=COR_FUNDO, fg=COR_TEXTO)
        caixa.insert("1.0", vulnerabilidades[idx]["tratamento"])
        caixa.config(state="disabled")
        caixa.pack(fill="both", expand=True, padx=10, pady=10)
    tabela_vul.bind("<Double-1>", mostrar_tratamento_completo)
    tk.Label(janela_vul, text="Vulnerabilidade:", **lbl_opts).pack(pady=(10, 0))
    entry_Vul = tk.Entry(janela_vul, width=50)
    entry_Vul.pack()
    tk.Label(janela_vul, text="CVSS (nota 0.0 a 10.0 ou vetor CVSS:3.1/...):", **lbl_opts).pack(pady=(10, 0))
    campo_cvss = CampoCVSS(janela_vul, bg=COR_PAINEL, fg=COR_TEXTO)
    campo_cvss.pack(padx=10)
    tk.Label(janela_vul, text="Responsavel:", **lbl_opts).pack(pady=(10, 0))
    entry_Responsavel = tk.Entry(janela_vul, width=50)
    entry_Responsavel.pack()
    tk.Label(janela_vul, text="Tratamento:", **lbl_opts).pack(pady=(10, 0))
    frame_tratamento = tk.Frame(janela_vul, bg=COR_PAINEL)
    frame_tratamento.pack()
    entry_Tratamento = tk.Text(frame_tratamento, width=50, height=5, wrap="word")
    entry_Tratamento.pack(side="left")
    scroll_tratamento = ttk.Scrollbar(frame_tratamento, orient="vertical",
                                      command=entry_Tratamento.yview)
    entry_Tratamento.configure(yscrollcommand=scroll_tratamento.set)
    scroll_tratamento.pack(side="right", fill="y")
    tk.Label(janela_vul, text="Progresso do tratamento (0 a 10):", **lbl_opts).pack(pady=(10, 0))
    progresso = tk.IntVar()
    progresso.set(0)
    frame_progresso = tk.Frame(janela_vul, bg=COR_PAINEL)
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
    ).pack(side="left", padx=10)

    def add_vulnerabilidade():
        if entry_Vul.get() == "":
            messagebox.showerror(
                "Erro",
                "Escreva a vulnerabilidade!"
            )
            return
        texto_tratamento = entry_Tratamento.get("1.0", "end").strip()
        if entry_Responsavel.get() == "" or texto_tratamento == "":
            messagebox.showerror(
                "Erro",
                "Preencha o responsavel e o tratamento!"
            )
            return
        try:
            nota_cvss = campo_cvss.obter()
        except ErroValidacao as erro:
            messagebox.showerror(
                "Erro",
                "CVSS invalido: " + erro.mensagem
            )
            return
        if not 0 <= progresso.get() <= 10:
            messagebox.showerror(
                "Erro",
                "O progresso deve estar entre 0 e 10!"
            )
            return
        vulnerabilidade = {
            "nome": entry_Vul.get(),
            "cvss": nota_cvss["cvss"],
            "vetor_cvss": nota_cvss["vetor_cvss"],
            "responsavel": entry_Responsavel.get(),
            "tratamento": texto_tratamento,
            "progresso": progresso.get()
        }
        vulnerabilidades.append(vulnerabilidade)
        tabela_vul.insert("", "end", values=(
            len(vulnerabilidades),
            entry_Vul.get(),
            texto_cvss(vulnerabilidade),
            entry_Responsavel.get(),
            texto_tratamento.replace("\n", " "),
            str(progresso.get()) + "/10"
        ))
        entry_Vul.delete(0, "end")
        campo_cvss.limpar()
        entry_Responsavel.delete(0, "end")
        entry_Tratamento.delete("1.0", "end")
        progresso.set(0)

    def salvar():
        dados = {
            "nome": nome,
            "tipo": tipo,
            "local": local,
            "vulnerabilidades": vulnerabilidades
        }
        if mandar_ativo(dados) is True:
            if estado.modo_offline is True:
                messagebox.showinfo(
                    "Sucesso",
                    "Ativo salvo no arquivo " + ARQUIVO_TXT + "!"
                )
            else:
                messagebox.showinfo(
                    "Sucesso",
                    "Ativo Salvo!"
                )
            janela_vul.destroy()
            atualizar_tabela()
    frame_botoes = tk.Frame(janela_vul, bg=COR_PAINEL)
    frame_botoes.pack(pady=20)
    btn_opts_janela = {
        "bg": COR_VIOLETA,
        "fg": COR_TEXTO,
        "activebackground": COR_VIOLETA_CLARO,
        "activeforeground": COR_TEXTO,
        "font": ("Arial", 9, "bold"),
    }
    tk.Button(
        frame_botoes,
        text="Add",
        command=add_vulnerabilidade,
        **btn_opts_janela
    ).pack(side="left", padx=5)
    tk.Button(
        frame_botoes,
        text="Salvar",
        command=salvar,
        **btn_opts_janela
    ).pack(side="left", padx=5)
