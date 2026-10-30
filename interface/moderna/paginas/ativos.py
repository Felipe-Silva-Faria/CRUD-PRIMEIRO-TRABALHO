import tkinter as tk

from dominio.enums import TipoAtivo
from dominio.excecoes import ErroCRUD
from interface.moderna import tema
from interface.moderna.componentes import Botao, Campo, Cartao, Combo, Rotulo, Tabela
from interface.moderna.paginas.base import Pagina

COLUNAS = [("id", "ID", 70, "w"), ("nome", "Nome", 190, "w"), ("tipo", "Tipo", 130, "w"),
           ("local", "Local", 130, "w"), ("vulnerabilidades", "Vulns", 60, "center"),
           ("cvss", "Maior CVSS", 90, "center"), ("risco", "Risco total", 90, "center")]


class PaginaAtivos(Pagina):
    def construir(self):
        direita = self.cabecalho("Ativos", "Inventário de ativos de TI.")
        Botao(direita, "+  Novo Ativo", self._limpar).pack()
        self._editando = None
        corpo = tk.Frame(self, bg=tema.PAINEL)
        corpo.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        corpo.columnconfigure(0, weight=3)
        corpo.columnconfigure(1, weight=1, minsize=300)
        corpo.rowconfigure(0, weight=1)

        # ---------------- lista (esquerda) ----------------
        lista = Cartao(corpo, padx=14, pady=12)
        lista.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        # altura=8 e so o tamanho MINIMO: com espaco sobrando a tabela cresce (expand=True)
        self._tabela = Tabela(lista, COLUNAS, ao_ordenar=lambda *_: self.recarregar(),
                              ao_duplo_clique=self._editar, altura=8)
        self._tabela.marcar_ordenacao("nome", False)

        # 1o: botoes presos embaixo (empacotados ANTES da tabela)
        acoes = tk.Frame(lista, bg=tema.CARTAO)
        acoes.pack(side="bottom", fill="x", pady=(10, 0))
        Botao(acoes, "Excluir", self._excluir, "perigo").pack(side="right")
        Botao(acoes, "Editar", lambda: self._editar(self._tabela.selecionado()), "secundario").pack(
            side="right", padx=8)
        Botao(acoes, "+ Vulnerabilidade neste ativo", self._nova_vul, "secundario").pack(side="right")

        # 2o: a tabela ocupa o espaco que sobrar
        self._tabela.pack(fill="both", expand=True)

        # ---------------- formulario (direita) ----------------
        form = Cartao(corpo, padx=18, pady=10)
        form.grid(row=0, column=1, sticky="nsew")
        self._titulo_form = Rotulo(form, "Novo ativo", tema.F_NEGRITO, tema.VIOLETA_CLARO)
        self._titulo_form.pack(anchor="w")
        self._nome = Campo(form, "Nome / hostname", True, "Ex: Servidor Web")
        self._nome.pack(fill="x")
        self._tipo = Combo(form, "Tipo", [t.rotulo for t in TipoAtivo], True, editavel=True,
                           dica="(ou digite outro)")
        self._tipo.pack(fill="x")
        self._local = Campo(form, "Local / setor", True, "Ex: Data Center")
        self._local.pack(fill="x")
        botoes = tk.Frame(form, bg=tema.CARTAO)
        botoes.pack(fill="x", pady=(16, 4))
        Botao(botoes, "Salvar", self._salvar).pack(side="right")
        Botao(botoes, "Limpar", self._limpar, "secundario").pack(side="right", padx=8)

    def carregar(self, **_):
        coluna = self._tabela.coluna_ordenada or "nome"
        ativos = self.painel.ativos(ordenar_por=coluna, reverso=self._tabela.reverso)
        self._tabela.carregar([
            (a.id, (a.id, a.nome, a.to_dict()["tipo"], a.local, len(a.vulnerabilidades),
                    "-" if a.maior_cvss() is None else f"{a.maior_cvss():.1f}", f"{a.risco_total():.2f}"))
            for a in ativos])

    def _limpar(self):
        self._editando = None
        self._titulo_form.configure(text="Novo ativo")
        self._nome.valor = self._local.valor = ""
        self._tipo.valor = TipoAtivo.SERVIDOR.rotulo

    def _editar(self, ativo_id):
        if not ativo_id:
            return
        ativo = self.painel.ativo(ativo_id)
        self._editando = ativo.id
        self._titulo_form.configure(text=f"Editando ativo {ativo.id}")
        self._nome.valor, self._local.valor = ativo.nome, ativo.local
        self._tipo.valor = ativo.to_dict()["tipo"]

    def _salvar(self):
        try:
            self.painel.salvar_ativo({"nome": self._nome.valor, "tipo": self._tipo.valor,
                                      "local": self._local.valor}, self._editando)
        except ErroCRUD as erro:
            self.erro(erro)
            return
        self._limpar()

    def _excluir(self):
        ativo_id = self._tabela.selecionado()
        if not ativo_id:
            return
        ativo = self.painel.ativo(ativo_id)
        if self.confirmar(f"Excluir '{ativo.nome}' e suas {len(ativo.vulnerabilidades)} vulnerabilidade(s)?\n"
                          "As dependências ligadas a ele também serão removidas."):
            try:
                self.painel.remover_ativo(ativo.id)
            except ErroCRUD as erro:
                self.erro(erro)

    def _nova_vul(self):
        if self._tabela.selecionado():
            self.app.navegar("nova_vulnerabilidade", ativo_id=self._tabela.selecionado())
