import tkinter as tk
from tkinter import ttk

from dominio.excecoes import ErroCRUD
from dominio.permissoes import Autorizacao, Funcao, autorizacoes_efetivas
from interface.moderna import tema
from interface.moderna.componentes import (
    Botao,
    CaixaSelecao,
    Campo,
    Cartao,
    Combo,
    Rotulo,
    Tabela,
    limpar,
    pedir_texto,
)
from interface.moderna.paginas.base import Pagina
from persistencia.usuarios import PENDENTE

COLUNAS_HISTORICO = [
    ("id", "Nº", 40, "center"), ("usuario", "Usuário", 110, "w"), ("status", "Decisão", 90, "w"),
    ("por", "Por", 100, "w"), ("quando", "Quando", 120, "w"), ("motivo", "Observação", 200, "w"),
]


class PaginaAcessos(Pagina):
    def construir(self):
        self.cabecalho("Acessos", "Usuários, funções, autorizações e solicitações.")
        self.contas = self.app.contas
        self._usuario_sel = None
        self._cadastro_sel = None
        self._pedido_sel = None
        self._caixas_funcao = {}
        self._caixas_extras = {}
        self._extras_marcados = set()
        self._abas = ttk.Notebook(self)
        self._abas.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        self._aba_usuarios = self._nova_aba("Usuários")
        self._aba_novo = self._nova_aba("Novo usuário")
        self._aba_cadastros = self._nova_aba("Cadastros")
        self._aba_pedidos = self._nova_aba("Autorizações")
        self._aba_funcoes = self._nova_aba("Funções")
        self._montar_usuarios()
        self._montar_novo()
        self._montar_cadastros()
        self._montar_pedidos()
        self._montar_funcoes()

    def _nova_aba(self, titulo):
        aba = tk.Frame(self._abas, bg=tema.PAINEL, pady=12)
        self._abas.add(aba, text=f"  {titulo}  ")
        return aba

    @property
    def _eu(self):
        return self.app.nome_usuario

    def _pode(self, autorizacao):
        return self.app.pode(autorizacao)

    def _executar(self, acao, sucesso=""):
        try:
            resultado = acao()
        except ErroCRUD as erro:
            self.erro(erro)
            return None
        if sucesso:
            self.informar(sucesso)
        self.app.atualizar_usuario()
        self.recarregar()
        return resultado

    @staticmethod
    def _bloqueado(mestre, autorizacao):
        Rotulo(mestre, f"Você não tem a autorização '{autorizacao.rotulo}'.", tema.F_NORMAL,
               tema.TEXTO_SUAVE, wraplength=340, justify="left").pack(anchor="w", padx=4, pady=8)

    @staticmethod
    def _historico(decididos):
        return [(p.id, (p.id, p.usuario, p.status.capitalize(), p.decidida_por, p.decidida_em, p.motivo or "-"))
                for p in reversed(decididos)]

    def _montar_usuarios(self):
        aba = self._aba_usuarios
        aba.columnconfigure(0, weight=3)
        aba.columnconfigure(1, weight=2, minsize=380)
        aba.rowconfigure(0, weight=1)
        lista = Cartao(aba, padx=14, pady=12)
        lista.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._tab_usuarios = Tabela(lista, [
            ("usuario", "Usuário", 110, "w"), ("nome", "Nome", 150, "w"), ("email", "E-mail", 180, "w"),
            ("funcoes", "Funções", 150, "w"), ("extras", "Extras", 60, "center"), ("status", "Status", 80, "w"),
        ], altura=10, ao_selecionar=self._selecionar_usuario)
        self._tab_usuarios.pack(fill="both", expand=True)
        self._detalhe_usuario = Cartao(aba, padx=16, pady=12)
        self._detalhe_usuario.grid(row=0, column=1, sticky="nsew")

    def _carregar_usuarios(self):
        usuarios = self.contas.usuarios()
        self._tab_usuarios.carregar([
            (u.nome, (u.nome, u.nome_completo or "-", u.email or "-", u.papel, len(u.autorizacoes_extras),
                      "Ativo" if u.ativo else "Desativado"))
            for u in usuarios])
        nomes = {u.nome for u in usuarios}
        self._selecionar_usuario(self._usuario_sel if self._usuario_sel in nomes else None)

    # Mostra funcoes e autorizacoes do usuario
    def _selecionar_usuario(self, nome):
        self._usuario_sel = nome
        painel = self._detalhe_usuario
        limpar(painel)
        if not nome:
            Rotulo(painel, "Selecione um usuário na tabela.", tema.F_NORMAL, tema.TEXTO_SUAVE).pack(anchor="w")
            return
        alvo = self.contas.usuario(nome)
        pode_editar = self._pode(Autorizacao.EDITAR_USUARIO)
        sou_admin = self.app.usuario.administrador
        Rotulo(painel, alvo.nome, (tema.FAMILIA, 14, "bold")).pack(anchor="w")
        Rotulo(painel, f"{alvo.nome_completo or '-'} · {alvo.email or '-'} · desde {alvo.criado_em}",
               tema.F_PEQUENA, tema.TEXTO_SUAVE, wraplength=360, justify="left").pack(anchor="w")

        Rotulo(painel, "Funções", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(anchor="w", pady=(12, 2))
        self._caixas_funcao = {}
        for funcao in Funcao:
            habilitada = pode_editar and (funcao is not Funcao.ADMINISTRADOR or sou_admin)
            caixa = CaixaSelecao(painel, funcao.rotulo, funcao.codigo in alvo.funcoes, habilitada,
                                 comando=self._redesenhar_extras)
            caixa.pack(anchor="w")
            self._caixas_funcao[funcao.codigo] = caixa

        Rotulo(painel, "Autorizações", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(anchor="w", pady=(12, 2))
        Rotulo(painel, "Cinza e marcada = já vem de uma função. Marque as demais para conceder individualmente.",
               tema.F_PEQUENA, tema.TEXTO_APAGADO, wraplength=360, justify="left").pack(anchor="w")
        self._quadro_extras = tk.Frame(painel, bg=tema.CARTAO)
        self._quadro_extras.pack(fill="x")
        self._extras_marcados = set(alvo.autorizacoes_extras)
        self._caixas_extras = {}
        self._redesenhar_extras()

        botoes = tk.Frame(painel, bg=tema.CARTAO)
        botoes.pack(fill="x", pady=(14, 0))
        if pode_editar:
            Botao(botoes, "Salvar acessos", lambda: self._salvar_acessos(alvo.nome)).pack(side="left")
            if alvo.nome.lower() != self._eu.lower():
                texto = "Desativar conta" if alvo.ativo else "Reativar conta"
                Botao(botoes, texto, lambda: self._alternar_ativo(alvo), "perigo" if alvo.ativo else "secundario"
                      ).pack(side="left", padx=8)
        else:
            self._bloqueado(botoes, Autorizacao.EDITAR_USUARIO)

    def _redesenhar_extras(self):
        for codigo, (caixa, da_funcao) in self._caixas_extras.items():
            if not da_funcao:
                (self._extras_marcados.add if caixa.marcada else self._extras_marcados.discard)(codigo)
        limpar(self._quadro_extras)
        funcoes = [c for c, cx in self._caixas_funcao.items() if cx.marcada]
        pelas_funcoes = autorizacoes_efetivas(funcoes)
        pode_editar = self._pode(Autorizacao.EDITAR_USUARIO)
        sou_admin = self.app.usuario.administrador
        self._caixas_extras = {}
        for grupo, autorizacoes in Autorizacao.grupos().items():
            Rotulo(self._quadro_extras, grupo, tema.F_PEQUENA, tema.TEXTO_SUAVE).pack(anchor="w", pady=(6, 0))
            for aut in autorizacoes:
                da_funcao = aut in pelas_funcoes
                habilitada = pode_editar and not da_funcao and (aut.solicitavel or sou_admin)
                caixa = CaixaSelecao(self._quadro_extras, aut.rotulo,
                                     da_funcao or aut.codigo in self._extras_marcados, habilitada)
                caixa.pack(anchor="w", padx=(12, 0))
                self._caixas_extras[aut.codigo] = (caixa, da_funcao)

    # Acao do Botao SALVAR ACESSOS
    def _salvar_acessos(self, nome):
        funcoes = [c for c, cx in self._caixas_funcao.items() if cx.marcada]
        pelas_funcoes = {a.codigo for a in autorizacoes_efetivas(funcoes)}
        extras = [c for c, (cx, _f) in self._caixas_extras.items() if cx.marcada and c not in pelas_funcoes]
        self._executar(lambda: self.contas.definir_acessos(self._eu, nome, funcoes, extras),
                       f"Acessos de {nome} atualizados.")

    # Acao do Botao DESATIVAR / REATIVAR
    def _alternar_ativo(self, alvo):
        acao = "desativar" if alvo.ativo else "reativar"
        if self.confirmar(f"Deseja {acao} a conta '{alvo.nome}'?"):
            self._executar(lambda: self.contas.definir_ativo(self._eu, alvo.nome, not alvo.ativo))

    def _montar_novo(self):
        self._form_novo = Cartao(self._aba_novo, padx=22, pady=12)
        self._form_novo.pack(fill="x")

    def _carregar_novo(self):
        cartao = self._form_novo
        limpar(cartao)
        if not self._pode(Autorizacao.CRIAR_USUARIO):
            self._bloqueado(cartao, Autorizacao.CRIAR_USUARIO)
            return
        cartao.columnconfigure(0, weight=1, uniform="n")
        cartao.columnconfigure(1, weight=1, uniform="n")
        esquerda = tk.Frame(cartao, bg=tema.CARTAO)
        esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        direita = tk.Frame(cartao, bg=tema.CARTAO)
        direita.grid(row=0, column=1, sticky="nsew")
        self._novo_usuario = Campo(esquerda, "Usuário", True, "carlos.dias")
        self._novo_usuario.pack(fill="x")
        self._novo_nome = Campo(esquerda, "Nome completo", True, "Carlos Dias")
        self._novo_nome.pack(fill="x")
        self._novo_email = Campo(esquerda, "E-mail", True, "carlos@empresa.com")
        self._novo_email.pack(fill="x")
        self._novo_senha = Campo(esquerda, "Senha inicial", True, senha=True,
                                 dica="(mín. 8; repasse por canal seguro)")
        self._novo_senha.pack(fill="x")
        Rotulo(direita, "Funções", tema.F_NEGRITO).pack(anchor="w", pady=(10, 4))
        sou_admin = self.app.usuario.administrador
        self._novo_funcoes = {f.codigo: CaixaSelecao(direita, f.rotulo, False,
                                                     f is not Funcao.ADMINISTRADOR or sou_admin)
                              for f in Funcao}
        for caixa in self._novo_funcoes.values():
            caixa.pack(anchor="w")
        Botao(direita, "Criar usuário", self._criar_usuario).pack(anchor="w", pady=(16, 0))

    # Acao do Botao CRIAR USUARIO
    def _criar_usuario(self):
        funcoes = [c for c, cx in self._novo_funcoes.items() if cx.marcada]
        novo = self._executar(lambda: self.contas.criar_usuario(
            self._eu, self._novo_usuario.valor, self._novo_senha.valor, self._novo_nome.valor,
            self._novo_email.valor, funcoes))
        if novo is not None:
            self.informar(f"Usuário '{novo.nome}' criado com a(s) função(ões): {novo.papel}.")

    def _montar_cadastros(self):
        aba = self._aba_cadastros
        aba.columnconfigure(0, weight=3)
        aba.columnconfigure(1, weight=2, minsize=360)
        aba.rowconfigure(0, weight=1)
        lista = Cartao(aba, padx=14, pady=12)
        lista.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        Rotulo(lista, "Pendentes", tema.F_NEGRITO).pack(anchor="w")
        self._tab_cadastros = Tabela(lista, [
            ("id", "Nº", 40, "center"), ("data", "Data", 120, "w"), ("usuario", "Usuário", 110, "w"),
            ("nome", "Nome", 150, "w"), ("email", "E-mail", 180, "w"), ("funcao", "Função", 110, "w"),
        ], altura=6, ao_selecionar=self._selecionar_cadastro)
        self._tab_cadastros.pack(fill="both", expand=True, pady=(4, 10))
        Rotulo(lista, "Histórico", tema.F_NEGRITO).pack(anchor="w")
        self._tab_cadastros_hist = Tabela(lista, COLUNAS_HISTORICO, altura=4)
        self._tab_cadastros_hist.pack(fill="both", expand=True, pady=(4, 0))
        self._ficha = Cartao(aba, padx=16, pady=12)
        self._ficha.grid(row=0, column=1, sticky="nsew")

    def _carregar_cadastros(self):
        pendentes = self.contas.cadastros_pendentes()
        self._abas.tab(self._aba_cadastros, text=f"  Cadastros ({len(pendentes)})  ")
        self._tab_cadastros.carregar([
            (p.id, (p.id, p.criada_em, p.usuario, p.nome_completo, p.email, Funcao.de_codigo(p.funcao).rotulo))
            for p in pendentes])
        self._tab_cadastros_hist.carregar(self._historico(
            [p for p in self.contas.cadastros() if p.status != PENDENTE]))
        ids = {str(p.id) for p in pendentes}
        self._selecionar_cadastro(self._cadastro_sel if self._cadastro_sel in ids else None)

    # Mostra a ficha do cadastro
    def _selecionar_cadastro(self, pedido_id):
        self._cadastro_sel = pedido_id
        ficha = self._ficha
        limpar(ficha)
        Rotulo(ficha, "Ficha do solicitante", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(anchor="w")
        if not pedido_id:
            Rotulo(ficha, "Selecione uma solicitação pendente.", tema.F_NORMAL, tema.TEXTO_SUAVE).pack(anchor="w")
            return
        p = self.contas.cadastro(pedido_id)
        for rotulo, valor in [("Nome", p.nome_completo), ("E-mail", p.email), ("Usuário", p.usuario),
                              ("Função desejada", Funcao.de_codigo(p.funcao).rotulo),
                              ("Justificativa", p.justificativa or "-"), ("Enviada em", p.criada_em)]:
            Rotulo(ficha, rotulo, tema.F_PEQUENA, tema.TEXTO_APAGADO).pack(anchor="w", pady=(6, 0))
            Rotulo(ficha, valor, tema.F_NORMAL, wraplength=320, justify="left").pack(anchor="w")
        if not self._pode(Autorizacao.APROVAR_CADASTRO):
            self._bloqueado(ficha, Autorizacao.APROVAR_CADASTRO)
            return
        opcoes = [f for f in Funcao if f is not Funcao.ADMINISTRADOR or self.app.usuario.administrador]
        self._funcao_aprovar = Combo(ficha, "Função a atribuir", [f.rotulo for f in opcoes])
        self._funcao_aprovar.valor = Funcao.de_codigo(p.funcao).rotulo
        self._funcao_aprovar.pack(fill="x")
        botoes = tk.Frame(ficha, bg=tema.CARTAO)
        botoes.pack(fill="x", pady=(14, 0))
        Botao(botoes, "Aprovar", lambda: self._aprovar_cadastro(p.id)).pack(side="left")
        Botao(botoes, "Recusar", lambda: self._recusar_cadastro(p.id), "perigo").pack(side="left", padx=8)

    # Acao do Botao APROVAR (cadastro)
    def _aprovar_cadastro(self, pedido_id):
        funcao = self._funcao_aprovar.valor
        usuario = self._executar(lambda: self.contas.aprovar_cadastro(self._eu, pedido_id, funcao))
        if usuario is not None:
            self.informar(f"Cadastro aprovado: '{usuario.nome}' já pode entrar ({usuario.papel}).")

    # Acao do Botao RECUSAR (cadastro)
    def _recusar_cadastro(self, pedido_id):
        motivo = pedir_texto(self, "Recusar cadastro", "Informe o motivo (fica registrado no histórico):")
        if motivo is not None:
            self._executar(lambda: self.contas.recusar_cadastro(self._eu, pedido_id, motivo), "Solicitação recusada.")

    def _montar_pedidos(self):
        aba = self._aba_pedidos
        aba.columnconfigure(0, weight=3)
        aba.columnconfigure(1, weight=2, minsize=360)
        aba.rowconfigure(0, weight=1)
        lista = Cartao(aba, padx=14, pady=12)
        lista.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        Rotulo(lista, "Pendentes", tema.F_NEGRITO).pack(anchor="w")
        self._tab_pedidos = Tabela(lista, [
            ("id", "Nº", 40, "center"), ("data", "Data", 120, "w"), ("usuario", "Usuário", 110, "w"),
            ("auts", "Autorizações pedidas", 300, "w"),
        ], altura=6, ao_selecionar=self._selecionar_pedido)
        self._tab_pedidos.pack(fill="both", expand=True, pady=(4, 10))
        Rotulo(lista, "Histórico", tema.F_NEGRITO).pack(anchor="w")
        self._tab_pedidos_hist = Tabela(lista, COLUNAS_HISTORICO, altura=4)
        self._tab_pedidos_hist.pack(fill="both", expand=True, pady=(4, 0))
        self._detalhe_pedido = Cartao(aba, padx=16, pady=12)
        self._detalhe_pedido.grid(row=0, column=1, sticky="nsew")

    @staticmethod
    def _rotulos(codigos):
        return ", ".join(Autorizacao.de_codigo(c).rotulo for c in codigos)

    def _carregar_pedidos(self):
        pendentes = self.contas.pedidos_pendentes()
        self._abas.tab(self._aba_pedidos, text=f"  Autorizações ({len(pendentes)})  ")
        self._tab_pedidos.carregar([(p.id, (p.id, p.criada_em, p.usuario, self._rotulos(p.autorizacoes)))
                                    for p in pendentes])
        self._tab_pedidos_hist.carregar(self._historico(
            [p for p in self.contas.pedidos() if p.status != PENDENTE]))
        ids = {str(p.id) for p in pendentes}
        self._selecionar_pedido(self._pedido_sel if self._pedido_sel in ids else None)

    # Mostra o pedido de autorizacao
    def _selecionar_pedido(self, pedido_id):
        self._pedido_sel = pedido_id
        painel = self._detalhe_pedido
        limpar(painel)
        Rotulo(painel, "Pedido de autorização", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(anchor="w")
        if not pedido_id:
            Rotulo(painel, "Selecione um pedido pendente.", tema.F_NORMAL, tema.TEXTO_SUAVE).pack(anchor="w")
            return
        p = self.contas.pedido(pedido_id)
        solicitante = self.contas.usuario(p.usuario)
        Rotulo(painel, f"{solicitante.nome} ({solicitante.nome_completo or '-'})", tema.F_NORMAL).pack(anchor="w")
        Rotulo(painel, f"Funções atuais: {solicitante.papel}", tema.F_PEQUENA, tema.TEXTO_SUAVE).pack(anchor="w")
        Rotulo(painel, "Pede:", tema.F_PEQUENA, tema.TEXTO_APAGADO).pack(anchor="w", pady=(8, 0))
        for codigo in p.autorizacoes:
            Rotulo(painel, f"• {Autorizacao.de_codigo(codigo).rotulo}", tema.F_NORMAL).pack(anchor="w")
        Rotulo(painel, "Justificativa:", tema.F_PEQUENA, tema.TEXTO_APAGADO).pack(anchor="w", pady=(8, 0))
        Rotulo(painel, p.justificativa or "-", tema.F_NORMAL, wraplength=320, justify="left").pack(anchor="w")
        if not self._pode(Autorizacao.APROVAR_AUTORIZACAO):
            self._bloqueado(painel, Autorizacao.APROVAR_AUTORIZACAO)
            return
        if p.usuario.lower() == self._eu.lower():
            Rotulo(painel, "Este pedido é seu: outro administrador precisa decidir.", tema.F_PEQUENA,
                   tema.CORES_SEVERIDADE["Média"]).pack(anchor="w", pady=(10, 0))
            return
        botoes = tk.Frame(painel, bg=tema.CARTAO)
        botoes.pack(fill="x", pady=(14, 0))
        Botao(botoes, "Aprovar", lambda: self._executar(
            lambda: self.contas.aprovar_autorizacao(self._eu, p.id), "Autorizações concedidas.")).pack(side="left")
        Botao(botoes, "Recusar", lambda: self._recusar_pedido(p.id), "perigo").pack(side="left", padx=8)

    # Acao do Botao RECUSAR (pedido)
    def _recusar_pedido(self, pedido_id):
        motivo = pedir_texto(self, "Recusar pedido", "Informe o motivo (o usuário verá na página Minha conta):")
        if motivo is not None:
            self._executar(lambda: self.contas.recusar_autorizacao(self._eu, pedido_id, motivo), "Pedido recusado.")

    # Tabela de funcoes x autorizacoes
    def _montar_funcoes(self):
        cartao = Cartao(self._aba_funcoes, padx=14, pady=12)
        cartao.pack(fill="both", expand=True)
        Rotulo(cartao, "Cada função é um conjunto de autorizações. Autorizações de Administração não podem ser "
                       "solicitadas: só um administrador as concede.", tema.F_PEQUENA, tema.TEXTO_SUAVE,
               wraplength=900, justify="left").pack(anchor="w")
        Rotulo(cartao, "Use a barra embaixo da tabela ou Shift + roda do mouse para ver todas as colunas.",
               tema.F_PEQUENA, tema.TEXTO_APAGADO).pack(anchor="w", pady=(0, 6))
        colunas = [("grupo", "Grupo", 130, "w"), ("aut", "Autorização", 380, "w"), ("codigo", "Código", 180, "w")]
        colunas += [(f.codigo, f.rotulo, 130, "center") for f in Funcao]
        colunas += [("sol", "Solicitável", 100, "center")]
        tabela = Tabela(cartao, colunas, altura=len(Autorizacao), rolagem_horizontal=True)
        tabela.pack(fill="both", expand=True)
        tabela.carregar([
            (a.codigo, (a.grupo, a.rotulo, a.codigo, *("✔" if a in f.autorizacoes else "" for f in Funcao),
                        "sim" if a.solicitavel else "não"))
            for a in Autorizacao])


    def carregar(self, **_):
        self._carregar_usuarios()
        self._carregar_novo()
        self._carregar_cadastros()
        self._carregar_pedidos()
