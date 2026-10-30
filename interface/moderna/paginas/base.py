import logging
import tkinter as tk
from tkinter import messagebox
from dominio.excecoes import ErroCRUD
from interface.moderna import NOME_EXIBICAO, tema
from interface.moderna.componentes import Rotulo

logger = logging.getLogger(__name__)


def mensagem_de(erro):
    campo = getattr(erro, "campo", "")
    texto = getattr(erro, "mensagem", "") or str(erro)
    return f"{campo}: {texto}" if campo and campo not in texto else texto


class Pagina(tk.Frame):
    def __init__(self, mestre, app):
        super().__init__(mestre, bg=tema.PAINEL)
        self.app = app
        self.painel = app.painel
        self._parametros = {}
        self.construir()

    def construir(self):
        ...

    def carregar(self, **parametros):
        ...

    def atualizar(self, **parametros):
        self._parametros = parametros
        try:
            self.carregar(**parametros)
        except ErroCRUD as erro:
            self.erro(erro)

    def recarregar(self):
        self.atualizar(**self._parametros)

    def cabecalho(self, titulo, subtitulo=""):
        barra = tk.Frame(self, bg=tema.PAINEL)
        barra.pack(fill="x", padx=28, pady=(22, 12))
        textos = tk.Frame(barra, bg=tema.PAINEL)
        textos.pack(side="left")
        self._titulo = Rotulo(textos, titulo, tema.F_TITULO)
        self._titulo.pack(anchor="w")
        if subtitulo:
            Rotulo(textos, subtitulo, tema.F_SUBTITULO, tema.TEXTO_SUAVE).pack(anchor="w")
        direita = tk.Frame(barra, bg=tema.PAINEL)
        direita.pack(side="right")
        return direita

    def erro(self, excecao):
        logger.warning("erro exibido ao usuario: %s", excecao)
        messagebox.showerror(NOME_EXIBICAO, mensagem_de(excecao), parent=self)

    def confirmar(self, pergunta):
        return messagebox.askyesno("Confirmar", pergunta, parent=self)

    def informar(self, texto):
        messagebox.showinfo(NOME_EXIBICAO, texto, parent=self)
