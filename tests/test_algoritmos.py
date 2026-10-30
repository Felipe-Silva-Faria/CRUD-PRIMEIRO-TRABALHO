import random
import pytest
from algoritmos.busca import busca_binaria, busca_binaria_recursiva, busca_linear, busca_por_prefixo, indexar
from algoritmos.ordenacao import ALGORITMOS, ordenar

CASOS = [
    [],
    [1],
    [2, 1],
    [1, 2, 3, 4, 5],
    [5, 4, 3, 2, 1],
    [3, 1, 3, 1, 3],
    random.Random(1).sample(range(1000), 200),
]


@pytest.mark.parametrize("nome", ALGORITMOS)
@pytest.mark.parametrize("entrada", CASOS)
def test_ordena_igual_ao_sorted(nome, entrada):
    assert ALGORITMOS[nome](entrada) == sorted(entrada)


@pytest.mark.parametrize("nome", ALGORITMOS)
def test_reverso_e_chave(nome):
    palavras = ["banana", "kiwi", "abacaxi", "uva"]
    assert ALGORITMOS[nome](palavras, chave=len, reverso=True)[0] == "abacaxi"


@pytest.mark.parametrize("nome", ALGORITMOS)
def test_nao_altera_original(nome):
    original = [3, 1, 2]
    ALGORITMOS[nome](original)
    assert original == [3, 1, 2]


@pytest.mark.parametrize("nome", ["bolha", "insercao", "merge"])
def test_estabilidade(nome):
    registros = [("b", 2), ("a", 1), ("c", 2), ("d", 1)]
    resultado = ALGORITMOS[nome](registros, chave=lambda r: r[1])
    assert resultado == [("a", 1), ("d", 1), ("b", 2), ("c", 2)]


def test_algoritmo_desconhecido():
    with pytest.raises(ValueError):
        ordenar([1], algoritmo="magico")


ORDENADA = [2, 4, 6, 8, 10, 12]


@pytest.mark.parametrize("busca", [busca_binaria, busca_binaria_recursiva, busca_linear])
@pytest.mark.parametrize("alvo, indice", [(2, 0), (12, 5), (8, 3), (7, -1), (0, -1), (99, -1)])
def test_buscas(busca, alvo, indice):
    assert busca(ORDENADA, alvo) == indice


@pytest.mark.parametrize("busca", [busca_binaria, busca_binaria_recursiva])
def test_busca_binaria_lista_vazia(busca):
    assert busca([], 1) == -1


def test_busca_por_prefixo():
    nomes = sorted(["SERVIDOR_A", "SERVIDOR_B", "ROTEADOR", "SWITCH", "NOTEBOOK"])
    assert busca_por_prefixo(nomes, "SERV") == ["SERVIDOR_A", "SERVIDOR_B"]
    assert busca_por_prefixo(nomes, "X") == []


def test_indexar():
    assert indexar([{"id": 1}, {"id": 2}], chave=lambda d: d["id"])[2] == {"id": 2}
