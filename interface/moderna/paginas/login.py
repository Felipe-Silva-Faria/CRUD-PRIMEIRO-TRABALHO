import math
import tkinter as tk
from tkinter import ttk

from dominio.excecoes import ErroValidacao
from interface.moderna import NOME_EXIBICAO, VERSAO, preferencias, tema
from interface.moderna.componentes import Botao, Campo, Cartao, Rotulo
from interface.moderna.paginas.base import mensagem_de
from servicos.autenticacao import ContaBloqueada, ErroAutenticacao


class PaginaLogin(tk.Frame):
    def __init__(self, mestre, app):
        super().__init__(mestre, bg=tema.FUNDO)
        self.app = app
        self.auth = app.autenticacao
        self.criando_admin = self.auth.primeiro_acesso()
        self.canvas = tk.Canvas(self, bg=tema.FUNDO, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._desenhar_painel())
        self._montar_formulario()

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

    def _montar_formulario(self):
        lado = tk.Frame(self, bg=tema.FUNDO, width=520)
        lado.pack(side="right", fill="y")
        lado.pack_propagate(False)
        cartao = Cartao(lado, padx=40, pady=36)
        cartao.place(relx=0.5, rely=0.5, anchor="center", width=430)
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
              self._enviar).pack(fill="x", pady=(18, 6), ipady=3)
        self.mensagem = Rotulo(cartao, "", tema.F_PEQUENA, tema.VERMELHO, wraplength=340, justify="left")
        self.mensagem.pack(anchor="w")
        Rotulo(cartao, f"v{VERSAO} | Projeto Acadêmico", tema.F_PEQUENA, tema.TEXTO_APAGADO).pack(pady=(14, 0))
        self.app.bind("<Return>", lambda _e: self._enviar())

    def _enviar(self):
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
            self.mensagem.configure(text=str(erro))
            return
        except (ErroAutenticacao, ErroValidacao) as erro:
            self.mensagem.configure(text=mensagem_de(erro))
            self.campo_senha.valor = ""
            return
        preferencias.gravar(lembrar_usuario=usuario.nome if self.lembrar.get() else "")
        self.app.unbind("<Return>")
        self.app.iniciar_sessao(usuario)
