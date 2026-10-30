import csv
import tkinter as tk
from tkinter import filedialog, ttk
from interface.moderna import tema
from interface.moderna.componentes import Botao, Cartao, CartaoMetrica, GraficoRosca, Rotulo, Tabela
from interface.moderna.paginas.base import Pagina


def celula_segura(valor):
    texto = "" if valor is None else str(valor)
    return "'" + texto if texto[:1] in ("=", "+", "-", "@", "\t", "\r") else texto


class PaginaRelatorios(Pagina):
    def construir(self):
        direita = self.cabecalho("Relatórios", "Consultas SQL sobre o mesmo esquema do RepositorioSQLite.")
        Botao(direita, "⤓  Exportar CSV", self._exportar).pack()
        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        geral = tk.Frame(abas, bg=tema.PAINEL, pady=12)
        abas.add(geral, text="  Visão Geral  ")
        linha = tk.Frame(geral, bg=tema.PAINEL)
        linha.pack(fill="x")
        self._metricas = {}
        for i, (chave, titulo) in enumerate([("total", "Vulnerabilidades"), ("criticas", "Críticas abertas"),
                                             ("risco_medio", "Risco residual médio"), ("cvss_max", "Maior CVSS")]):
            cartao = CartaoMetrica(linha, titulo)
            cartao.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            linha.columnconfigure(i, weight=1, uniform="m")
            self._metricas[chave] = cartao
        baixo = tk.Frame(geral, bg=tema.PAINEL)
        baixo.pack(fill="both", expand=True, pady=(12, 0))
        baixo.columnconfigure(0, weight=1, uniform="b")
        baixo.columnconfigure(1, weight=1, uniform="b")
        baixo.rowconfigure(0, weight=1)
        top = Cartao(baixo, padx=14, pady=10)
        top.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        Rotulo(top, "Top 5 ativos com mais vulnerabilidades abertas", tema.F_NEGRITO).pack(anchor="w")
        self._top = Tabela(top, [("nome", "Ativo", 170, "w"), ("abertas", "Abertas", 70, "center"),
                                 ("criticas", "Críticas", 70, "center"), ("risco", "Risco residual", 100, "center")],
                           altura=5)
        self._top.pack(fill="both", expand=True, pady=(6, 0))
        self._legenda(top, "ativos a LEFT JOIN vulnerabilidades v ON ... AND v.progresso < 10 GROUP BY a.id LIMIT 5")
        rosca = Cartao(baixo, padx=14, pady=10)
        rosca.grid(row=0, column=1, sticky="nsew")
        Rotulo(rosca, "Por severidade", tema.F_NEGRITO).pack(anchor="w")
        self._rosca = GraficoRosca(rosca, altura=220)
        self._rosca.pack(fill="both", expand=True)
        self._legenda(rosca, "GROUP BY severidade")

        status = tk.Frame(abas, bg=tema.PAINEL, pady=12)
        abas.add(status, text="  Status e Tipos  ")
        self._tab_status = self._tabela_em(status, "Por status (GROUP BY status)",
                                           [("s", "Status", 200, "w"), ("t", "Total", 80, "center")])
        self._tab_tipo = self._tabela_em(status, "Por tipo de ativo (JOIN + GROUP BY a.tipo)",
                                         [("t", "Tipo", 200, "w"), ("n", "Vulnerabilidades", 120, "center"),
                                          ("m", "CVSS médio", 100, "center")])
        self._sem_vul = Rotulo(status, "", tema.F_NORMAL, tema.VERDE)
        self._sem_vul.pack(anchor="w", pady=(8, 0))

        local = tk.Frame(abas, bg=tema.PAINEL, pady=12)
        abas.add(local, text="  Risco por Local  ")
        self._tab_local = self._tabela_em(local, "INNER JOIN + WHERE progresso < 10 + GROUP BY a.local HAVING > 0",
                                          [("l", "Local", 200, "w"), ("a", "Ativos", 70, "center"),
                                           ("b", "Abertas", 70, "center"), ("r", "Risco residual", 110, "center")])

    @staticmethod
    def _legenda(mestre, texto):
        Rotulo(mestre, f"SQL: {texto}", tema.F_PEQUENA, tema.TEXTO_APAGADO, wraplength=520,
               justify="left").pack(anchor="w", pady=(4, 0))

    @staticmethod
    def _tabela_em(mestre, titulo, colunas):
        cartao = Cartao(mestre, padx=14, pady=10)
        cartao.pack(fill="x", pady=(0, 12))
        Rotulo(cartao, titulo, tema.F_NEGRITO).pack(anchor="w")
        tabela = Tabela(cartao, colunas, altura=5)
        tabela.pack(fill="x", pady=(6, 0))
        return tabela

    def carregar(self, **_):
        with self.painel.relatorio() as rel:
            resumo = rel.resumo()
            top = rel.top_ativos(5)
            severidades = rel.por_severidade()
            status = rel.por_status()
            tipos = rel.por_tipo_de_ativo()
            sem_vul = rel.ativos_sem_vulnerabilidades()
            locais = rel.risco_por_local()
        self._metricas["total"].definir(resumo["total"], f"{resumo['abertas']} abertas")
        self._metricas["criticas"].definir(resumo["criticas"], "CVSS ≥ 9.0", tema.cor_severidade("Crítica"))
        self._metricas["risco_medio"].definir(resumo["risco_medio"], "média das abertas")
        self._metricas["cvss_max"].definir(resumo["cvss_max"] or "-", f"{resumo['ativos']} ativos")
        self._top.carregar([(t["id"], (t["nome"], t["abertas"], t["criticas"] or 0, t["risco_residual"]))
                            for t in top])
        self._rosca.desenhar([(s["severidade"], s["total"], tema.cor_severidade(s["severidade"]))
                              for s in severidades])
        self._tab_status.carregar([(i, (s["status"], s["total"])) for i, s in enumerate(status)])
        self._tab_tipo.carregar([(i, (t["tipo"], t["total"], t["cvss_medio"])) for i, t in enumerate(tipos)])
        self._sem_vul.configure(text="Sem vulnerabilidades (anti-join): "
                                     + (", ".join(a["nome"] for a in sem_vul) or "nenhum"))
        self._tab_local.carregar([(i, (l_["local"], l_["ativos"], l_["abertas"], l_["risco_residual"]))
                                  for i, l_ in enumerate(locais)])

    def _exportar(self):
        caminho = filedialog.asksaveasfilename(parent=self, defaultextension=".csv",
                                               initialfile="relatorio_vulnerabilidades.csv",
                                               filetypes=[("CSV", "*.csv")])
        if not caminho:
            return
        with self.painel.relatorio() as rel:
            linhas = rel.vulnerabilidades_detalhadas()
        try:
            with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.writer(arquivo, delimiter=";")
                if linhas:
                    escritor.writerow(linhas[0].keys())
                for linha in linhas:
                    escritor.writerow([celula_segura(v) for v in linha.values()])
        except OSError as erro:
            self.erro(erro)
            return
        self.informar(f"{len(linhas)} vulnerabilidades exportadas para:\n{caminho}")
