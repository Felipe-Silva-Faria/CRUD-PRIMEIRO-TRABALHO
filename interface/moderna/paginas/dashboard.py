import tkinter as tk

from interface.moderna import tema
from interface.moderna.componentes import Badge, Cartao, CartaoMetrica, GraficoBarras, GraficoRosca, Rotulo, limpar
from interface.moderna.paginas.base import Pagina


class PaginaDashboard(Pagina):
    def construir(self):
        direita = self.cabecalho("Olá", "Aqui está o panorama geral do seu ambiente.")
        self._conexao = Rotulo(direita, "", tema.F_PEQUENA, tema.TEXTO_SUAVE)
        self._conexao.pack(anchor="e")
        linha = tk.Frame(self, bg=tema.PAINEL)
        linha.pack(fill="x", padx=28)
        self._cartoes = {}
        for i, (chave, titulo) in enumerate([("total", "Vulnerabilidades"), ("criticas", "Críticas (abertas)"),
                                             ("risco", "Risco residual (médio)"), ("ativos", "Ativos monitorados")]):
            cartao = CartaoMetrica(linha, titulo)
            cartao.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            linha.columnconfigure(i, weight=1, uniform="m")
            self._cartoes[chave] = cartao

        graficos = tk.Frame(self, bg=tema.PAINEL)
        graficos.pack(fill="both", expand=True, padx=28, pady=14)
        graficos.columnconfigure(0, weight=3, uniform="g")
        graficos.columnconfigure(1, weight=2, uniform="g")
        graficos.rowconfigure(0, weight=1)
        esquerda = Cartao(graficos, padx=16, pady=12)
        esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        Rotulo(esquerda, "Vulnerabilidades por nota CVSS", tema.F_NEGRITO).pack(anchor="w")
        Rotulo(esquerda, "GROUP BY CAST(cvss AS INTEGER)", tema.F_PEQUENA, tema.TEXTO_APAGADO).pack(anchor="w")
        self._barras = GraficoBarras(esquerda, altura=200)
        self._barras.pack(fill="both", expand=True, pady=(8, 0))
        direita_g = Cartao(graficos, padx=16, pady=12)
        direita_g.grid(row=0, column=1, sticky="nsew")
        Rotulo(direita_g, "Distribuição por Severidade", tema.F_NEGRITO).pack(anchor="w")
        self._rosca = GraficoRosca(direita_g, altura=210)
        self._rosca.pack(fill="both", expand=True, pady=(8, 0))

        prioridades = Cartao(self, padx=16, pady=12)
        prioridades.pack(fill="x", padx=28, pady=(0, 20))
        Rotulo(prioridades, "Prioridades: maiores CVSS em aberto", tema.F_NEGRITO).pack(anchor="w")
        self._lista = tk.Frame(prioridades, bg=tema.CARTAO)
        self._lista.pack(fill="x", pady=(6, 0))

    def carregar(self, **_):
        self._titulo.configure(text=f"Olá, {self.app.usuario.nome}")
        self._conexao.configure(text="API conectada" if self.painel.online
                                else f"Offline: {self.painel.pendentes} operação(ões) na fila")
        with self.painel.relatorio() as rel:
            resumo = rel.resumo()
            faixas = {f["faixa"]: f["total"] for f in rel.por_faixa_cvss()}
            severidades = {s["severidade"]: s["total"] for s in rel.por_severidade()}
            sem_vul = len(rel.ativos_sem_vulnerabilidades())
        self._cartoes["total"].definir(resumo["total"], f"{resumo['abertas']} em aberto", tema.VIOLETA_CLARO)
        self._cartoes["criticas"].definir(resumo["criticas"], "CVSS ≥ 9.0 sem correção",
                                          tema.cor_severidade("Crítica"))
        self._cartoes["risco"].definir(resumo["risco_medio"], "CVSS × (10 − progresso) / 10")
        self._cartoes["ativos"].definir(resumo["ativos"], f"{sem_vul} sem vulnerabilidades", tema.VERDE)
        notas = list(range(11))
        self._barras.desenhar([str(n) for n in notas], [faixas.get(n, 0) for n in notas],
                              [tema.cor_severidade("Crítica" if n >= 9 else "Alta" if n >= 7 else
                                                   "Média" if n >= 4 else "Baixa") for n in notas])
        self._rosca.desenhar([(s, severidades.get(s, 0), tema.cor_severidade(s))
                              for s in tema.ORDEM_SEVERIDADE if severidades.get(s)])
        limpar(self._lista)
        top = self.painel.mais_criticas(5)
        if not top:
            Rotulo(self._lista, "Nenhuma vulnerabilidade aberta. ✔", tema.F_NORMAL, tema.VERDE).pack(anchor="w")
        for r in top:
            linha = tk.Frame(self._lista, bg=tema.CARTAO, cursor="hand2")
            linha.pack(fill="x", pady=2)
            Badge(linha, f"{r.vul.cvss:.1f}", tema.cor_severidade(r.severidade)).pack(side="left")
            texto = Rotulo(linha, f"  {r.id}   {r.vul.nome}   ·   {r.ativo.nome}")
            texto.pack(side="left")
            Rotulo(linha, f"{r.status} ({r.vul.progresso}/10)", tema.F_PEQUENA,
                   tema.cor_progresso(r.vul.progresso)).pack(side="right", padx=8)
            for w in (linha, texto):
                w.bind("<Button-1>", lambda _e, i=r.id: self.app.navegar("detalhes", id_registro=i))
