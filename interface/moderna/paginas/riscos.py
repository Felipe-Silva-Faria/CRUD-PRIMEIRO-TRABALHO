import math
import tkinter as tk
from dominio.excecoes import ErroCRUD
from interface.moderna import tema
from interface.moderna.componentes import Botao, Cartao, Combo, Rotulo, Tabela, limpar
from interface.moderna.paginas.base import Pagina


class PaginaRiscos(Pagina):
    def construir(self):
        self.cabecalho("Riscos", "Propagação de risco pelas dependências entre ativos.")
        self._alcancados, self._caminho = {}, []
        corpo = tk.Frame(self, bg=tema.PAINEL)
        corpo.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        corpo.columnconfigure(0, weight=3)
        corpo.columnconfigure(1, weight=2, minsize=380)
        corpo.rowconfigure(0, weight=1)

        esquerda = tk.Frame(corpo, bg=tema.PAINEL)
        esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        mapa = Cartao(esquerda, padx=10, pady=10)
        mapa.pack(fill="both", expand=True)
        Rotulo(mapa, "Mapa de dependências (A → B: o risco de A chega em B)", tema.F_NEGRITO).pack(anchor="w")
        self._canvas = tk.Canvas(mapa, bg=tema.CARTAO, highlightthickness=0, height=300)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", lambda _e: self._desenhar())
        ranking = Cartao(esquerda, padx=10, pady=10)
        ranking.pack(fill="x", pady=(12, 0))
        Rotulo(ranking, "Ranking pela álgebra da S3: b = Mv (próprio) e (I − A)x = b (propagado)",
               tema.F_NEGRITO).pack(anchor="w")
        self._ranking = Tabela(ranking, [("ativo", "Ativo", 200, "w"), ("b", "Risco próprio b", 110, "center"),
                                         ("x", "Risco propagado x", 120, "center")], altura=5)
        self._ranking.pack(fill="x", pady=(6, 0))
        self._diagnostico = Rotulo(ranking, "", tema.F_PEQUENA, tema.TEXTO_SUAVE)
        self._diagnostico.pack(anchor="w", pady=(6, 0))

        painel = Cartao(corpo, padx=16, pady=10)
        painel.grid(row=0, column=1, sticky="nsew")
        Rotulo(painel, "Dependências", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(anchor="w")
        linha = tk.Frame(painel, bg=tema.CARTAO)
        linha.pack(fill="x")
        self._dep_origem = Combo(linha, "Origem", [], largura=14)
        self._dep_origem.pack(side="left", fill="x", expand=True)
        self._dep_destino = Combo(linha, "Destino", [], largura=14)
        self._dep_destino.pack(side="left", fill="x", expand=True, padx=6)
        self._dep_peso = Combo(linha, "Peso", ["0.2", "0.4", "0.5", "0.6", "0.8"], editavel=True, largura=5)
        self._dep_peso.pack(side="left")
        self._dep_peso.valor = "0.5"
        botoes = tk.Frame(painel, bg=tema.CARTAO)
        botoes.pack(fill="x", pady=(8, 0))
        Botao(botoes, "Adicionar", self._adicionar_dep).pack(side="left")
        Botao(botoes, "Remover selecionada", self._remover_dep, "secundario").pack(side="left", padx=8)
        self._tab_deps = Tabela(painel, [("o", "Origem", 130, "w"), ("d", "Destino", 130, "w"),
                                         ("p", "Peso", 50, "center")], altura=4)
        self._tab_deps.pack(fill="x", pady=(8, 0))

        Rotulo(painel, "Simular comprometimento (BFS)", tema.F_NEGRITO, tema.VIOLETA_CLARO).pack(
            anchor="w", pady=(14, 0))
        self._origem = Combo(painel, "", [], ao_mudar=lambda _v: self._calcular())
        self._origem.pack(fill="x", pady=(4, 0))
        self._destino = Combo(painel, "Até o ativo", [], ao_mudar=lambda _v: self._calcular())
        self._destino.pack(fill="x")
        self._resultado = tk.Frame(painel, bg=tema.CARTAO)
        self._resultado.pack(fill="x", pady=(8, 0))

    def carregar(self, **_):
        self._ativos = {a.id: a for a in self.painel.ativos()}
        opcoes = [f"{a.id} - {a.nome}" for a in self._ativos.values()]
        for combo in (self._dep_origem, self._dep_destino, self._origem, self._destino):
            combo.definir_opcoes(opcoes)
        if opcoes and not self._origem.valor:
            self._origem.valor = opcoes[0]
        self._grafo = self.painel.grafo()
        deps = self.painel.dependencias()
        self._tab_deps.carregar([(f"{d['origem']}>{d['destino']}", (self._nome(d["origem"]),
                                  self._nome(d["destino"]), d["peso"])) for d in deps])
        try:
            analise = self.painel.analise_risco()
        except ErroCRUD as erro:
            self._ranking.carregar([])
            self._diagnostico.configure(text=f"✖ {erro}", fg=tema.VERMELHO)
        else:
            self._x = dict(zip(analise.ids, (float(v) for v in analise.x)))
            self._ranking.carregar([(i, (nome, f"{b:.2f}", f"{x:.2f}")) for i, nome, b, x in analise.ranking()])
            self._diagnostico.configure(
                fg=tema.TEXTO_SUAVE,
                text=f"det(I − A) = {analise.determinante:.3f} · condição κ = {analise.condicao:.2f} · "
                     f"raio espectral ρ(A) = {analise.raio_espectral:.2f} · resíduo = {analise.residuo:.1e}")
        self._calcular()

    def _nome(self, aid):
        return self._ativos[aid].nome if aid in self._ativos else str(aid)

    @staticmethod
    def _id(texto):
        return int(texto.split(" - ", 1)[0]) if texto else None

    def _adicionar_dep(self):
        try:
            self.painel.adicionar_dependencia(self._id(self._dep_origem.valor), self._id(self._dep_destino.valor),
                                              self._dep_peso.valor)
        except (ErroCRUD, TypeError) as erro:
            self.erro(erro)

    def _remover_dep(self):
        selecao = self._tab_deps.selecionado()
        if selecao:
            origem, destino = selecao.split(">")
            self.painel.remover_dependencia(origem, destino)

    def _calcular(self):
        limpar(self._resultado)
        origem = self._id(self._origem.valor)
        if origem is None:
            return
        self._alcancados = self._grafo.bfs(origem)
        for aid, saltos in list(self._alcancados.items())[1:]:
            Rotulo(self._resultado, f"{'→ ' * saltos}{self._nome(aid)}  ({saltos} salto(s))",
                   tema.F_NORMAL).pack(anchor="w")
        if len(self._alcancados) <= 1:
            Rotulo(self._resultado, "Nenhum outro ativo alcançável.", tema.F_PEQUENA, tema.TEXTO_SUAVE).pack(anchor="w")
        destino = self._id(self._destino.valor)
        self._caminho = self._grafo.caminho_mais_curto(origem, destino) if destino else []
        if destino:
            texto = (" → ".join(self._nome(a) for a in self._caminho) if self._caminho
                     else "inalcançável a partir da origem ✔")
            Rotulo(self._resultado, f"Caminho mais curto: {texto}", tema.F_NORMAL, tema.VIOLETA_CLARO,
                   wraplength=340, justify="left").pack(anchor="w", pady=(6, 0))
        Rotulo(self._resultado, "Ordem DFS: " + " → ".join(self._nome(a) for a in self._grafo.dfs(origem)),
               tema.F_PEQUENA, tema.TEXTO_SUAVE, wraplength=340, justify="left").pack(anchor="w", pady=(6, 0))
        ciclo = self._grafo.encontrar_ciclo()
        Rotulo(self._resultado, ("⚠ Ciclo (DFS): " + " → ".join(self._nome(c) for c in ciclo)) if ciclo
               else "✔ Sem ciclos de dependência", tema.F_PEQUENA,
               tema.CORES_SEVERIDADE["Média"] if ciclo else tema.VERDE, wraplength=340,
               justify="left").pack(anchor="w", pady=(4, 0))
        self._desenhar()

    def _desenhar(self):
        c = self._canvas
        c.delete("all")
        ativos = getattr(self, "_ativos", {})
        largura, altura = c.winfo_width(), c.winfo_height()
        if not ativos or largura < 60:
            return
        ids = sorted(ativos)
        raio = min(largura, altura) / 2 - 50
        cx, cy = largura / 2, altura / 2
        pos = {aid: (cx + raio * math.cos(2 * math.pi * i / len(ids) - math.pi / 2),
                     cy + raio * math.sin(2 * math.pi * i / len(ids) - math.pi / 2)) for i, aid in enumerate(ids)}
        no = 22
        caminho = set(zip(self._caminho, self._caminho[1:]))
        for o, d in self._grafo.arestas():
            (x1, y1), (x2, y2) = pos[o], pos[d]
            dist = math.hypot(x2 - x1, y2 - y1) or 1
            ux, uy = (x2 - x1) / dist, (y2 - y1) / dist
            destaque = (o, d) in caminho
            c.create_line(x1 + ux * no, y1 + uy * no, x2 - ux * no, y2 - uy * no, arrow="last",
                          fill=tema.VIOLETA_CLARO if destaque else tema.BORDA, width=3 if destaque else 1.5)
            c.create_text((x1 + x2) / 2, (y1 + y2) / 2 - 8, text=str(self._grafo.peso(o, d)),
                          fill=tema.TEXTO_APAGADO, font=tema.F_PEQUENA)
        x_vals = getattr(self, "_x", {})
        maior = max(x_vals.values(), default=0) or 1
        origem = self._id(self._origem.valor)
        for aid, (x, y) in pos.items():
            intensidade = x_vals.get(aid, 0) / maior
            contorno = tema.VERMELHO if aid == origem else tema.VIOLETA_CLARO if aid in self._alcancados else tema.BORDA
            c.create_oval(x - no, y - no, x + no, y + no, outline=contorno, width=3 if aid in self._alcancados else 1,
                          fill=tema.misturar(tema.VERMELHO, tema.CARTAO, 0.15 + 0.6 * intensidade))
            c.create_text(x, y, text=f"{x_vals.get(aid, 0):.1f}", fill=tema.TEXTO, font=tema.F_PEQUENA)
            c.create_text(x, y + no + 11, text=self._nome(aid), fill=tema.TEXTO_SUAVE, font=tema.F_PEQUENA)
