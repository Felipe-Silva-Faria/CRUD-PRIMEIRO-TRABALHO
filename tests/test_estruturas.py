import pytest

from dominio.excecoes import FilaVaziaError
from estruturas.fila import Fila, FilaLimitada
from estruturas.lista_encadeada import ListaEncadeada


class TestListaEncadeada:
    def test_vazia(self):
        lista = ListaEncadeada()
        assert len(lista) == 0 and not lista and list(lista) == []

    def test_insercoes_mantem_ordem(self):
        lista = ListaEncadeada([2, 3])
        lista.adicionar_no_inicio(1)
        lista.adicionar_no_fim(4)
        assert list(lista) == [1, 2, 3, 4]
        assert lista[0] == 1 and lista[-1] == 4

    def test_remover_do_inicio_ate_esvaziar(self):
        lista = ListaEncadeada([1, 2])
        assert lista.remover_do_inicio() == 1
        assert lista.remover_do_inicio() == 2
        with pytest.raises(IndexError):
            lista.remover_do_inicio()
        lista.adicionar_no_fim(9)
        assert list(lista) == [9]

    @pytest.mark.parametrize("alvo, esperado", [(1, [2, 3]), (2, [1, 3]), (3, [1, 2]), (7, [1, 2, 3])])
    def test_remover_primeiro(self, alvo, esperado):
        lista = ListaEncadeada([1, 2, 3])
        lista.remover_primeiro(lambda v: v == alvo)
        assert list(lista) == esperado
        lista.adicionar_no_fim(99)
        assert list(lista)[-1] == 99

    def test_inverter(self):
        lista = ListaEncadeada([1, 2, 3])
        lista.inverter()
        assert list(lista) == [3, 2, 1]
        lista.adicionar_no_fim(0)
        assert list(lista) == [3, 2, 1, 0]

    def test_contains_e_buscar(self):
        lista = ListaEncadeada(["a", "bb", "ccc"])
        assert "bb" in lista and "z" not in lista
        assert lista.buscar(lambda s: len(s) == 3) == "ccc"

    def test_indice_invalido(self):
        with pytest.raises(IndexError):
            ListaEncadeada([1])[5]


class TestFila:
    def test_fifo(self):
        fila = Fila()
        for item in "abc":
            fila.enfileirar(item)
        assert fila.espiar() == "a"
        assert [fila.desenfileirar() for _ in range(3)] == ["a", "b", "c"]
        assert fila.esta_vazia()

    def test_fila_vazia_lanca_erro_especifico(self):
        with pytest.raises(FilaVaziaError):
            Fila().desenfileirar()

    def test_fila_limitada_descarta_mais_antigo(self):
        fila = FilaLimitada(3, [1, 2, 3])
        fila.enfileirar(4)
        assert list(fila) == [2, 3, 4]
        assert len(fila) == 3

    def test_fila_limitada_e_uma_fila(self):
        assert isinstance(FilaLimitada(1), Fila)

    def test_capacidade_invalida(self):
        with pytest.raises(ValueError):
            FilaLimitada(0)
