import json
import sqlite3

import pytest

from dominio.entidades import criar_ativo
from dominio.excecoes import AtivoNaoEncontrado
from persistencia.repositorio import RepositorioJsonLines, RepositorioMemoria, RepositorioSQLite


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


def test_salvar_e_obter_preserva_cvss_e_vetor(repo, ativo):
    repo.salvar(ativo)
    lido = repo.obter(11111)
    assert lido == ativo
    assert [v.cvss for v in lido.vulnerabilidades] == [10.0, 5.3]
    assert lido.vulnerabilidades[0].vetor_cvss.startswith("CVSS:3.1/")


def test_remover(repo, ativo):
    repo.salvar(ativo)
    repo.remover(11111)
    with pytest.raises(AtivoNaoEncontrado):
        repo.obter(11111)


def test_jsonl_le_formato_antigo_com_severidade(tmp_path):
    caminho = tmp_path / "banco.txt"
    antigo = {"id": 33333, "nome": "Roteador 01", "tipo": "Roteador", "local": "Recepcao",
              "vulnerabilidades": [{"nome": "Senha padrao", "severidade": "Alta",
                                    "responsavel": "", "tratamento": "", "progresso": 0}]}
    caminho.write_text(json.dumps(antigo) + "\n", encoding="utf-8")
    vul = RepositorioJsonLines(caminho).obter(33333).vulnerabilidades[0]
    assert vul.cvss == 7.0


def test_jsonl_preserva_linhas_invalidas(tmp_path, ativo):
    caminho = tmp_path / "banco.txt"
    invalida = '{"id": 44444, "nome": "Switch", "tipo": "Outro", "local": "Sala#3", "vulnerabilidades": []}'
    caminho.write_text(invalida + "\n", encoding="utf-8")
    repo = RepositorioJsonLines(caminho)
    repo.salvar(ativo)
    assert invalida in caminho.read_text(encoding="utf-8").splitlines()


def test_sqlite_migra_banco_antigo_sem_colunas_cvss(tmp_path):
    caminho = tmp_path / "antigo.db"
    conexao = sqlite3.connect(caminho)
    conexao.executescript("""
        CREATE TABLE ativos (id INTEGER PRIMARY KEY, nome TEXT NOT NULL, tipo TEXT NOT NULL, local TEXT NOT NULL);
        CREATE TABLE vulnerabilidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ativo_id INTEGER NOT NULL, ordem INTEGER NOT NULL,
            nome TEXT NOT NULL, severidade TEXT NOT NULL, responsavel TEXT NOT NULL DEFAULT '',
            tratamento TEXT NOT NULL DEFAULT '', progresso INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL);
        INSERT INTO ativos VALUES (55555, 'Servidor', 'Servidor', 'DC');
        INSERT INTO vulnerabilidades (ativo_id, ordem, nome, severidade, status) VALUES (55555, 0, 'Antiga', 'Crítica', 'Aberta');
    """)
    conexao.commit()
    conexao.close()
    repo = RepositorioSQLite(caminho)
    assert repo.obter(55555).vulnerabilidades[0].cvss == 9.0
