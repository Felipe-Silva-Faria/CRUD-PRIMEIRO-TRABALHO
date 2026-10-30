import tkinter as tk
from tkinter import messagebox, ttk
from interface.tema import TEMAS


class GerenciadorAcessibilidade:
    def __init__(self, root, ao_trocar_tema=None):
        self.root = root
        self._indice_tema = 0
        self._escala = 0
        self._atalhos = {}
        self._ao_trocar_tema = ao_trocar_tema or (lambda tema: None)
        self.registrar("<F1>", "Mostrar atalhos", self.mostrar_ajuda)
        self.registrar("<Control-equal>", "Aumentar fonte", lambda: self.escalar(+1))
        self.registrar("<Control-minus>", "Diminuir fonte", lambda: self.escalar(-1))
        self.registrar("<F6>", "Alternar alto contraste", self.alternar_tema)

    @property
    def tema(self):
        return TEMAS[self._indice_tema].com_escala(self._escala)

    def registrar(self, sequencia, descricao, funcao):
        self._atalhos[sequencia] = (descricao, funcao)
        self.root.bind_all(sequencia, lambda _evento: (funcao(), "break")[1])

    def escalar(self, passos):
        self._escala = max(-3, min(10, self._escala + passos))
        self.aplicar()

    def alternar_tema(self):
        self._indice_tema = (self._indice_tema + 1) % len(TEMAS)
        self.aplicar()

    def aplicar(self):
        tema = self.tema
        estilo = ttk.Style(self.root)
        estilo.configure("Treeview", font=tema.fonte(), rowheight=tema.fonte_tamanho * 2 + 6,
                         background=tema.painel, fieldbackground=tema.painel, foreground=tema.texto)
        estilo.configure("Treeview.Heading", font=tema.fonte(0, "bold"))
        estilo.map("Treeview", background=[("selected", tema.destaque_claro)])
        aplicar_tema_recursivo(self.root, tema)
        self._ao_trocar_tema(tema)

    def mostrar_ajuda(self):
        linhas = [f"{_legivel(seq):<14} {desc}" for seq, (desc, _f) in self._atalhos.items()]
        messagebox.showinfo("Atalhos de teclado", "\n".join(linhas))


def _legivel(sequencia):
    return (sequencia.strip("<>").replace("Control-", "Ctrl+")
            .replace("equal", "=").replace("minus", "-"))


def aplicar_tema_recursivo(widget, tema):
    cores = {
        tk.Frame: {"bg": tema.painel},
        tk.Label: {"bg": tema.painel, "fg": tema.texto, "font": tema.fonte()},
        tk.Button: {"bg": tema.destaque, "fg": tema.texto, "font": tema.fonte(0, "bold"),
                    "highlightcolor": tema.foco},
        tk.Entry: {"bg": tema.fundo, "fg": tema.texto, "insertbackground": tema.texto,
                   "font": tema.fonte(), "highlightcolor": tema.foco},
        tk.Text: {"bg": tema.fundo, "fg": tema.texto, "insertbackground": tema.texto, "font": tema.fonte()},
        tk.Tk: {"bg": tema.fundo},
        tk.Toplevel: {"bg": tema.painel},
    }
    for classe, opcoes in cores.items():
        if isinstance(widget, classe):
            try:
                widget.configure(**opcoes)
            except tk.TclError:
                pass
            break
    for filho in widget.winfo_children():
        aplicar_tema_recursivo(filho, tema)
