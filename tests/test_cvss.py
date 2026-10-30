import pytest

from algoritmos.cvss import (
    arredondar_para_cima,
    calcular_cvss,
    descrever_vetor,
    faixa_qualitativa,
    formatar,
    interpretar_entrada,
    montar_vetor,
    nota_de_dict,
    nota_de_rotulo_legado,
    validar_nota,
)
from dominio.excecoes import ErroValidacao


@pytest.mark.parametrize("vetor, nota", [
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", 9.8),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", 10.0),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H", 7.5),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N", 5.3),
    ("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N", 4.3),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", 6.1),
    ("CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H", 7.8),
    ("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H", 9.9),
    ("CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N", 5.9),
    ("CVSS:3.1/AV:P/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N", 1.6),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N", 0.0),
])
def test_notas_de_referencia(vetor, nota):
    assert calcular_cvss(vetor).nota == nota


def test_cenario_da_aula_risco_proprio():
    v1 = calcular_cvss("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H").nota
    v2 = calcular_cvss("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N").nota
    v3 = calcular_cvss("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H").nota
    assert round(v1 + v2, 1) == 15.1 and v3 == 7.5 and v2 == 5.3


def test_ordem_das_metricas_e_minusculas_nao_importam():
    a = calcular_cvss("cvss:3.1/a:h/i:h/c:h/s:u/ui:n/pr:n/ac:l/av:n")
    assert a.nota == 9.8
    assert a.vetor == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"


def test_resultado_traz_subnotas():
    r = calcular_cvss("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
    assert r.impacto == 5.9 and r.explorabilidade == 3.9 and r.faixa == "Crítica"


@pytest.mark.parametrize("vetor", [
    "",
    "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
    "CVSS:4.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
    "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H",
    "CVSS:3.1/AV:X/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
    "CVSS:3.1/AV:N/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
    "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/ZZ:Q",
    "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/AH",
])
def test_vetores_invalidos(vetor):
    with pytest.raises(ErroValidacao):
        calcular_cvss(vetor)


@pytest.mark.parametrize("nota, faixa", [
    (0.0, "Nenhuma"), (0.1, "Baixa"), (3.9, "Baixa"), (4.0, "Média"), (6.9, "Média"),
    (7.0, "Alta"), (8.9, "Alta"), (9.0, "Crítica"), (10.0, "Crítica")])
def test_faixas_qualitativas_nos_limites(nota, faixa):
    assert faixa_qualitativa(nota) == faixa


@pytest.mark.parametrize("valor", [-0.1, 10.1, "abc", None, True, 5.25, float("nan")])
def test_nota_invalida(valor):
    with pytest.raises(ErroValidacao):
        validar_nota(valor)


def test_arredondamento_oficial_3_1():
    assert arredondar_para_cima(4.0) == 4.0
    assert arredondar_para_cima(4.02) == 4.1
    assert arredondar_para_cima(4.000001) == 4.0


@pytest.mark.parametrize("entrada, esperado", [
    ("9.8", (9.8, "")), ("7,5", (7.5, "")), (4, (4.0, "")),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", (9.8, "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")),
])
def test_interpretar_entrada(entrada, esperado):
    assert interpretar_entrada(entrada) == esperado


@pytest.mark.parametrize("entrada", ["", "alta", "9.8.1", "100"])
def test_interpretar_entrada_invalida(entrada):
    with pytest.raises(ErroValidacao):
        interpretar_entrada(entrada)


def test_montar_e_descrever_vetor():
    metricas = {"AV": "N", "AC": "L", "PR": "N", "UI": "N", "S": "U", "C": "H", "I": "H", "A": "H"}
    vetor = montar_vetor(metricas)
    assert calcular_cvss(vetor).nota == 9.8
    assert descrever_vetor(vetor)["Vetor de ataque"] == "N"


def test_rotulo_legado_vira_minimo_da_faixa():
    assert [nota_de_rotulo_legado(r) for r in ("Baixa", "media", "ALTA", "Crítica")] == [0.1, 4.0, 7.0, 9.0]


def test_nota_de_dict_prioriza_vetor():
    assert nota_de_dict({"cvss": 1.0, "vetor_cvss": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}) == 9.8
    assert nota_de_dict({"cvss": 6.5}) == 6.5
    assert nota_de_dict({"severidade": "Alta"}) == 7.0


def test_formatar():
    assert formatar(9.8) == "9.8 (Crítica)"
    assert formatar(5, com_faixa=False) == "5.0"
