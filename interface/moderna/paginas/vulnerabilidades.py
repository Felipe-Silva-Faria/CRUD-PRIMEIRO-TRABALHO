import tkinter as tk
from dominio.excecoes import ErroCRUD
from interface.moderna import tema
from interface.moderna.componentes import Botao, Cartao, Combo, Rotulo, Tabela
from interface.moderna.paginas.base import Pagina

TODAS = "Todas"
FAIXAS = {"Qualquer CVSS": None, "CVSS ≥ 4.0": 4.0, "CVSS ≥ 7.0": 7.0, "CVSS ≥ 9.0": 9.0}
COLUNAS = [("id", "ID", 80, "w"), ("nome", "Vulnerabilidade", 240, "w"), ("severidade", "Severidade", 100, "w"),
           ("cvss", "CVSS", 60, "center"), ("ativo", "Ativo", 170, "w"), ("status", "Status", 120, "w"),
           ("progresso", "Progresso", 80, "center"), ("risco", "Risco residual", 100, "center")]


class PaginaVulnerabilidades(Pagina):
    def construir(self):
        direita = self.cabecalho("Vulnerabilidades", "Gerencie, filtre e acompanhe as vulnerabilidades.")
        Botao(direita, "+  Nova Vulnerabilidade", lambda: self.app.navegar("nova_vulnerabilidade")).pack()
        corpo = Cartao(self, padx=16, pady=14)
        corpo.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        # ---------------- filtros (topo) ----------------
        filtros = tk.Frame(corpo, bg=tema.CARTAO)
        filtros.pack(fill="x", pady=(0, 12))
        caixa = tk.Frame(filtros, bg=tema.CARTAO_ALTO, highlightthickness=1, highlightbackground=tema.BORDA)
        caixa.pack(side="left", fill="x", expand=True)
        Rotulo(caixa, " ⌕ ", tema.F_NEGRITO, tema.TEXTO_SUAVE).pack(side="left")
        self._busca = tk.StringVar()
        tk.Entry(caixa, textvariable=self._busca, bg=tema.CARTAO_ALTO, fg=tema.TEXTO, relief="flat",
                 insertbackground=tema.TEXTO, font=tema.F_NORMAL).pack(side="left", fill="x", expand=True, ipady=6)
        self._sev = Combo(filtros, "", [TODAS, *tema.ORDEM_SEVERIDADE[:4]], ao_mudar=lambda _v: self._aplicar(),
                          largura=10)
        self._sev.valor = TODAS
        self._sev.pack(side="left", padx=(10, 0))
        self._cvss = Combo(filtros, "", list(FAIXAS), ao_mudar=lambda _v: self._aplicar(), largura=13)
        self._cvss.valor = "Qualquer CVSS"
        self._cvss.pack(side="left", padx=(8, 0))
        self._abertas = tk.BooleanVar(value=False)
        tk.Checkbutton(filtros, text="Só abertas", variable=self._abertas, command=self._aplicar,
                       bg=tema.CARTAO, fg=tema.TEXTO, selectcolor=tema.CARTAO_ALTO,
                       activebackground=tema.CARTAO).pack(side="left", padx=8)

        # ---------------- tabela (criada, mas empacotada so no fim) ----------------
        # altura=8 e so o tamanho MINIMO: com espaco sobrando a tabela cresce (expand=True)
        self._tabela = Tabela(corpo, COLUNAS, ao_ordenar=lambda *_: self._aplicar(),
                              ao_duplo_clique=self._abrir, altura=8)
        self._tabela.marcar_ordenacao("cvss", True)

        # ---------------- rodape preso embaixo (empacotado ANTES da tabela) ----------------
        rodape = tk.Frame(corpo, bg=tema.CARTAO)
        rodape.pack(side="bottom", fill="x", pady=(10, 0))
        self._info = Rotulo(rodape, "", tema.F_PEQUENA, tema.TEXTO_SUAVE)
        self._info.pack(side="left")
        Botao(rodape, "Excluir", self._excluir, "perigo").pack(side="right")
        Botao(rodape, "Editar", lambda: self._abrir(self._tabela.selecionado(), editar=True),
              "secundario").pack(side="right", padx=8)
        Botao(rodape, "Ver detalhes", lambda: self._abrir(self._tabela.selecionado()), "secundario").pack(side="right")

        # a tabela ocupa o espaco que sobrar entre os filtros e o rodape
        self._tabela.pack(fill="both", expand=True)

        # so liga a busca "ao digitar" depois que a tabela e o rodape existem
        self._busca.trace_add("write", lambda *_: self._aplicar())

    def carregar(self, texto=None, **_):
        if texto is not None:
            self._busca.set(texto)
        else:
            self._aplicar()

    def _aplicar(self):
        coluna = self._tabela.coluna_ordenada or "cvss"
        registros = self.painel.vulnerabilidades(
            texto=self._busca.get(), severidade=None if self._sev.valor == TODAS else self._sev.valor,
            cvss_min=FAIXAS.get(self._cvss.valor), somente_abertas=self._abertas.get(),
            ordenar_por=coluna, reverso=self._tabela.reverso)
        self._tabela.carregar([(r.id, (r.id, r.vul.nome, f"● {r.severidade}", f"{r.vul.cvss:.1f}", r.ativo.nome,
                                       r.status, f"{r.vul.progresso}/10", f"{r.vul.risco_residual():.2f}"))
                               for r in registros])
        self._info.configure(text=f"{len(registros)} resultado(s) · ordenado por '{coluna}' com "
                                  f"'{self.painel.algoritmo}' em {self.painel.ultima_ordenacao_ms:.3f} ms")

    def _abrir(self, id_registro, editar=False):
        if id_registro:
            self.app.navegar("nova_vulnerabilidade" if editar else "detalhes", id_registro=id_registro)

    def _excluir(self):
        id_registro = self._tabela.selecionado()
        if id_registro and self.confirmar(f"Excluir a vulnerabilidade {id_registro}?"):
            try:
                self.painel.remover_vulnerabilidade(id_registro)
            except ErroCRUD as erro:
                self.erro(erro)
