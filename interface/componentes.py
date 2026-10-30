import tkinter as tk
from dominio.excecoes import ErroValidacao
from interface.tema import TEMA_PADRAO


class Tooltip:
    ATRASO_MS = 500

    def __init__(self, widget, texto):
        self.widget = widget
        self.texto = texto
        self._janela = None
        self._agendado = None
        for evento in ("<Enter>", "<FocusIn>"):
            widget.bind(evento, self._agendar, add="+")
        for evento in ("<Leave>", "<FocusOut>", "<ButtonPress>"):
            widget.bind(evento, self._esconder, add="+")

    def _agendar(self, _evento=None):
        self._cancelar()
        self._agendado = self.widget.after(self.ATRASO_MS, self._mostrar)

    def _cancelar(self):
        if self._agendado:
            self.widget.after_cancel(self._agendado)
            self._agendado = None

    def _mostrar(self):
        if self._janela or not self.texto:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._janela = tk.Toplevel(self.widget)
        self._janela.wm_overrideredirect(True)
        self._janela.wm_geometry(f"+{x}+{y}")
        tk.Label(self._janela, text=self.texto, bg="#ffffe0", fg="#000000",
                 relief="solid", borderwidth=1, padx=6, pady=3,
                 font=TEMA_PADRAO.fonte(-1)).pack()

    def _esconder(self, _evento=None):
        self._cancelar()
        if self._janela:
            self._janela.destroy()
            self._janela = None


class BotaoAcessivel(tk.Button):
    def __init__(self, master, texto, comando, dica="", tema=TEMA_PADRAO, atalho="", **kwargs):
        rotulo = f"{texto} ({atalho})" if atalho else texto
        super().__init__(
            master, text=rotulo, command=comando,
            bg=tema.destaque, fg=tema.texto,
            activebackground=tema.destaque_claro, activeforeground=tema.texto,
            font=tema.fonte(0, "bold"), relief="flat", cursor="hand2",
            padx=12, pady=6, takefocus=True,
            highlightthickness=3, highlightcolor=tema.foco, highlightbackground=tema.painel,
            **kwargs,
        )
        self.bind("<Return>", lambda _e: self.invoke())
        self.bind("<space>", lambda _e: self.invoke())
        if dica:
            Tooltip(self, dica)


class CampoRotulado(tk.Frame):
    def __init__(self, master, rotulo, validador=None, dica="", tema=TEMA_PADRAO, **kwargs):
        super().__init__(master, bg=tema.painel, **kwargs)
        self.tema = tema
        self.validador = validador
        self.variavel = tk.StringVar()
        self.rotulo = tk.Label(self, text=rotulo, bg=tema.painel, fg=tema.texto,
                               font=tema.fonte(0, "bold"), anchor="w")
        self.rotulo.pack(fill="x")
        self.entrada = tk.Entry(self, textvariable=self.variavel, font=tema.fonte(),
                                insertbackground=tema.texto, bg=tema.fundo, fg=tema.texto,
                                highlightthickness=2, highlightcolor=tema.foco,
                                highlightbackground=tema.destaque)
        self.entrada.pack(fill="x", pady=(2, 0))
        self.erro = tk.Label(self, text="", bg=tema.painel, fg=tema.erro,
                             font=tema.fonte(-1), anchor="w")
        self.erro.pack(fill="x")
        self.entrada.bind("<FocusOut>", lambda _e: self.validar())
        if dica:
            Tooltip(self.entrada, dica)

    def obter(self):
        return self.variavel.get()

    def definir(self, valor):
        self.variavel.set(valor)

    def validar(self):
        try:
            valor = self.validador(self.obter()) if self.validador else self.obter()
        except ErroValidacao as erro:
            self.erro.config(text="\u26a0 " + erro.mensagem)
            self.entrada.config(highlightbackground=self.tema.erro)
            return None
        self.erro.config(text="")
        self.entrada.config(highlightbackground=self.tema.destaque)
        return valor

    def focar(self):
        self.entrada.focus_set()


class BarraStatus(tk.Label):
    def __init__(self, master, tema=TEMA_PADRAO):
        super().__init__(master, text="Pronto", anchor="w", padx=8,
                         bg=tema.fundo, fg=tema.texto, font=tema.fonte(-1))
        self._tema = tema

    def informar(self, mensagem, erro=False, duracao_ms=5000):
        self.config(text=mensagem, fg=self._tema.erro if erro else self._tema.texto)
        if duracao_ms:
            self.after(duracao_ms, lambda: self.config(text="Pronto", fg=self._tema.texto))
