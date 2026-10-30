import tkinter as tk
from algoritmos.cvss import descrever_vetor, faixa_qualitativa, interpretar_entrada
from dominio.excecoes import ErroCRUD, ErroValidacao
from interface.moderna import tema
from interface.moderna.componentes import AreaTexto, Botao, Campo, Cartao, Combo, Rotulo
from interface.moderna.paginas.base import Pagina, mensagem_de
from servicos.painel import separar_id


class PaginaNovaVulnerabilidade(Pagina):
    def construir(self):
        self.cabecalho("Nova Vulnerabilidade", "Preencha os dados da vulnerabilidade.")
        self._id_registro = None
        cartao = Cartao(self, padx=22, pady=10)
        cartao.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        cartao.columnconfigure(0, weight=3, uniform="f")
        cartao.columnconfigure(1, weight=2, uniform="f")
        esquerda = tk.Frame(cartao, bg=tema.CARTAO)
        esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 24))
        direita = tk.Frame(cartao, bg=tema.CARTAO)
        direita.grid(row=0, column=1, sticky="nsew")

        self.nome = Campo(esquerda, "Nome da vulnerabilidade", True, "Ex: CVE-2021-44228 Log4Shell")
        self.nome.pack(fill="x")
        self.responsavel = Campo(esquerda, "Responsável", placeholder="Ex: Ana Souza")
        self.responsavel.pack(fill="x")
        self.tratamento = AreaTexto(esquerda, "Plano de tratamento", altura=6)
        self.tratamento.pack(fill="x")

        self.ativo = Combo(direita, "Ativo afetado", [], True)
        self.ativo.pack(fill="x")
        self.cvss = Campo(direita, "CVSS", True, "9.8 ou CVSS:3.1/AV:N/AC:L/...", dica="(nota ou vetor)")
        self.cvss.pack(fill="x")
        self.cvss.entrada.bind("<KeyRelease>", lambda _e: self._previa())
        self.aviso = Rotulo(direita, "", tema.F_PEQUENA, tema.TEXTO_SUAVE, wraplength=360, justify="left")
        self.aviso.pack(anchor="w", pady=(4, 0))
        Rotulo(direita, "Progresso do tratamento (0 a 10)", tema.F_NEGRITO).pack(anchor="w", pady=(10, 0))
        self.progresso = tk.Scale(direita, from_=0, to=10, orient="horizontal", bg=tema.CARTAO, fg=tema.TEXTO,
                                  troughcolor=tema.CARTAO_ALTO, highlightthickness=0,
                                  activebackground=tema.VIOLETA, command=lambda _v: self._previa())
        self.progresso.pack(fill="x")
        self.previa = Rotulo(direita, "", tema.F_NEGRITO, tema.VIOLETA_CLARO)
        self.previa.pack(anchor="w", pady=(6, 0))

        botoes = tk.Frame(cartao, bg=tema.CARTAO)
        botoes.grid(row=1, column=0, columnspan=2, sticky="e", pady=(12, 4))
        Botao(botoes, "Cancelar", self._cancelar, "secundario").pack(side="left", padx=8)
        self._salvar_btn = Botao(botoes, "Salvar Vulnerabilidade", self._salvar)
        self._salvar_btn.pack(side="left")

    def carregar(self, id_registro=None, ativo_id=None, **_):
        self._id_registro = id_registro
        self._opcoes = {f"{a.id} - {a.nome}": a.id for a in self.painel.ativos()}
        self.ativo.definir_opcoes(self._opcoes)
        rotulo = {v: k for k, v in self._opcoes.items()}
        if id_registro is None:
            self._titulo.configure(text="Nova Vulnerabilidade")
            self._salvar_btn.configure(text="Salvar Vulnerabilidade")
            self.nome.valor = self.responsavel.valor = self.cvss.valor = ""
            self.tratamento.valor = ""
            self.progresso.set(0)
            self.ativo.valor = rotulo.get(int(ativo_id), "") if ativo_id else ""
        else:
            try:
                r = self.painel.vulnerabilidade(id_registro)
            except ErroCRUD:
                self._id_registro = None
                self.app.navegar("vulnerabilidades")
                return
            self._titulo.configure(text=f"Editar Vulnerabilidade {r.id}")
            self._salvar_btn.configure(text="Salvar alterações")
            self.nome.valor, self.responsavel.valor = r.vul.nome, r.vul.responsavel
            self.cvss.valor = r.vul.vetor_cvss or f"{r.vul.cvss:.1f}"
            self.tratamento.valor = r.vul.tratamento
            self.progresso.set(r.vul.progresso)
            self.ativo.valor = rotulo.get(r.ativo.id, "")
        self._previa()

    def _previa(self):
        texto = self.cvss.valor
        progresso = int(self.progresso.get())
        if not texto:
            self.aviso.configure(text="")
            self.previa.configure(text="")
            return
        try:
            nota, vetor = interpretar_entrada(texto)
        except ErroValidacao as erro:
            self.aviso.configure(text=f"✖ {mensagem_de(erro)}", fg=tema.VERMELHO)
            self.previa.configure(text="")
            return
        detalhe = ""
        if vetor:
            metricas = descrever_vetor(vetor)
            detalhe = " · ".join(f"{k}: {v}" for k, v in list(metricas.items())[:4]) + " ..."
        self.aviso.configure(text=f"✔ CVSS {nota:.1f} ({faixa_qualitativa(nota)})  {detalhe}",
                             fg=tema.cor_severidade(faixa_qualitativa(nota)))
        risco = nota * (10 - progresso) / 10
        self.previa.configure(text=f"Risco residual: {risco:.2f}  (= {nota:.1f} × (10 − {progresso}) / 10)")

    def _salvar(self):
        try:
            if self.ativo.valor not in self._opcoes:
                raise ErroValidacao("ativo", "selecione o ativo afetado")
            nota, vetor = interpretar_entrada(self.cvss.valor)
            dados = {"nome": self.nome.valor, "cvss": nota, "vetor_cvss": vetor,
                     "responsavel": self.responsavel.valor, "tratamento": self.tratamento.valor,
                     "progresso": int(self.progresso.get())}
            ativo_id = self._opcoes[self.ativo.valor]
            self.painel.salvar_vulnerabilidade(ativo_id, dados, self._id_registro)
        except ErroCRUD as erro:
            self.erro(erro)
            return
        if self._id_registro and separar_id(self._id_registro)[0] == ativo_id:
            self.app.navegar("detalhes", id_registro=self._id_registro)
        else:
            self.app.navegar("vulnerabilidades")

    def _cancelar(self):
        if self._id_registro:
            self.app.navegar("detalhes", id_registro=self._id_registro)
        else:
            self.app.navegar("vulnerabilidades")
