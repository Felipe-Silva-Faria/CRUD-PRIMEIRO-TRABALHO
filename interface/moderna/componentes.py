import tkinter as tk
from tkinter import ttk
from interface.moderna import tema


def limpar(widget):
    for filho in widget.winfo_children():
        filho.destroy()


_ESTILOS_BOTAO = {
    "primario": (tema.VIOLETA, tema.VIOLETA_HOVER, tema.TEXTO),
    "secundario": (tema.CARTAO_ALTO, tema.BORDA, tema.TEXTO),
    "perigo": (tema.misturar(tema.VERMELHO, tema.CARTAO, 0.35), tema.VERMELHO, tema.TEXTO),
}


class Botao(tk.Button):
    def __init__(self, mestre, texto, comando=None, tipo="primario", **kw):
        fundo, hover, frente = _ESTILOS_BOTAO[tipo]
        super().__init__(mestre, text=texto, command=comando, bg=fundo, fg=frente,
                         activebackground=hover, activeforeground=tema.TEXTO, relief="flat", bd=0,
                         cursor="hand2", font=kw.pop("font", tema.F_NEGRITO), padx=kw.pop("padx", 16),
                         pady=kw.pop("pady", 7), highlightthickness=0, **kw)
        self._fundo, self._hover = fundo, hover
        self.bind("<Enter>", lambda _e: self.configure(bg=self._hover))
        self.bind("<Leave>", lambda _e: self.configure(bg=self._fundo))


class Rotulo(tk.Label):
    def __init__(self, mestre, texto="", fonte=tema.F_NORMAL, cor=tema.TEXTO, fundo=None, **kw):
        super().__init__(mestre, text=texto, font=fonte, fg=cor, bg=fundo or mestre.cget("bg"), **kw)


class Cartao(tk.Frame):
    def __init__(self, mestre, **kw):
        super().__init__(mestre, bg=kw.pop("bg", tema.CARTAO), highlightthickness=1,
                         highlightbackground=tema.BORDA, **kw)


class Badge(tk.Label):
    def __init__(self, mestre, texto, cor, **kw):
        super().__init__(mestre, text=f" {texto} ", fg=cor, bg=tema.misturar(cor, mestre.cget("bg"), 0.22),
                         font=tema.F_NEGRITO, padx=6, pady=2, **kw)


class CartaoMetrica(Cartao):
    def __init__(self, mestre, titulo):
        super().__init__(mestre, padx=18, pady=14)
        Rotulo(self, titulo, tema.F_NORMAL, tema.TEXTO_SUAVE).pack(anchor="w")
        self._valor = Rotulo(self, "-", tema.F_METRICA)
        self._valor.pack(anchor="w", pady=(4, 0))
        self._detalhe = Rotulo(self, "", tema.F_PEQUENA, tema.TEXTO_SUAVE)
        self._detalhe.pack(anchor="w")

    def definir(self, valor, detalhe="", cor=tema.TEXTO_SUAVE):
        self._valor.configure(text=str(valor))
        self._detalhe.configure(text=detalhe, fg=cor)


def _rotulo_campo(mestre, rotulo, obrigatorio, dica=""):
    linha = tk.Frame(mestre, bg=mestre.cget("bg"))
    Rotulo(linha, rotulo, tema.F_NEGRITO).pack(side="left")
    if obrigatorio:
        Rotulo(linha, " *", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(side="left")
    if dica:
        Rotulo(linha, f" {dica}", tema.F_PEQUENA, tema.TEXTO_APAGADO).pack(side="left")
    linha.pack(anchor="w", pady=(10, 4))


class Campo(tk.Frame):
    def __init__(self, mestre, rotulo, obrigatorio=False, placeholder="", senha=False, dica=""):
        super().__init__(mestre, bg=mestre.cget("bg"))
        if rotulo:
            _rotulo_campo(self, rotulo, obrigatorio, dica)
        self._placeholder, self._senha = placeholder, senha
        self.entrada = tk.Entry(self, bg=tema.CARTAO_ALTO, fg=tema.TEXTO, insertbackground=tema.TEXTO,
                                relief="flat", font=tema.F_NORMAL, highlightthickness=1,
                                highlightbackground=tema.BORDA, highlightcolor=tema.VIOLETA)
        self.entrada.pack(fill="x", ipady=7)
        self._mostrando = False
        if senha:
            self.entrada.configure(show="•")
        self._colocar()
        self.entrada.bind("<FocusIn>", self._tirar)
        self.entrada.bind("<FocusOut>", lambda _e: self._colocar())

    def _colocar(self):
        if not self.entrada.get() and self._placeholder:
            self._mostrando = True
            self.entrada.configure(fg=tema.TEXTO_APAGADO, show="")
            self.entrada.insert(0, self._placeholder)

    def _tirar(self, _evento=None):
        if self._mostrando:
            self._mostrando = False
            self.entrada.delete(0, "end")
            self.entrada.configure(fg=tema.TEXTO, show="•" if self._senha else "")

    @property
    def valor(self):
        return "" if self._mostrando else self.entrada.get().strip()

    @valor.setter
    def valor(self, texto):
        self._tirar()
        self.entrada.delete(0, "end")
        self.entrada.insert(0, "" if texto is None else str(texto))
        self._colocar()

    def alternar_visibilidade(self):
        if not self._mostrando:
            self._senha = not self._senha
            self.entrada.configure(show="•" if self._senha else "")


class AreaTexto(tk.Frame):
    def __init__(self, mestre, rotulo, obrigatorio=False, altura=4):
        super().__init__(mestre, bg=mestre.cget("bg"))
        _rotulo_campo(self, rotulo, obrigatorio)
        self.texto = tk.Text(self, height=altura, bg=tema.CARTAO_ALTO, fg=tema.TEXTO,
                             insertbackground=tema.TEXTO, relief="flat", font=tema.F_NORMAL, wrap="word",
                             highlightthickness=1, highlightbackground=tema.BORDA,
                             highlightcolor=tema.VIOLETA, padx=8, pady=6)
        self.texto.pack(fill="both", expand=True)

    @property
    def valor(self):
        return self.texto.get("1.0", "end").strip()

    @valor.setter
    def valor(self, conteudo):
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", conteudo or "")


class Combo(tk.Frame):
    def __init__(self, mestre, rotulo, valores, obrigatorio=False, ao_mudar=None, largura=None,
                 editavel=False, dica=""):
        super().__init__(mestre, bg=mestre.cget("bg"))
        if rotulo:
            _rotulo_campo(self, rotulo, obrigatorio, dica)
        self.var = tk.StringVar()
        self.caixa = ttk.Combobox(self, textvariable=self.var, values=list(valores),
                                  state="normal" if editavel else "readonly", width=largura or 20)
        self.caixa.pack(fill="x")
        if ao_mudar:
            self.caixa.bind("<<ComboboxSelected>>", lambda _e: ao_mudar(self.var.get()))

    @property
    def valor(self):
        return self.var.get().strip()

    @valor.setter
    def valor(self, texto):
        self.var.set(texto)

    def definir_opcoes(self, valores):
        self.caixa.configure(values=list(valores))


class Tabela(tk.Frame):
    def __init__(self, mestre, colunas, ao_ordenar=None, ao_duplo_clique=None, altura=12):
        super().__init__(mestre, bg=tema.CARTAO)
        self._colunas, self._ao_ordenar = colunas, ao_ordenar
        self.coluna_ordenada, self.reverso = None, False
        self.arvore = ttk.Treeview(self, columns=[c[0] for c in colunas], show="headings",
                                   height=altura, selectmode="browse")
        for ident, titulo, largura, ancora in colunas:
            self.arvore.heading(ident, text=titulo, anchor=ancora,
                                command=lambda c=ident: self._clicou_cabecalho(c))
            self.arvore.column(ident, width=largura, anchor=ancora, stretch=True)
        self.arvore.tag_configure("impar", background=tema.misturar(tema.CARTAO_ALTO, tema.CARTAO, 0.5))
        barra = ttk.Scrollbar(self, orient="vertical", command=self.arvore.yview)
        self.arvore.configure(yscrollcommand=barra.set)
        self.arvore.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        if ao_duplo_clique:
            self.arvore.bind("<Double-1>", lambda _e: self._duplo(ao_duplo_clique))
            self.arvore.bind("<Return>", lambda _e: self._duplo(ao_duplo_clique))

    def _duplo(self, callback):
        if self.selecionado():
            callback(self.selecionado())

    def _clicou_cabecalho(self, coluna):
        if self._ao_ordenar is None:
            return
        self.reverso = not self.reverso if self.coluna_ordenada == coluna else False
        self.coluna_ordenada = coluna
        self.marcar_ordenacao(coluna, self.reverso)
        self._ao_ordenar(coluna, self.reverso)

    def marcar_ordenacao(self, coluna, reverso):
        self.coluna_ordenada, self.reverso = coluna, reverso
        for ident, titulo, _l, _a in self._colunas:
            seta = (" ▼" if reverso else " ▲") if ident == coluna else ""
            self.arvore.heading(ident, text=titulo + seta)

    def carregar(self, linhas):
        self.arvore.delete(*self.arvore.get_children())
        for i, (iid, valores) in enumerate(linhas):
            self.arvore.insert("", "end", iid=str(iid), values=valores, tags=("impar",) if i % 2 else ())

    def selecionado(self):
        selecao = self.arvore.selection()
        return selecao[0] if selecao else None


class _Grafico(tk.Canvas):
    def __init__(self, mestre, altura=220):
        super().__init__(mestre, height=altura, bg=mestre.cget("bg"), highlightthickness=0)
        self._dados = None
        self.bind("<Configure>", lambda _e: self._redesenhar())

    def _redesenhar(self):
        self.delete("all")
        if self._dados is not None:
            self._desenhar(*self._dados)

    def _desenhar(self, *dados):
        raise NotImplementedError


class GraficoBarras(_Grafico):
    def desenhar(self, rotulos, valores, cores=None):
        self._dados = (list(rotulos), list(valores), cores)
        self._redesenhar()

    def _desenhar(self, rotulos, valores, cores):
        largura, altura = self.winfo_width(), self.winfo_height()
        if largura < 50 or not valores:
            return
        esq, topo, base = 36, 18, 26
        util_l, util_a = largura - esq - 12, altura - topo - base
        maximo = max(1, max(valores))
        for i in range(5):
            y = topo + util_a - util_a * i / 4
            self.create_line(esq, y, esq + util_l, y, fill=tema.BORDA, dash=(2, 4))
            self.create_text(esq - 6, y, text=f"{maximo * i / 4:.0f}", fill=tema.TEXTO_APAGADO,
                             font=tema.F_PEQUENA, anchor="e")
        fatia = util_l / len(valores)
        barra = min(40, fatia * 0.6)
        for i, (rotulo, valor) in enumerate(zip(rotulos, valores)):
            centro = esq + fatia * (i + 0.5)
            y = topo + util_a - util_a * valor / maximo
            cor = cores[i] if cores else tema.VIOLETA
            self.create_rectangle(centro - barra / 2, y, centro + barra / 2, topo + util_a, fill=cor, outline="")
            if valor:
                self.create_text(centro, y - 8, text=str(valor), fill=tema.TEXTO, font=tema.F_PEQUENA)
            self.create_text(centro, altura - 10, text=rotulo, fill=tema.TEXTO_SUAVE, font=tema.F_PEQUENA)


class GraficoRosca(_Grafico):
    def desenhar(self, fatias, titulo_centro="Total"):
        self._dados = (list(fatias), titulo_centro)
        self._redesenhar()

    def _desenhar(self, fatias, titulo_centro):
        largura, altura = self.winfo_width(), self.winfo_height()
        if largura < 50:
            return
        total = sum(v for _, v, _ in fatias)
        raio = min(altura, largura * 0.45) / 2 - 14
        cx, cy = raio + 20, altura / 2
        espessura = max(12, raio * 0.28)
        caixa = (cx - raio, cy - raio, cx + raio, cy + raio)
        if total == 0:
            self.create_oval(*caixa, outline=tema.BORDA, width=espessura)
        inicio = 90.0
        for _r, valor, cor in fatias:
            if valor <= 0:
                continue
            extensao = -360.0 * valor / total
            if abs(extensao) >= 359.9:
                self.create_oval(*caixa, outline=cor, width=espessura)
            else:
                self.create_arc(*caixa, start=inicio, extent=extensao, style="arc", outline=cor, width=espessura)
            inicio += extensao
        self.create_text(cx, cy - 8, text=str(total), fill=tema.TEXTO, font=tema.F_METRICA)
        self.create_text(cx, cy + 20, text=titulo_centro, fill=tema.TEXTO_SUAVE, font=tema.F_PEQUENA)
        x_leg = cx + raio + 30
        y = cy - (len(fatias) - 1) * 13
        for rotulo, valor, cor in fatias:
            pct = f"{100 * valor / total:.0f}%" if total else "0%"
            self.create_oval(x_leg, y - 5, x_leg + 10, y + 5, fill=cor, outline="")
            self.create_text(x_leg + 18, y, text=rotulo, fill=tema.TEXTO, font=tema.F_NORMAL, anchor="w")
            self.create_text(largura - 8, y, text=f"{valor} ({pct})", fill=tema.TEXTO_SUAVE,
                             font=tema.F_PEQUENA, anchor="e")
            y += 26


class BarraLateral(tk.Frame):
    def __init__(self, mestre, itens, ao_selecionar, titulo=""):
        super().__init__(mestre, bg=tema.PAINEL, width=220)
        self.pack_propagate(False)
        self._botoes, self._ativo = {}, None
        if titulo:
            Rotulo(self, titulo, tema.F_NEGRITO, tema.TEXTO_SUAVE, wraplength=180,
                   justify="left").pack(anchor="w", padx=22, pady=(22, 18))
        for chave, icone, texto in itens:
            botao = tk.Label(self, text=f"  {icone}   {texto}", anchor="w", font=tema.F_NORMAL,
                             bg=tema.PAINEL, fg=tema.TEXTO_SUAVE, padx=12, pady=10, cursor="hand2")
            botao.pack(fill="x", padx=10, pady=2)
            botao.bind("<Button-1>", lambda _e, c=chave: ao_selecionar(c))
            botao.bind("<Enter>", lambda _e, b=botao: self._hover(b, True))
            botao.bind("<Leave>", lambda _e, b=botao: self._hover(b, False))
            self._botoes[chave] = botao

    def _hover(self, botao, entrando):
        if botao is not self._botoes.get(self._ativo):
            botao.configure(bg=tema.CARTAO_ALTO if entrando else tema.PAINEL)

    def marcar(self, chave):
        self._ativo = chave
        for c, botao in self._botoes.items():
            sel = c == chave
            botao.configure(bg=tema.VIOLETA_ESCURO if sel else tema.PAINEL,
                            fg=tema.TEXTO if sel else tema.TEXTO_SUAVE)

class AreaRolavel(tk.Frame):

    def __init__(self, mestre, bg=tema.PAINEL):
        super().__init__(mestre, bg=bg)
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self._barra = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._barra.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        self.interior = tk.Frame(self._canvas, bg=bg)
        self._janela = self._canvas.create_window(0, 0, window=self.interior, anchor="nw")
        self._canvas.bind("<Configure>", lambda _e: self._ajustar())
        self.interior.bind("<Configure>", lambda _e: self._ajustar())

    def _ajustar(self):
        largura = self._canvas.winfo_width()
        visivel = self._canvas.winfo_height()
        necessario = self.interior.winfo_reqheight()
        altura = max(visivel, necessario)
        self._canvas.itemconfigure(self._janela, width=largura, height=altura)
        self._canvas.configure(scrollregion=(0, 0, largura, altura))
        if necessario > visivel:
            if not self._barra.winfo_ismapped():
                self._barra.pack(side="right", fill="y", before=self._canvas)
        elif self._barra.winfo_ismapped():
            self._barra.pack_forget()
            self._canvas.yview_moveto(0)

    def rolar(self, evento):

        classe = getattr(evento.widget, "winfo_class", lambda: "")()
        if classe in ("Treeview", "Text", "Listbox"):
            return
        if self._canvas.yview() != (0.0, 1.0):
            self._canvas.yview_scroll(int(-evento.delta / 120), "units")