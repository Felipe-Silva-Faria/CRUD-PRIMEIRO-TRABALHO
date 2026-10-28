import tkinter as tk
from tkinter import ttk

from algoritmos.cvss import descrever_vetor
from dominio.excecoes import ErroCRUD
from interface.moderna import tema
from interface.moderna.componentes import Badge, Botao, Cartao, Rotulo, Tabela, limpar
from interface.moderna.paginas.base import Pagina


class PaginaDetalhes(Pagina):
    def construir(self):
        direita = self.cabecalho("Detalhes da Vulnerabilidade", "Visualize e gerencie todas as informações.")
        Botao(direita, "←  Voltar", lambda: self.app.navegar("vulnerabilidades"), "secundario").pack()
        self._id = None
        cartao = Cartao(self, padx=22, pady=16)
        cartao.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        self._topo = tk.Frame(cartao, bg=tema.CARTAO)
        self._topo.pack(fill="x", pady=(0, 12))
        abas = ttk.Notebook(cartao)
        abas.pack(fill="both", expand=True)
        self._geral = tk.Frame(abas, bg=tema.CARTAO, padx=12, pady=12)
        self._vetor = tk.Frame(abas, bg=tema.CARTAO, padx=12, pady=12)
        self._risco = tk.Frame(abas, bg=tema.CARTAO, padx=12, pady=12)
        abas.add(self._geral, text="  Geral  ")
        abas.add(self._vetor, text="  Vetor CVSS  ")
        abas.add(self._risco, text="  Risco  ")
        self._tab_vetor = Tabela(self._vetor, [("metrica", "Métrica", 240, "w"), ("valor", "Valor", 80, "center")],
                                 altura=8)
        self._tab_vetor.pack(fill="both", expand=True)

    def carregar(self, id_registro=None, **_):
        id_registro = id_registro or self._id
        try:
            r = self.painel.vulnerabilidade(id_registro)
        except ErroCRUD:
            self._id = None
            self.app.navegar("vulnerabilidades")
            return
        self._id = r.id
        cor = tema.cor_severidade(r.severidade)
        limpar(self._topo)
        Rotulo(self._topo, r.vul.nome, (tema.FAMILIA, 17, "bold")).pack(side="left")
        Badge(self._topo, r.severidade, cor).pack(side="left", padx=12)
        Badge(self._topo, r.status, tema.cor_progresso(r.vul.progresso)).pack(side="left")
        Botao(self._topo, "Excluir", self._excluir, "perigo").pack(side="right")
        Botao(self._topo, "✎  Editar", lambda: self.app.navegar("nova_vulnerabilidade", id_registro=r.id)).pack(
            side="right", padx=8)

        limpar(self._geral)
        for coluna in (0, 1):
            self._geral.columnconfigure(coluna, weight=1, uniform="g")
        esq = tk.Frame(self._geral, bg=tema.CARTAO)
        esq.grid(row=0, column=0, sticky="nsew")
        dir_ = tk.Frame(self._geral, bg=tema.CARTAO)
        dir_.grid(row=0, column=1, sticky="nsew")
        self._par(esq, "ID", r.id)
        self._par(esq, "Responsável", r.vul.responsavel or "-")
        self._par(esq, "Plano de tratamento", r.vul.tratamento or "-")
        self._par(dir_, "CVSS base", f"{r.vul.cvss:.1f} ({r.severidade})", cor)
        self._par(dir_, "Vetor", r.vul.vetor_cvss or "não informado (nota digitada)")
        self._par(dir_, "Ativo afetado", f"{r.ativo.nome} · {r.ativo.tipo.rotulo} · {r.ativo.local}")
        self._par(dir_, "Recomendação para o ativo", r.ativo.recomendacao())

        self._tab_vetor.carregar(list(enumerate(descrever_vetor(r.vul.vetor_cvss).items()))
                                 if r.vul.vetor_cvss else [])

        limpar(self._risco)
        residual = r.vul.risco_residual()
        Rotulo(self._risco, f"Risco residual: {residual:.2f}", (tema.FAMILIA, 16, "bold"),
               tema.VIOLETA_CLARO).pack(anchor="w")
        Rotulo(self._risco, f"R = CVSS × (10 − progresso) / 10 = {r.vul.cvss:.1f} × (10 − {r.vul.progresso}) / 10",
               tema.F_NORMAL, tema.TEXTO_SUAVE).pack(anchor="w", pady=(2, 8))
        ttk.Progressbar(self._risco, style="Violeta.Horizontal.TProgressbar", maximum=10,
                        value=r.vul.progresso, length=420).pack(anchor="w")
        Rotulo(self._risco, "Se este ativo for comprometido (BFS sobre o dependencias.json):",
               tema.F_NEGRITO).pack(anchor="w", pady=(14, 4))
        try:
            impacto = self.painel.raio_de_impacto(r.ativo.id)
        except ErroCRUD as erro:
            Rotulo(self._risco, str(erro), tema.F_PEQUENA, tema.VERMELHO).pack(anchor="w")
            return
        if len(impacto) <= 1:
            Rotulo(self._risco, "Nenhuma dependência cadastrada a partir deste ativo (veja a página Riscos).",
                   tema.F_PEQUENA, tema.TEXTO_SUAVE).pack(anchor="w")
        for item in impacto:
            Rotulo(self._risco, f"  {'→ ' * item['saltos']}{item['ativo'].nome}   "
                                f"({item['saltos']} salto(s), risco propagado x = {item['risco_propagado']:.2f})",
                   tema.F_NORMAL).pack(anchor="w")

    @staticmethod
    def _par(mestre, rotulo, valor, cor=tema.TEXTO):
        Rotulo(mestre, rotulo, tema.F_PEQUENA, tema.TEXTO_APAGADO).pack(anchor="w", pady=(8, 0))
        Rotulo(mestre, valor, tema.F_NORMAL, cor, wraplength=420, justify="left").pack(anchor="w")

    def _excluir(self):
        if self._id and self.confirmar(f"Excluir a vulnerabilidade {self._id}?"):
            try:
                self.painel.remover_vulnerabilidade(self._id)
            except ErroCRUD as erro:
                self.erro(erro)
                return
            self._id = None
            self.app.navegar("vulnerabilidades")
