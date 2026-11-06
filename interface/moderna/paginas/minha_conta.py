import tkinter as tk

from dominio.excecoes import ErroCRUD
from dominio.permissoes import Autorizacao, origem_das_autorizacoes
from interface.moderna import tema
from interface.moderna.componentes import AreaTexto, Botao, CaixaSelecao, Cartao, Rotulo, Tabela, limpar, pedir_senha
from interface.moderna.paginas.base import Pagina


class PaginaMinhaConta(Pagina):
    def construir(self):
        self.cabecalho("Minha conta", "Seus dados, suas autorizações e pedidos de novos acessos.")
        self.contas = self.app.contas
        self._caixas = {}
        corpo = tk.Frame(self, bg=tema.PAINEL)
        corpo.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        corpo.columnconfigure(0, weight=1, uniform="c")
        corpo.columnconfigure(1, weight=1, uniform="c")

        esquerda = tk.Frame(corpo, bg=tema.PAINEL)
        esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._dados = Cartao(esquerda, padx=18, pady=14)
        self._dados.pack(fill="x")
        self._minhas = Cartao(esquerda, padx=18, pady=14)
        self._minhas.pack(fill="both", expand=True, pady=(12, 0))

        direita = tk.Frame(corpo, bg=tema.PAINEL)
        direita.grid(row=0, column=1, sticky="nsew")
        self._solicitar = Cartao(direita, padx=18, pady=14)
        self._solicitar.pack(fill="x")
        historico = Cartao(direita, padx=18, pady=14)
        historico.pack(fill="both", expand=True, pady=(12, 0))
        Rotulo(historico, "Meus pedidos", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(anchor="w")
        self._tab_pedidos = Tabela(historico, [
            ("data", "Data", 120, "w"), ("auts", "Autorizações", 220, "w"), ("status", "Situação", 90, "w"),
            ("motivo", "Observação", 160, "w"),
        ], altura=5)
        self._tab_pedidos.pack(fill="both", expand=True, pady=(6, 0))

    def carregar(self, **_):
        usuario = self.contas.usuario(self.app.nome_usuario)
        self._mostrar_dados(usuario)
        self._mostrar_autorizacoes(usuario)
        self._mostrar_solicitaveis(usuario)
        self._tab_pedidos.carregar([
            (p.id, (p.criada_em, ", ".join(Autorizacao.de_codigo(c).rotulo for c in p.autorizacoes),
                    p.status.capitalize(), p.motivo or "-"))
            for p in reversed(self.contas.pedidos_de(usuario.nome))])

    # Dados da conta
    def _mostrar_dados(self, usuario):
        quadro = self._dados
        limpar(quadro)
        Rotulo(quadro, "Dados da conta", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(anchor="w")
        for rotulo, valor in [("Usuário", usuario.nome), ("Nome", usuario.nome_completo or "-"),
                              ("E-mail", usuario.email or "-"), ("Funções", usuario.papel),
                              ("Conta criada em", usuario.criado_em)]:
            linha = tk.Frame(quadro, bg=tema.CARTAO)
            linha.pack(fill="x", pady=(4, 0))
            Rotulo(linha, f"{rotulo}:", tema.F_PEQUENA, tema.TEXTO_APAGADO, width=16, anchor="w").pack(side="left")
            Rotulo(linha, valor, tema.F_NORMAL).pack(side="left")

    # Autorizacoes do usuario
    def _mostrar_autorizacoes(self, usuario):
        quadro = self._minhas
        limpar(quadro)
        Rotulo(quadro, "Minhas autorizações", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(anchor="w")
        origem = origem_das_autorizacoes(usuario.funcoes, usuario.autorizacoes_extras)
        if not origem:
            Rotulo(quadro, "Nenhuma autorização.", tema.F_NORMAL, tema.TEXTO_SUAVE).pack(anchor="w")
        for grupo, autorizacoes in Autorizacao.grupos().items():
            minhas = [a for a in autorizacoes if a in origem]
            if not minhas:
                continue
            Rotulo(quadro, grupo, tema.F_PEQUENA, tema.TEXTO_SUAVE).pack(anchor="w", pady=(8, 0))
            for aut in minhas:
                linha = tk.Frame(quadro, bg=tema.CARTAO)
                linha.pack(fill="x")
                Rotulo(linha, f"✔ {aut.rotulo}", tema.F_NORMAL, tema.VERDE).pack(side="left", padx=(12, 0))
                Rotulo(linha, origem[aut], tema.F_PEQUENA, tema.TEXTO_APAGADO).pack(side="right")

    # Autorizacoes que podem ser pedidas
    def _mostrar_solicitaveis(self, usuario):
        quadro = self._solicitar
        limpar(quadro)
        Rotulo(quadro, "Solicitar autorizações", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(anchor="w")
        disponiveis = self.contas.solicitaveis_para(usuario.nome)
        self._caixas = {}
        if not disponiveis:
            Rotulo(quadro, "Não há autorizações disponíveis para solicitar (ou já há pedidos pendentes).",
                   tema.F_NORMAL, tema.TEXTO_SUAVE, wraplength=420, justify="left").pack(anchor="w", pady=(6, 0))
            return
        Rotulo(quadro, "Marque o que precisa e explique o motivo. Funções e autorizações de administração "
                       "só podem ser dadas por um administrador.", tema.F_PEQUENA, tema.TEXTO_APAGADO,
               wraplength=420, justify="left").pack(anchor="w")
        grupos = {}
        for aut in disponiveis:
            grupos.setdefault(aut.grupo, []).append(aut)
        for grupo, autorizacoes in grupos.items():
            Rotulo(quadro, grupo, tema.F_PEQUENA, tema.TEXTO_SUAVE).pack(anchor="w", pady=(8, 0))
            for aut in autorizacoes:
                caixa = CaixaSelecao(quadro, aut.rotulo)
                caixa.pack(anchor="w", padx=(12, 0))
                self._caixas[aut.codigo] = caixa
        self._justificativa = AreaTexto(quadro, "Justificativa", altura=2)
        self._justificativa.pack(fill="x")
        Botao(quadro, "Solicitar", self._solicitar_marcadas).pack(anchor="w", pady=(12, 0))

    def _pedir_senha(self, mensagem):
        return pedir_senha(self, "Confirmar solicitação", mensagem)

    # Acao do Botao SOLICITAR
    def _solicitar_marcadas(self):
        codigos = [c for c, cx in self._caixas.items() if cx.marcada]
        if not codigos:
            self.informar("Marque ao menos uma autorização.")
            return
        lista = "\n".join(f"• {Autorizacao.de_codigo(c).rotulo}" for c in codigos)
        senha = self._pedir_senha(f"Você vai solicitar:\n{lista}\n\nDigite sua senha para confirmar.")
        if senha is None:
            return
        try:
            self.contas.solicitar_autorizacoes(self.app.nome_usuario, senha, codigos, self._justificativa.valor)
        except ErroCRUD as erro:
            self.erro(erro)
            return
        self.informar("Solicitação enviada. Um administrador vai analisar o pedido.")
        self.recarregar()
