import random
import pytest
from fastapi.testclient import TestClient
from api.app_rest import criar_app
from persistencia.repositorio import RepositorioMemoria
from servicos.servico_ativos import ServicoAtivos


@pytest.fixture
def cliente():
    app = criar_app(ServicoAtivos(RepositorioMemoria(), aleatorio=random.Random(5)))
    with TestClient(app) as c:
        yield c


def test_cadastro_devolve_cvss(cliente, dados_servidor):
    resposta = cliente.post("/ativos", json=dados_servidor)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert [v["cvss"] for v in corpo["vulnerabilidades"]] == [10.0, 5.3]
    assert corpo["maior_cvss"] == 10.0 and corpo["risco_proprio"] == 15.3


def test_cliente_antigo_com_severidade_ainda_funciona(cliente, dados_notebook):
    dados = {**dados_notebook, "vulnerabilidades": [{"nome": "USB liberado", "severidade": "Média"}]}
    vul = cliente.post("/ativos", json=dados).json()["vulnerabilidades"][0]
    assert vul["cvss"] == 4.0 and vul["severidade"] == "Média"


@pytest.mark.parametrize("vul", [
    {"nome": "XSS"},
    {"nome": "XSS", "cvss": 11},
    {"nome": "XSS", "cvss": -1},
    {"nome": "XSS", "vetor_cvss": "CVSS:3.1/AV:N"},
    {"nome": "XSS", "severidade": "gravissima"},
])
def test_cvss_invalido_retorna_422(cliente, dados_notebook, vul):
    resposta = cliente.post("/ativos", json={**dados_notebook, "vulnerabilidades": [vul]})
    assert resposta.status_code == 422
    assert cliente.get("/ativos").json() == []


def test_vetor_tem_prioridade_sobre_nota(cliente, dados_notebook):
    dados = {**dados_notebook, "vulnerabilidades": [
        {"nome": "Falha", "cvss": 1.0, "vetor_cvss": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}]}
    assert cliente.post("/ativos", json=dados).json()["vulnerabilidades"][0]["cvss"] == 9.8


def test_endpoint_calcular(cliente):
    corpo = cliente.get("/cvss/calcular", params={"vetor": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H"}).json()
    assert corpo["cvss"] == 7.5 and corpo["severidade"] == "Alta"
    assert cliente.get("/cvss/calcular", params={"vetor": "CVSS:3.1/AV:Z/AC:L"}).status_code == 422


def test_filtro_e_ordenacao_por_cvss(cliente, dados_servidor, dados_notebook):
    cliente.post("/ativos", json=dados_servidor)
    cliente.post("/ativos", json={**dados_notebook, "vulnerabilidades": [{"nome": "USB", "cvss": 4.3}]})
    assert [a["nome"] for a in cliente.get("/ativos", params={"cvss_minimo": 9}).json()] == ["Servidor Web"]
    nomes = [a["nome"] for a in cliente.get("/ativos", params={"ordenar_por": "cvss", "ordem": "desc"}).json()]
    assert nomes == ["Servidor Web", "Notebook Financeiro"]


def test_sub_recurso_com_vetor(cliente, dados_notebook):
    ativo_id = cliente.post("/ativos", json=dados_notebook).json()["id"]
    resposta = cliente.post(f"/ativos/{ativo_id}/vulnerabilidades",
                            json={"nome": "SMB", "vetor_cvss": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"})
    assert resposta.status_code == 201
    assert cliente.get(f"/ativos/{ativo_id}/vulnerabilidades").json()[0]["cvss"] == 9.8
