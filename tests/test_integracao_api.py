import random

import pytest
from fastapi.testclient import TestClient

from api.app_rest import criar_app
from api.cliente_api import ClienteAPI
from persistencia.repositorio import RepositorioMemoria
from servicos.servico_ativos import ServicoAtivos


@pytest.fixture
def cliente():
    app = criar_app(ServicoAtivos(RepositorioMemoria(), aleatorio=random.Random(5)))
    with TestClient(app) as c:
        yield c


def test_health(cliente):
    assert cliente.get("/health").json() == {"status": "ok"}


def test_ciclo_crud_completo(cliente, dados_servidor):
    criado = cliente.post("/ativos", json=dados_servidor)
    assert criado.status_code == 201
    ativo_id = criado.json()["id"]
    assert criado.headers["location"] == f"/ativos/{ativo_id}"

    assert cliente.get(f"/ativos/{ativo_id}").json()["nome"] == "Servidor Web"

    atualizado = cliente.put(f"/ativos/{ativo_id}", json={**dados_servidor, "local": "Sala Cofre"})
    assert atualizado.status_code == 200 and atualizado.json()["local"] == "Sala Cofre"

    assert cliente.delete(f"/ativos/{ativo_id}").status_code == 204
    assert cliente.get(f"/ativos/{ativo_id}").status_code == 404


@pytest.mark.parametrize("alteracao", [
    {"nome": ""},
    {"local": "Sala@2"},
    {"vulnerabilidades": [{"nome": "XSS", "severidade": "gravissima"}]},
    {"vulnerabilidades": [{"nome": "XSS", "severidade": "Alta", "progresso": 11}]},
])
def test_dados_invalidos_retornam_422(cliente, dados_servidor, alteracao):
    resposta = cliente.post("/ativos", json={**dados_servidor, **alteracao})
    assert resposta.status_code == 422
    assert cliente.get("/ativos").json() == []


def test_id_nao_numerico_retorna_422(cliente):
    assert cliente.get("/ativos/abc").status_code == 422


def test_filtros_ordenacao_e_paginacao(cliente, dados_servidor, dados_notebook):
    cliente.post("/ativos", json=dados_servidor)
    cliente.post("/ativos", json=dados_notebook)
    assert [a["nome"] for a in cliente.get("/ativos", params={"tipo": "Notebook"}).json()] == ["Notebook Financeiro"]
    assert len(cliente.get("/ativos", params={"severidade_minima": "Crítica"}).json()) == 1
    nomes = [a["nome"] for a in cliente.get("/ativos", params={"ordenar_por": "nome", "ordem": "desc"}).json()]
    assert nomes == ["Servidor Web", "Notebook Financeiro"]
    assert len(cliente.get("/ativos", params={"limite": 1}).json()) == 1
    assert cliente.get("/ativos", params={"ordenar_por": "senha"}).status_code == 422


def test_sub_recurso_vulnerabilidades(cliente, dados_notebook):
    ativo_id = cliente.post("/ativos", json=dados_notebook).json()["id"]
    resposta = cliente.post(f"/ativos/{ativo_id}/vulnerabilidades",
                            json={"nome": "USB liberado", "severidade": "media"})
    assert resposta.status_code == 201
    vuls = cliente.get(f"/ativos/{ativo_id}/vulnerabilidades").json()
    assert vuls[0]["severidade"] == "Média" and vuls[0]["status"] == "Aberta"
    assert cliente.delete(f"/ativos/{ativo_id}/vulnerabilidades/0").status_code == 204
    assert cliente.delete(f"/ativos/{ativo_id}/vulnerabilidades/0").status_code == 422


def test_relatorio_risco(cliente, dados_servidor, dados_notebook):
    cliente.post("/ativos", json=dados_notebook)
    cliente.post("/ativos", json=dados_servidor)
    ranking = cliente.get("/relatorios/risco").json()
    assert ranking[0]["nome"] == "Servidor Web" and ranking[0]["risco"] > ranking[1]["risco"]


def test_cliente_python_contra_api_real(cliente, dados_servidor, tmp_path):
    api = ClienteAPI(url="http://testserver/ativos", sessao=cliente, arquivo_local=tmp_path / "cache.txt")
    criado = api.cadastrar(dados_servidor)
    assert [a["id"] for a in api.listar()] == [criado["id"]]
    assert (tmp_path / "cache.txt").exists()
    assert api.remover(criado["id"]) is True
    assert api.listar() == []
