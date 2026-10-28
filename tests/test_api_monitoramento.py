import random
from fastapi.testclient import TestClient
from api.app_rest import criar_app
from persistencia.repositorio import RepositorioMemoria
from servicos.servico_ativos import ServicoAtivos


def _cliente(chave):
    return TestClient(criar_app(ServicoAtivos(RepositorioMemoria(), aleatorio=random.Random(1)), chave_api=chave))


def test_sem_chave_continua_igual_a_v2():
    assert _cliente("").get("/ativos").status_code == 200


def test_com_chave_exige_cabecalho():
    cliente = _cliente("segredo")
    assert cliente.get("/ativos").status_code == 401
    assert cliente.get("/ativos", headers={"X-API-Key": "errada"}).status_code == 401
    assert cliente.get("/ativos", headers={"X-API-Key": "segredo"}).status_code == 200
    assert cliente.get("/health").json() == {"status": "ok", "versao": "3.0.0"}


def test_requisicao_vira_log_estruturado(caplog):
    caplog.set_level("INFO", logger="api.app_rest")
    _cliente("").get("/ativos")
    registro = next(r for r in caplog.records if r.getMessage() == "requisicao")
    assert (registro.metodo, registro.rota, registro.status) == ("GET", "/ativos", 200)
