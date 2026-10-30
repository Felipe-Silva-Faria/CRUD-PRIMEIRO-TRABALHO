import json

import pytest

from dominio.excecoes import ErroValidacao
from persistencia.usuarios import RepositorioUsuariosJSON, RepositorioUsuariosMemoria
from servicos.autenticacao import ContaBloqueada, ErroAutenticacao, ServicoAutenticacao


class Relogio:
    agora = 0.0

    def __call__(self):
        return self.agora


@pytest.fixture
def relogio():
    return Relogio()


@pytest.fixture
def auth(relogio):
    return ServicoAutenticacao(RepositorioUsuariosMemoria(), iteracoes=1000, max_tentativas=3, relogio=relogio)


def test_primeiro_acesso_e_login(auth):
    assert auth.primeiro_acesso()
    auth.criar_usuario("admin", "frase-longa-123")
    assert auth.autenticar("ADMIN", "frase-longa-123").nome == "admin"


@pytest.mark.parametrize(("nome", "senha"), [("ad", "frase-longa-123"), ("admin", "curta")])
def test_politica(auth, nome, senha):
    with pytest.raises(ErroValidacao):
        auth.criar_usuario(nome, senha)


def test_mensagem_generica_e_bloqueio(auth, relogio):
    auth.criar_usuario("admin", "frase-longa-123")
    with pytest.raises(ErroAutenticacao, match="Usuário ou senha inválidos"):
        auth.autenticar("nao_existe", "x")
    for _ in range(3):
        with pytest.raises(ErroAutenticacao):
            auth.autenticar("admin", "errada")
    with pytest.raises(ContaBloqueada):
        auth.autenticar("admin", "frase-longa-123")
    relogio.agora = 61
    assert auth.autenticar("admin", "frase-longa-123")


def test_json_nao_guarda_a_senha(tmp_path):
    caminho = tmp_path / "usuarios.json"
    ServicoAutenticacao(RepositorioUsuariosJSON(caminho), iteracoes=1000).criar_usuario("admin", "frase-longa-123")
    conteudo = caminho.read_text(encoding="utf-8")
    assert "frase-longa-123" not in conteudo and json.loads(conteudo)[0]["nome"] == "admin"
    assert RepositorioUsuariosJSON(caminho).quantidade() == 1
