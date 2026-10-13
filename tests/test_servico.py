import pytest

from dominio.excecoes import AtivoNaoEncontrado, ErroValidacao
from servicos.servico_ativos import ID_MAXIMO, ID_MINIMO
from utilitarios.funcional import por_tipo


def test_cadastrar_gera_id_valido(servico, dados_servidor):
    ativo = servico.cadastrar(dados_servidor)
    assert ID_MINIMO <= ativo.id <= ID_MAXIMO
    assert servico.obter(ativo.id) is ativo


def test_cliente_nao_escolhe_id(servico, dados_servidor):
    ativo = servico.cadastrar({**dados_servidor, "id": 1})
    assert ativo.id != 1


def test_ids_unicos(servico, dados_notebook):
    ids = {servico.cadastrar(dados_notebook).id for _ in range(300)}
    assert len(ids) == 300


def test_cadastro_invalido_nao_salva(servico, dados_servidor):
    with pytest.raises(ErroValidacao):
        servico.cadastrar({**dados_servidor, "nome": ""})
    assert servico.listar() == []


def test_atualizar_e_remover(servico, dados_servidor):
    ativo = servico.cadastrar(dados_servidor)
    servico.atualizar(ativo.id, {**dados_servidor, "local": "Filial Norte"})
    assert servico.obter(ativo.id).local == "Filial Norte"
    servico.remover(ativo.id)
    with pytest.raises(AtivoNaoEncontrado):
        servico.obter(ativo.id)


def test_atualizar_inexistente(servico, dados_servidor):
    with pytest.raises(AtivoNaoEncontrado):
        servico.atualizar(12345, dados_servidor)


def test_vulnerabilidade_sub_recurso(servico, dados_notebook):
    ativo = servico.cadastrar(dados_notebook)
    servico.adicionar_vulnerabilidade(ativo.id, {"nome": "Disco sem BitLocker", "severidade": "Alta"})
    assert len(servico.obter(ativo.id).vulnerabilidades) == 1
    servico.remover_vulnerabilidade(ativo.id, 0)
    assert servico.obter(ativo.id).vulnerabilidades == []


def test_listar_filtrado_e_ordenado(servico, dados_servidor, dados_notebook):
    servico.cadastrar(dados_servidor)
    servico.cadastrar(dados_notebook)
    assert [a.nome for a in servico.listar([por_tipo("Notebook")])] == ["Notebook Financeiro"]
    assert [a.nome for a in servico.listar(ordenar_por="nome")] == ["Notebook Financeiro", "Servidor Web"]
    assert servico.relatorio_risco(1)[0].nome == "Servidor Web"


def test_ordenar_por_campo_invalido(servico):
    with pytest.raises(ErroValidacao):
        servico.listar(ordenar_por="senha")


def test_buscar_por_prefixo(servico, dados_servidor, dados_notebook):
    servico.cadastrar(dados_servidor)
    servico.cadastrar(dados_notebook)
    assert [a.nome for a in servico.buscar_por_prefixo("serv")] == ["Servidor Web"]


def test_historico_de_auditoria(servico, dados_notebook):
    ativo = servico.cadastrar(dados_notebook)
    servico.remover(ativo.id)
    assert [e["acao"] for e in servico.historico] == ["CADASTRO", "REMOCAO"]
