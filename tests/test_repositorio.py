import json

import pytest

from dominio.entidades import criar_ativo
from dominio.excecoes import AtivoNaoEncontrado
from persistencia.repositorio import (RepositorioJsonLines, RepositorioMemoria,
                                      RepositorioSQLite)


@pytest.fixture(params=["memoria", "jsonl", "sqlite"])
def repo(request, tmp_path):
    if request.param == "memoria":
        return RepositorioMemoria()
    if request.param == "jsonl":
        return RepositorioJsonLines(tmp_path / "banco.txt")
    return RepositorioSQLite(tmp_path / "banco.db")


@pytest.fixture
def ativo(dados_servidor):
    return criar_ativo({**dados_servidor, "id": 11111})


def test_salvar_e_obter(repo, ativo):
    repo.salvar(ativo)
    assert repo.obter(11111) == ativo


def test_listar_preserva_ordem(repo, ativo, dados_notebook):
    outro = criar_ativo({**dados_notebook, "id": 22222})
    repo.salvar(ativo)
    repo.salvar(outro)
    assert [a.id for a in repo.listar()] == [11111, 22222]
    assert repo.ids() == {11111, 22222}


def test_salvar_de_novo_atualiza(repo, ativo):
    repo.salvar(ativo)
    ativo.nome = "Servidor Novo"
    ativo.remover_vulnerabilidade(0)
    repo.salvar(ativo)
    lido = repo.obter(11111)
    assert lido.nome == "Servidor Novo" and len(lido.vulnerabilidades) == 1
    assert len(repo.listar()) == 1


def test_remover(repo, ativo):
    repo.salvar(ativo)
    repo.remover(11111)
    assert not repo.existe(11111)
    with pytest.raises(AtivoNaoEncontrado):
        repo.remover(11111)


def test_obter_inexistente(repo):
    with pytest.raises(AtivoNaoEncontrado):
        repo.obter(99999)


def test_jsonl_persiste_entre_instancias(tmp_path, ativo):
    caminho = tmp_path / "banco.txt"
    RepositorioJsonLines(caminho).salvar(ativo)
    assert RepositorioJsonLines(caminho).obter(11111) == ativo


def test_jsonl_le_formato_antigo_e_ignora_linha_corrompida(tmp_path, caplog):
    caminho = tmp_path / "banco.txt"
    antigo = {"id": 33333, "nome": "Roteador 01", "tipo": "Roteador", "local": "Recepcao",
              "vulnerabilidades": [{"nome": "Senha padrao", "severidade": "Alta",
                                    "responsavel": "", "tratamento": "", "progresso": 0}]}
    caminho.write_text(json.dumps(antigo) + "\n{linha quebrada\n\n", encoding="utf-8")
    repo = RepositorioJsonLines(caminho)
    assert repo.ids() == {33333}
    assert "ignorada" in caplog.text


def test_jsonl_nao_deixa_temporarios(tmp_path, ativo):
    RepositorioJsonLines(tmp_path / "banco.txt").salvar(ativo)
    assert [p.name for p in tmp_path.iterdir()] == ["banco.txt"]


def test_sqlite_cascade_remove_vulnerabilidades(tmp_path, ativo):
    repo = RepositorioSQLite(tmp_path / "banco.db")
    repo.salvar(ativo)
    repo.remover(ativo.id)
    restantes = repo._conexao.execute("SELECT COUNT(*) FROM vulnerabilidades").fetchone()[0]
    assert restantes == 0


def test_sqlite_resiste_a_sql_injection(tmp_path, ativo):
    repo = RepositorioSQLite(tmp_path / "banco.db")
    repo.salvar(ativo)
    with pytest.raises(AtivoNaoEncontrado):
        repo.obter("1 OR 1=1")
    assert repo.ids() == {11111}


def test_jsonl_preserva_linhas_invalidas_ao_regravar(tmp_path, ativo):
    caminho = tmp_path / "banco.txt"
    invalida = '{"id": 44444, "nome": "Switch", "tipo": "Outro", "local": "Sala#3", "vulnerabilidades": []}'
    caminho.write_text(invalida + "\n", encoding="utf-8")
    repo = RepositorioJsonLines(caminho)
    repo.salvar(ativo)
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    assert invalida in linhas
    assert len(linhas) == 2
