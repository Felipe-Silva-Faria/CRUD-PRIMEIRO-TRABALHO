from unittest.mock import MagicMock

import pytest
import requests

from api.cliente_api import ClienteAPI
from dominio.excecoes import ApiIndisponivel


def resposta(status, corpo=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = corpo
    return r


@pytest.fixture
def sessao():
    return MagicMock()


@pytest.fixture
def cliente(sessao, tmp_path):
    return ClienteAPI(url="http://api/ativos", sessao=sessao, arquivo_local=tmp_path / "local.txt", tentativas=1)


def test_online_usa_api(cliente, sessao):
    sessao.request.return_value = resposta(200, [])
    assert cliente.listar() == []
    sessao.request.assert_called_once_with("GET", "http://api/ativos", json=None, timeout=3)


def test_offline_cai_para_arquivo_e_avisa(cliente, sessao, dados_servidor):
    avisos = []
    cliente._ao_mudar_conexao = avisos.append
    sessao.request.side_effect = requests.ConnectionError("sem rede")
    criado = cliente.cadastrar(dados_servidor)
    assert cliente.online is False and avisos == [False]
    assert [a["id"] for a in cliente.listar()] == [criado["id"]]
    assert len(cliente.pendentes) == 1


def test_sincroniza_em_ordem_e_traduz_ids(cliente, sessao, dados_servidor):
    sessao.request.side_effect = requests.Timeout()
    provisorio = cliente.cadastrar(dados_servidor)["id"]
    cliente.atualizar(provisorio, {**dados_servidor, "local": "Outro Lugar"})
    assert len(cliente.pendentes) == 2

    sessao.request.side_effect = None
    sessao.request.return_value = resposta(201, {**dados_servidor, "id": 55555})
    assert cliente.sincronizar() == 2
    chamadas = [(c.args[0], c.args[1]) for c in sessao.request.call_args_list[-2:]]
    assert chamadas == [("POST", "http://api/ativos"), ("PUT", "http://api/ativos/55555")]
    assert cliente.pendentes.esta_vazia()


def test_falha_no_meio_da_sincronizacao_nao_perde_nada(cliente, sessao, dados_servidor, dados_notebook):
    sessao.request.side_effect = requests.ConnectionError()
    cliente.cadastrar(dados_servidor)
    cliente.cadastrar(dados_notebook)
    sessao.request.side_effect = [resposta(201, {"id": 1}), requests.ConnectionError()]
    with pytest.raises(ApiIndisponivel):
        cliente.sincronizar()
    assert len(cliente.pendentes) == 1
    assert cliente.pendentes.espiar().dados["nome"] == "Notebook Financeiro"


def test_erro_500_tambem_conta_como_offline(cliente, sessao):
    sessao.request.return_value = resposta(500)
    assert cliente.listar() == []
    assert cliente.online is False
