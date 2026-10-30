import numpy as np
import pytest

from algoritmos.risco import analisar, montar_A, montar_M_v, propagar, risco_proprio, somas_parciais
from dominio.excecoes import ErroValidacao
from persistencia import dependencias as deps

WEB, APP, BANCO = 10001, 10002, 10003


@pytest.fixture
def ativos_da_aula():
    v1 = {"nome": "V1", "cvss": 9.8}
    v2 = {"nome": "V2", "cvss": 5.3}
    v3 = {"nome": "V3", "cvss": 7.5}
    return [
        {"id": WEB, "nome": "Servidor Web", "vulnerabilidades": [v1, v2]},
        {"id": APP, "nome": "Servidor de Aplicacao", "vulnerabilidades": [v3]},
        {"id": BANCO, "nome": "Banco de Dados", "vulnerabilidades": [v2]},
    ]


@pytest.fixture
def dependencias_da_aula():
    return [
        {"origem": APP, "destino": WEB, "peso": 0.2},
        {"origem": WEB, "destino": APP, "peso": 0.5},
        {"origem": APP, "destino": BANCO, "peso": 0.6},
    ]


def test_s3_09_matriz_M_e_b(ativos_da_aula):
    M, v, nomes = montar_M_v(ativos_da_aula)
    assert nomes == ("V1", "V2", "V3")
    assert M.tolist() == [[1, 1, 0], [0, 0, 1], [0, 1, 0]]
    assert np.allclose(risco_proprio(M, v), [15.1, 7.5, 5.3])


def test_s3_09_dimensoes_incompativeis():
    with pytest.raises(ErroValidacao):
        risco_proprio(np.ones((2, 3)), np.ones(2))


def test_s3_10_somas_parciais_batem_com_a_tabela_da_aula(ativos_da_aula, dependencias_da_aula):
    r = analisar(ativos_da_aula, dependencias_da_aula)
    parciais = somas_parciais(r.b, r.A, 10)
    esperado = {0: [15.10, 7.50, 5.30], 1: [16.60, 15.05, 9.80], 2: [18.11, 15.80, 14.33],
                5: [18.43, 16.71, 15.28], 10: [18.44, 16.72, 15.33]}
    for salto, valores in esperado.items():
        assert np.allclose(np.round(parciais[salto], 2), valores), salto


def test_s3_10_solucao_do_sistema_e_o_limite_das_somas(ativos_da_aula, dependencias_da_aula):
    r = analisar(ativos_da_aula, dependencias_da_aula)
    assert np.allclose((np.eye(3) - r.A) @ r.x, r.b)
    assert np.allclose(r.x, somas_parciais(r.b, r.A, 200)[-1])
    assert np.allclose(np.round(r.x, 2), [18.44, 16.72, 15.33])


def test_s3_11_determinante_e_raio_espectral(ativos_da_aula, dependencias_da_aula):
    r = analisar(ativos_da_aula, dependencias_da_aula)
    assert r.determinante == pytest.approx(0.9)
    assert r.raio_espectral < 1


def test_s3_11_sistema_singular_e_recusado():
    A = np.array([[0.0, 1.0], [1.0, 0.0]])
    with pytest.raises(ErroValidacao):
        propagar(np.array([1.0, 1.0]), A)


def test_s3_12_condicao_e_residuo(ativos_da_aula, dependencias_da_aula):
    r = analisar(ativos_da_aula, dependencias_da_aula)
    assert 1 <= r.condicao < 10
    assert r.residuo < 1e-12


def test_s3_12_mal_condicionado_e_recusado():
    A = np.array([[0.0, 0.999999999], [0.999999999, 0.0]])
    with pytest.raises(ErroValidacao):
        propagar(np.array([1.0, 1.0]), A)


def test_sem_dependencias_x_igual_b(ativos_da_aula):
    r = analisar(ativos_da_aula)
    assert np.allclose(r.x, r.b)


def test_ranking(ativos_da_aula, dependencias_da_aula):
    assert [linha[1] for linha in analisar(ativos_da_aula, dependencias_da_aula).ranking()] == [
        "Servidor Web", "Servidor de Aplicacao", "Banco de Dados"]


@pytest.mark.parametrize("dep", [
    {"origem": WEB, "destino": WEB, "peso": 0.5},
    {"origem": WEB, "destino": APP, "peso": 1.0},
    {"origem": WEB, "destino": APP, "peso": 0},
])
def test_dependencias_invalidas(dep):
    with pytest.raises(ErroValidacao):
        montar_A((WEB, APP), [dep])


def test_dependencia_para_ativo_inexistente_e_ignorada():
    assert not montar_A((WEB,), [{"origem": 99999, "destino": WEB, "peso": 0.5}]).any()


def test_legado_com_severidade_textual():
    _m, v, _ = montar_M_v([{"id": 1, "nome": "X", "vulnerabilidades": [{"nome": "Y", "severidade": "Alta"}]}])
    assert v.tolist() == [7.0]


def test_vazio():
    r = analisar([])
    assert r.x.size == 0


def test_persistencia_de_dependencias(tmp_path, dependencias_da_aula):
    caminho = tmp_path / "dep.json"
    deps.gravar(dependencias_da_aula + [{"origem": APP, "destino": WEB, "peso": "0,3"}], caminho)
    lidas = deps.ler(caminho)
    assert len(lidas) == 3
    assert {"origem": APP, "destino": WEB, "peso": 0.3} in lidas
    assert len(deps.remover_do_ativo(BANCO, caminho)) == 2
