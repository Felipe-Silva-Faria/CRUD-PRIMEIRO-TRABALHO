import pytest

from dominio.excecoes import ErroValidacao
from servicos.eventos import DADOS_ALTERADOS, BarramentoEventos
from servicos.painel import FonteLocal, PainelVulnerabilidades


@pytest.fixture
def painel(servico, dados_servidor, dados_notebook, tmp_path):
    servico.cadastrar(dados_servidor)
    servico.cadastrar({**dados_notebook, "vulnerabilidades": [{"nome": "USB liberado", "cvss": 4.3}]})
    return PainelVulnerabilidades(FonteLocal(servico), BarramentoEventos(), tmp_path / "dep.json")


def test_achata_vulnerabilidades_de_todos_os_ativos(painel):
    assert [r.vul.cvss for r in painel.vulnerabilidades()] == [10.0, 5.3, 4.3]


def test_busca_por_texto_usa_indice_hash(painel):
    assert [r.vul.nome for r in painel.vulnerabilidades(texto="log4")] == ["CVE-2021-44228 Log4Shell"]
    assert [r.ativo.nome for r in painel.vulnerabilidades(texto="financ")] == ["Notebook Financeiro"]


def test_filtro_cvss_pela_arvore(painel):
    assert [r.vul.cvss for r in painel.vulnerabilidades(cvss_min=5.0)] == [10.0, 5.3]


@pytest.mark.parametrize("algoritmo", ["merge", "quick", "merge_iterativo", "quick_hoare"])
def test_strategy_de_ordenacao(painel, algoritmo):
    painel.algoritmo = algoritmo
    assert [r.vul.cvss for r in painel.vulnerabilidades(ordenar_por="cvss", reverso=False)] == [4.3, 5.3, 10.0]


def test_criar_editar_mover_e_remover_vulnerabilidade(painel):
    notebook = next(a for a in painel.ativos() if a.nome == "Notebook Financeiro")
    servidor = next(a for a in painel.ativos() if a.nome == "Servidor Web")
    painel.salvar_vulnerabilidade(notebook.id, {"nome": "SMB v1", "vetor_cvss":
                                                "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"})
    novo = f"{notebook.id}-2"
    assert painel.vulnerabilidade(novo).vul.cvss == 9.8
    painel.salvar_vulnerabilidade(notebook.id, {"nome": "SMB v1", "cvss": 8.1, "progresso": 5}, novo)
    assert painel.vulnerabilidade(novo).vul.risco_residual() == 4.05
    painel.salvar_vulnerabilidade(servidor.id, {"nome": "SMB v1", "cvss": 8.1}, novo)
    assert len(painel.ativo(notebook.id).vulnerabilidades) == 1
    assert len(painel.ativo(servidor.id).vulnerabilidades) == 3
    painel.remover_vulnerabilidade(f"{servidor.id}-3")
    assert len(painel.ativo(servidor.id).vulnerabilidades) == 2


def test_vulnerabilidade_invalida_nao_e_gravada(painel):
    ativo = painel.ativos()[0]
    with pytest.raises(ErroValidacao):
        painel.salvar_vulnerabilidade(ativo.id, {"nome": "X1", "cvss": 11})
    assert len(painel.vulnerabilidades()) == 3


def test_editar_ativo_preserva_vulnerabilidades(painel):
    servidor = next(a for a in painel.ativos() if a.nome == "Servidor Web")
    painel.salvar_ativo({"nome": "Servidor Web", "tipo": "Servidor", "local": "Filial Norte"}, servidor.id)
    assert painel.ativo(servidor.id).local == "Filial Norte"
    assert len(painel.ativo(servidor.id).vulnerabilidades) == 2


def test_observer_e_avisado(painel):
    avisos = []
    painel._eventos.assinar(DADOS_ALTERADOS, lambda **_: avisos.append(1))
    painel.salvar_ativo({"nome": "Roteador Sala", "tipo": "Roteador", "local": "Recepcao"})
    assert avisos == [1]


def test_risco_s3_e_bfs_s4_juntos(painel):
    servidor = next(a for a in painel.ativos() if a.nome == "Servidor Web")
    notebook = next(a for a in painel.ativos() if a.nome == "Notebook Financeiro")
    painel.adicionar_dependencia(servidor.id, notebook.id, 0.5)
    analise = painel.analise_risco()
    x = dict(zip(analise.ids, analise.x))
    assert x[notebook.id] == pytest.approx(4.3 + 0.5 * 15.3)
    impacto = painel.raio_de_impacto(servidor.id)
    assert [(i["ativo"].nome, i["saltos"]) for i in impacto] == [("Servidor Web", 0), ("Notebook Financeiro", 1)]
    painel.remover_ativo(notebook.id)
    assert painel.dependencias() == []
