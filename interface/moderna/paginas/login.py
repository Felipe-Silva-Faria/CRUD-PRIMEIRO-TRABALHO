import math
import tkinter as tk
from tkinter import ttk

from dominio.excecoes import ErroCRUD, ErroValidacao
from dominio.permissoes import Funcao
from interface.moderna import NOME_EXIBICAO, VERSAO, preferencias, tema
from interface.moderna.componentes import AreaRolavel, AreaTexto, Botao, Campo, Cartao, Combo, Rotulo, limpar
from interface.moderna.paginas.base import mensagem_de
from servicos.autenticacao import ContaBloqueada, ErroAutenticacao


class PaginaLogin(tk.Frame):
    def __init__(self, mestre, app):
        super().__init__(mestre, bg=tema.FUNDO)
        self.app = app
        self.auth = app.autenticacao
        self.contas = app.contas
        self.criando_admin = self.auth.primeiro_acesso()
        self.canvas = tk.Canvas(self, bg=tema.FUNDO, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._desenhar_painel())
        lado = tk.Frame(self, bg=tema.FUNDO, width=520)
        lado.pack(side="right", fill="y")
        lado.pack_propagate(False)
        area = AreaRolavel(lado, bg=tema.FUNDO)
        area.pack(fill="both", expand=True)
        self.cartao = Cartao(area.interior, padx=40, pady=30)
        self.cartao.pack(padx=40, pady=40, fill="x")
        self.mostrar_login()

    def _desenhar_painel(self):
        c = self.canvas
        c.delete("all")
        largura, altura = c.winfo_width(), c.winfo_height()
        cx = largura / 2
        c.create_text(cx, altura * 0.24, text=NOME_EXIBICAO, fill=tema.TEXTO, font=tema.F_DESTAQUE,
                      width=largura * 0.8, justify="center")
        c.create_text(cx, altura * 0.33, text="Projeto Acadêmico · Cibersegurança UFU",
                      fill=tema.TEXTO_SUAVE, font=(tema.FAMILIA, 12))
        raio, cy = min(largura, altura) * 0.22, altura * 0.65
        for lat in range(-75, 90, 15):
            for lon in range(0, 360, 12):
                phi, theta = math.radians(lat), math.radians(lon + 20)
                z = math.cos(phi) * math.cos(theta)
                if z < 0:
                    continue
                x = cx + raio * math.cos(phi) * math.sin(theta)
                y = cy - raio * math.sin(phi)
                r = 1 + 1.6 * z
                c.create_oval(x - r, y - r, x + r, y + r, outline="",
                              fill=tema.misturar(tema.VIOLETA_CLARO, tema.FUNDO, 0.25 + 0.6 * z))

    @staticmethod
    def _link(mestre, texto, comando):
        link = Rotulo(mestre, texto, tema.F_PEQUENA, tema.VIOLETA_CLARO, cursor="hand2")
        link.bind("<Button-1>", lambda _e: comando())
        return link

    # Tela de login
    def mostrar_login(self, aviso=""):
        self.modo = "login"
        cartao = self.cartao
        limpar(cartao)
        Rotulo(cartao, "Primeiro acesso" if self.criando_admin else "Acesso ao Sistema",
               tema.F_TITULO).pack(anchor="w")
        Rotulo(cartao, "Crie a conta de administrador." if self.criando_admin
               else "Entre para continuar no ambiente seguro.", tema.F_SUBTITULO,
               tema.TEXTO_SUAVE).pack(anchor="w", pady=(2, 8))
        lembrado = self.app.preferencias.get("lembrar_usuario", "")
        self.campo_usuario = Campo(cartao, "Usuário", placeholder="seu.usuario")
        self.campo_usuario.pack(fill="x")
        if lembrado and not self.criando_admin:
            self.campo_usuario.valor = lembrado
        self.campo_senha = Campo(cartao, "Senha", senha=True)
        self.campo_senha.pack(fill="x")
        olho = tk.Label(self.campo_senha, text="◉", bg=tema.CARTAO_ALTO, fg=tema.TEXTO_SUAVE, cursor="hand2")
        olho.place(relx=1.0, rely=1.0, x=-8, y=-6, anchor="se")
        olho.bind("<Button-1>", lambda _e: self.campo_senha.alternar_visibilidade())
        self.campo_confirmar = None
        if self.criando_admin:
            self.campo_confirmar = Campo(cartao, "Confirmar senha", senha=True)
            self.campo_confirmar.pack(fill="x")
            Rotulo(cartao, "Mínimo de 8 caracteres. Prefira uma frase longa.", tema.F_PEQUENA,
                   tema.TEXTO_APAGADO).pack(anchor="w", pady=(4, 0))
        opcoes = tk.Frame(cartao, bg=tema.CARTAO)
        opcoes.pack(fill="x", pady=(12, 0))
        self.lembrar = tk.BooleanVar(value=bool(lembrado))
        ttk.Checkbutton(opcoes, text="Lembrar de mim", variable=self.lembrar).pack(side="left")
        Botao(cartao, "Criar administrador  →" if self.criando_admin else "Entrar  →",
              self._entrar).pack(fill="x", pady=(18, 6), ipady=3)
        self.mensagem = Rotulo(cartao, aviso, tema.F_PEQUENA, tema.VERDE if aviso else tema.VERMELHO,
                               wraplength=340, justify="left")
        self.mensagem.pack(anchor="w")
        if not self.criando_admin and self.contas is not None:
            rodape = tk.Frame(cartao, bg=tema.CARTAO)
            rodape.pack(fill="x", pady=(10, 0))
            Rotulo(rodape, "Não tem conta?", tema.F_PEQUENA, tema.TEXTO_SUAVE).pack(side="left")
            self._link(rodape, " Solicitar acesso", self.mostrar_solicitacao).pack(side="left")
        Rotulo(cartao, f"v{VERSAO} | Projeto Acadêmico", tema.F_PEQUENA, tema.TEXTO_APAGADO).pack(pady=(14, 0))
        self.app.bind("<Return>", lambda _e: self._enter())

    def _enter(self):
        if self.modo == "login":
            self._entrar()

    # Acao do Botao ENTRAR
    def _entrar(self):
        if not self.winfo_exists():
            return
        nome, senha = self.campo_usuario.valor, self.campo_senha.valor
        try:
            if self.criando_admin:
                if senha != self.campo_confirmar.valor:
                    raise ErroValidacao("senha", "as senhas não conferem")
                self.auth.criar_usuario(nome, senha)
            usuario = self.auth.autenticar(nome, senha)
        except ContaBloqueada as erro:
            self.mensagem.configure(text=str(erro), fg=tema.VERMELHO)
            return
        except (ErroAutenticacao, ErroValidacao) as erro:
            self.mensagem.configure(text=mensagem_de(erro), fg=tema.VERMELHO)
            self.campo_senha.valor = ""
            return
        preferencias.gravar(lembrar_usuario=usuario.nome if self.lembrar.get() else "")
        self.app.unbind("<Return>")
        self.app.iniciar_sessao(usuario)

    # Tela de solicitar acesso
    def mostrar_solicitacao(self):
        self.modo = "solicitacao"
        cartao = self.cartao
        limpar(cartao)
        Rotulo(cartao, "Solicitar acesso", tema.F_TITULO).pack(anchor="w")
        Rotulo(cartao, "Sua ficha será analisada por um administrador.", tema.F_SUBTITULO,
               tema.TEXTO_SUAVE).pack(anchor="w", pady=(2, 4))
        self.sol_usuario = Campo(cartao, "Usuário", True, "ana.souza", dica="(para entrar no sistema)")
        self.sol_usuario.pack(fill="x")
        self.sol_nome = Campo(cartao, "Nome completo", True, "Ana Souza")
        self.sol_nome.pack(fill="x")
        self.sol_email = Campo(cartao, "E-mail", True, "ana.souza@empresa.com")
        self.sol_email.pack(fill="x")
        self._funcoes = {f.rotulo: f.codigo for f in Funcao.solicitaveis()}
        self.sol_funcao = Combo(cartao, "Função desejada", list(self._funcoes), True)
        self.sol_funcao.pack(fill="x")
        self.sol_justificativa = AreaTexto(cartao, "Justificativa", altura=2)
        self.sol_justificativa.pack(fill="x")
        self.sol_senha = Campo(cartao, "Senha", True, senha=True, dica="(mín. 8 caracteres)")
        self.sol_senha.pack(fill="x")
        self.sol_confirmar = Campo(cartao, "Confirmar senha", True, senha=True)
        self.sol_confirmar.pack(fill="x")
        Rotulo(cartao, "A função Administrador só pode ser atribuída por outro administrador.",
               tema.F_PEQUENA, tema.TEXTO_APAGADO, wraplength=340, justify="left").pack(anchor="w", pady=(8, 0))
        Botao(cartao, "Enviar solicitação", self._enviar_solicitacao).pack(fill="x", pady=(14, 6), ipady=3)
        self.mensagem = Rotulo(cartao, "", tema.F_PEQUENA, tema.VERMELHO, wraplength=340, justify="left")
        self.mensagem.pack(anchor="w")
        self._link(cartao, "← Voltar para o login", self.mostrar_login).pack(anchor="w", pady=(8, 0))

    # Acao do Botao ENVIAR SOLICITACAO
    def _enviar_solicitacao(self):
        try:
            if self.sol_senha.valor != self.sol_confirmar.valor:
                raise ErroValidacao("senha", "as senhas não conferem")
            if self.sol_funcao.valor not in self._funcoes:
                raise ErroValidacao("funcao", "escolha a função desejada")
            self.contas.solicitar_cadastro(
                self.sol_usuario.valor, self.sol_senha.valor, self.sol_nome.valor, self.sol_email.valor,
                self._funcoes[self.sol_funcao.valor], self.sol_justificativa.valor)
        except ErroCRUD as erro:
            self.mensagem.configure(text=mensagem_de(erro), fg=tema.VERMELHO)
            self.sol_senha.valor = self.sol_confirmar.valor = ""
            return
        self.mostrar_login(aviso="Solicitação enviada. Você poderá entrar assim que um administrador aprovar.")
