import pytest
from dominio.entidades import criar_ativo
from persistencia.relatorios_sql import RelatorioSQL


@pytest.fixture
def rel(dados_servidor, dados_notebook):
    ativos = [
        criar_ativo({**dados_servidor, "id": 10001}),
        criar_ativo({**dados_notebook, "id": 10002, "vulnerabilidades": [
            {"nome": "USB liberado", "cvss": 4.3, "responsavel": "Ana Souza"},
            {"nome": "Disco sem criptografia", "cvss": 7.5, "progresso": 10}]}),
        criar_ativo({"id": 10003, "nome": "Roteador Sala", "tipo": "Roteador", "local": "Recepcao"}),
    ]
    with RelatorioSQL(ativos) as r:
        yield r


def test_resumo(rel):
    r = rel.resumo()
    assert (r["total"], r["abertas"], r["criticas"], r["ativos"]) == (4, 3, 1, 3)
    assert r["risco_medio"] == pytest.approx(round((10.0 + 2.65 + 4.3) / 3, 2))


def test_left_join_inclui_ativo_sem_vulnerabilidade(rel):
    top = rel.top_ativos(10)
    assert [(t["nome"], t["abertas"]) for t in top] == [
        ("Servidor Web", 2), ("Notebook Financeiro", 1), ("Roteador Sala", 0)]


def test_anti_join(rel):
    assert [a["nome"] for a in rel.ativos_sem_vulnerabilidades()] == ["Roteador Sala"]


def test_group_by_e_having(rel):
    assert sum(s["total"] for s in rel.por_severidade()) == 4
    locais = rel.risco_por_local()
    assert [linha["local"] for linha in locais] == ["Data Center", "Sala Dois"]


def test_parametro_impede_sql_injection(rel):
    assert len(rel.buscar_por_responsavel("Ana Souza")) == 2
    assert rel.buscar_por_responsavel("x' OR '1'='1") == []
