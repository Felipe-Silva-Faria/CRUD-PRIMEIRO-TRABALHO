import random
import time
import tkinter as tk
from tkinter import ttk

from algoritmos.ordenacao import ALGORITMOS
from dominio.excecoes import ErroCRUD
from interface.moderna import preferencias, tema
from interface.moderna.componentes import Botao, Cartao, Rotulo, Tabela
from interface.moderna.paginas.base import Pagina

DESCRICOES = {
    "bolha": "Bubble sort (S2) · O(n²)", "selecao": "Selection sort (S2) · O(n²)",
    "insercao": "Insertion sort (S2) · O(n²), O(n) se quase ordenada",
    "merge": "Merge sort recursivo (S2) · O(n log n), estável",
    "quick": "Quick sort pivô aleatório (S2) · O(n log n) médio",
    "merge_iterativo": "Merge sort bottom-up (S4_11) · sem recursão, estável",
    "quick_hoare": "Quick sort Hoare + mediana de 3 (S4_12) · in-place",
}


class PaginaConfiguracoes(Pagina):
    def construir(self):
        self.cabecalho("Configurações", "Preferências, conexão e desempenho.")
        corpo = tk.Frame(self, bg=tema.PAINEL)
        corpo.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        corpo.columnconfigure(0, weight=1, uniform="c")
        corpo.columnconfigure(1, weight=1, uniform="c")
        ordem = Cartao(corpo, padx=18, pady=14)
        ordem.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        Rotulo(ordem, "Algoritmo de ordenação das tabelas", tema.F_NEGRITO).pack(anchor="w")
        self._algoritmo = tk.StringVar()
        for nome in ALGORITMOS:
            ttk.Radiobutton(ordem, text=DESCRICOES.get(nome, nome), value=nome, variable=self._algoritmo,
                            command=self._trocar).pack(anchor="w", pady=2)
        conexao = Cartao(corpo, padx=18, pady=14)
        conexao.grid(row=0, column=1, sticky="nsew")
        Rotulo(conexao, "Conexão (cliente-servidor)", tema.F_NEGRITO).pack(anchor="w")
        self._texto_conexao = Rotulo(conexao, "", tema.F_NORMAL, tema.TEXTO_SUAVE, wraplength=420, justify="left")
        self._texto_conexao.pack(anchor="w", pady=(6, 8))
        Botao(conexao, "Recarregar / sincronizar", self._sincronizar, "secundario").pack(anchor="w")

        bench = Cartao(corpo, padx=18, pady=14)
        bench.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        topo = tk.Frame(bench, bg=tema.CARTAO)
        topo.pack(fill="x")
        Rotulo(topo, "Benchmark: tempo para ordenar n notas CVSS (ms)", tema.F_NEGRITO).pack(side="left")
        Botao(topo, "Executar", self._benchmark).pack(side="right")
        self._tamanhos = (500, 1000, 2000)
        self._tabela = Tabela(bench, [("alg", "Algoritmo", 200, "w")] +
                              [(str(n), f"n = {n}", 100, "center") for n in self._tamanhos], altura=7)
        self._tabela.pack(fill="x", pady=(10, 0))
        Rotulo(bench, "Benchmark completo (buscas, comparações, hash e BST): python -m analise.benchmark",
               tema.F_PEQUENA, tema.TEXTO_SUAVE).pack(anchor="w", pady=(8, 0))

    def carregar(self, **_):
        self._algoritmo.set(self.painel.algoritmo)
        if self.app.descricao_conexao == "local":
            texto = "Modo LOCAL: dados no banco_ativos.txt (RepositorioJsonLines)."
        elif self.painel.online:
            texto = "Conectado à API (ClienteAPI). Sem operações pendentes." if not self.painel.pendentes \
                else f"Conectado à API. {self.painel.pendentes} operação(ões) aguardando envio."
        else:
            texto = (f"API indisponível: usando o arquivo local. {self.painel.pendentes} operação(ões) "
                     "na fila serão enviadas quando a API voltar.")
        self._texto_conexao.configure(text=texto)

    def _trocar(self):
        self.painel.algoritmo = self._algoritmo.get()
        preferencias.gravar(algoritmo=self.painel.algoritmo)

    def _sincronizar(self):
        try:
            self.painel.recarregar()
        except ErroCRUD as erro:
            self.erro(erro)
        self.app.atualizar_indicador()
        self.recarregar()

    def _benchmark(self):
        rng = random.Random(42)
        linhas = []
        for nome, funcao in ALGORITMOS.items():
            tempos = []
            for n in self._tamanhos:
                dados = [round(rng.uniform(0, 10), 1) for _ in range(n)]
                inicio = time.perf_counter()
                funcao(dados)
                tempos.append(f"{(time.perf_counter() - inicio) * 1000:.2f}")
            linhas.append((nome, (nome, *tempos)))
        self._tabela.carregar(linhas)
