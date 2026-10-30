import random
import pytest
from estruturas.arvore_bst import ArvoreBinariaBusca
from estruturas.grafo import GrafoDirecionado
from estruturas.tabela_hash import IndiceTexto, TabelaHash


class TestTabelaHash:
    def test_insere_atualiza_remove_e_redimensiona(self):
        t = TabelaHash()
        for i in range(100):
            t[f"k{i}"] = i
        assert len(t) == 100 and t["k42"] == 42 and t.fator_carga <= 0.75
        t["k42"] = -1
        assert t["k42"] == -1 and len(t) == 100
        del t["k42"]
        assert "k42" not in t and t.get("k42", "x") == "x"

    def test_chave_ausente(self):
        with pytest.raises(KeyError):
            TabelaHash()["nada"]

    def test_indice_por_prefixo_sem_acento_e_and(self):
        idx = IndiceTexto()
        idx.indexar("A", "SQL Injection Aplicação Interna Crítica")
        idx.indexar("B", "XSS Refletido Portal")
        assert idx.buscar("sql") == {"A"}
        assert idx.buscar("aplicacao critica") == {"A"}
        assert idx.buscar("sql portal") == set()
        assert idx.buscar("  ") is None
        idx.remover("A")
        assert idx.buscar("sql") == set()


class TestArvore:
    def _arvore(self, chaves):
        a = ArvoreBinariaBusca()
        for k in chaves:
            a.inserir(k, str(k))
        return a

    def test_em_ordem_e_reverso(self):
        chaves = random.Random(1).sample(range(1000), 200)
        a = self._arvore(chaves)
        assert [k for k, _ in a.em_ordem()] == sorted(chaves)
        assert [k for k, _ in a.em_ordem(reverso=True)] == sorted(chaves, reverse=True)

    def test_intervalo(self):
        assert [k for k, _ in self._arvore([50, 30, 70, 20, 40, 60, 80]).intervalo(35, 65)] == [40, 50, 60]

    @pytest.mark.parametrize("alvo", [20, 30, 50])
    def test_remover_tres_casos(self, alvo):
        a = self._arvore([50, 30, 70, 20, 40, 60, 80])
        a.remover(alvo)
        assert alvo not in a and len(a) == 6

    def test_balanceada_x_degenerada(self):
        degenerada = self._arvore(range(1023))
        balanceada = ArvoreBinariaBusca.construir_balanceada([(i, i) for i in range(1023)])
        assert degenerada.altura() == 1023 and balanceada.altura() == 10


class TestGrafo:
    WEB, APP, BANCO = 10001, 10002, 10003

    @pytest.fixture
    def grafo(self):
        return GrafoDirecionado.de_dependencias([self.WEB, self.APP, self.BANCO], [
            {"origem": self.APP, "destino": self.WEB, "peso": 0.2},
            {"origem": self.WEB, "destino": self.APP, "peso": 0.5},
            {"origem": self.APP, "destino": self.BANCO, "peso": 0.6},
            {"origem": 99999, "destino": self.WEB, "peso": 0.5},
        ])

    def test_bfs_e_caminho(self, grafo):
        assert grafo.bfs(self.WEB) == {self.WEB: 0, self.APP: 1, self.BANCO: 2}
        assert grafo.caminho_mais_curto(self.WEB, self.BANCO) == [self.WEB, self.APP, self.BANCO]
        assert grafo.caminho_mais_curto(self.BANCO, self.WEB) == []
        assert grafo.peso(self.APP, self.BANCO) == 0.6

    def test_dfs_e_ciclo_web_app(self, grafo):
        assert grafo.dfs(self.APP) == [self.APP, self.WEB, self.BANCO]
        ciclo = grafo.encontrar_ciclo()
        assert ciclo[0] == ciclo[-1] and set(ciclo) == {self.WEB, self.APP}
