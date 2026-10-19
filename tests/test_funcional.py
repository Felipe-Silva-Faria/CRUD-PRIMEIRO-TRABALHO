from unittest.mock import Mock

import pytest

from dominio.entidades import criar_ativo
from utilitarios.funcional import (
    achatar,
    agrupar_por,
    algum,
    compor,
    contar_vulnerabilidades,
    cronometrar,
    negar,
    por_severidade_minima,
    por_texto,
    por_tipo,
    risco_recursivo,
    somar,
    tentar_novamente,
    todos,
)


def par(n):
    return n % 2 == 0


def positivo(n):
    return n > 0


@pytest.fixture
def ativos(dados_servidor, dados_notebook):
    return [criar_ativo({**dados_servidor, "id": 10001}), criar_ativo({**dados_notebook, "id": 10002})]


def test_compor():
    assert compor(str, lambda x: x * 2, abs)(-4) == "8"
    assert compor()(5) == 5


def test_combinadores():
    assert todos(par, positivo)(4) and not todos(par, positivo)(-4)
    assert algum(par, positivo)(-4) and not algum(par, positivo)(-3)
    assert negar(par)(3)


def test_predicados_de_dominio(ativos):
    servidor, notebook = ativos
    assert por_tipo("Servidor")(servidor) and not por_tipo("Servidor")(notebook)
    assert por_texto("financeiro")(notebook)
    assert por_texto("data center")(servidor)
    assert por_severidade_minima("Alta")(servidor) and not por_severidade_minima("Baixa")(notebook)


def test_agrupar_e_somar(ativos):
    grupos = agrupar_por(ativos, lambda a: a.tipo.rotulo)
    assert set(grupos) == {"Servidor", "Notebook"}
    assert somar(ativos, lambda a: len(a.vulnerabilidades)) == 2


def test_cronometrar_preserva_metadados():
    def soma(a, b):
        return a + b
    soma.__doc__ = "doc"
    soma = cronometrar(soma)
    assert soma(1, 2) == 3 and soma.__name__ == "soma" and soma.__doc__ == "doc"


def test_tentar_novamente_ate_conseguir():
    funcao = Mock(side_effect=[ConnectionError, ConnectionError, "ok"])
    dormir = Mock()
    decorada = tentar_novamente(3, espera=0.1, excecoes=(ConnectionError,), dormir=dormir)(funcao)
    assert decorada() == "ok"
    assert funcao.call_count == 3
    assert [c.args[0] for c in dormir.call_args_list] == [0.1, 0.2]


def test_tentar_novamente_desiste():
    funcao = Mock(side_effect=ConnectionError("fora"))
    decorada = tentar_novamente(2, excecoes=(ConnectionError,), dormir=lambda s: None)(funcao)
    with pytest.raises(ConnectionError):
        decorada()
    assert funcao.call_count == 2


def test_tentar_novamente_nao_engole_outros_erros():
    funcao = Mock(side_effect=ValueError)
    with pytest.raises(ValueError):
        tentar_novamente(5, excecoes=(ConnectionError,), dormir=lambda s: None)(funcao)()
    assert funcao.call_count == 1


@pytest.mark.parametrize("entrada, esperado", [
    (1, [1]), ([], []), ([1, [2, [3, [4]]], 5], [1, 2, 3, 4, 5]), ([[[]]], [])])
def test_achatar(entrada, esperado):
    assert achatar(entrada) == esperado


def test_recursoes_de_dominio(ativos):
    assert contar_vulnerabilidades(ativos) == 2
    assert contar_vulnerabilidades([]) == 0
    assert risco_recursivo(ativos) == round(sum(a.risco_total() for a in ativos), 2)
