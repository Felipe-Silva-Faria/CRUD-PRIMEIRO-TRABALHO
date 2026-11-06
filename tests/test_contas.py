import json

import pytest

from dominio.excecoes import ErroValidacao
from dominio.permissoes import Autorizacao, Funcao, autorizacoes_efetivas
from persistencia.usuarios import APROVADA, RECUSADA, RepositorioUsuariosJSON, RepositorioUsuariosMemoria
from servicos.autenticacao import ErroAutenticacao, ServicoAutenticacao
from servicos.contas import ErroPermissao, ServicoContas
from servicos.painel_protegido import PainelProtegido

SENHA = "frase-longa-123"


@pytest.fixture
def contas():
    repo = RepositorioUsuariosMemoria()
    auth = ServicoAutenticacao(repo, iteracoes=1000)
    auth.criar_usuario("admin", SENHA)
    return ServicoContas(repo, auth)


def _cadastrar(contas, nome="ana.souza", funcao="ativos", email=None):
    pedido = contas.solicitar_cadastro(nome, SENHA, "Ana Souza", email or f"{nome}@empresa.com", funcao)
    return contas.aprovar_cadastro("admin", pedido.id)


def test_funcoes_sao_conjuntos_de_autorizacoes():
    assert autorizacoes_efetivas(["ativos"]) == {Autorizacao.VER_ATIVOS, Autorizacao.CRIAR_ATIVO,
                                                 Autorizacao.EDITAR_ATIVO, Autorizacao.EXCLUIR_ATIVO}
    assert Autorizacao.EDITAR_VULNERABILIDADE in autorizacoes_efetivas(["vulnerabilidades"])
    assert autorizacoes_efetivas(["administrador"]) == set(Autorizacao)
    assert not Funcao.ADMINISTRADOR.solicitavel
    assert not Autorizacao.EDITAR_USUARIO.solicitavel and Autorizacao.VER_RISCOS.solicitavel


def test_cada_acao_tem_codigo_unico():
    codigos = [a.codigo for a in Autorizacao]
    assert len(codigos) == len(set(codigos))


def test_fluxo_de_cadastro(contas):
    pedido = contas.solicitar_cadastro("ana.souza", SENHA, "Ana Souza", "Ana@Empresa.com", "vulnerabilidades",
                                       "Analista do SOC")
    assert pedido.email == "ana@empresa.com" and SENHA not in json.dumps(pedido.to_dict())
    assert [p.usuario for p in contas.cadastros_pendentes()] == ["ana.souza"]
    usuario = contas.aprovar_cadastro("admin", pedido.id)
    assert usuario.funcoes == ["vulnerabilidades"] and contas.cadastros_pendentes() == []
    assert contas._auth.autenticar("ana.souza", SENHA).nome == "ana.souza"


@pytest.mark.parametrize("campos", [
    {"funcao": "administrador"}, {"email": "sem-arroba"}, {"usuario": "a"}, {"senha": "curta"},
    {"nome_completo": "<script>"},
])
def test_cadastro_invalido(contas, campos):
    dados = {"usuario": "ana.souza", "senha": SENHA, "nome_completo": "Ana Souza",
             "email": "ana@empresa.com", "funcao": "ativos", **campos}
    with pytest.raises(ErroValidacao):
        contas.solicitar_cadastro(**dados)


def test_nome_e_email_nao_repetem(contas):
    contas.solicitar_cadastro("ana.souza", SENHA, "Ana Souza", "ana@empresa.com", "ativos")
    with pytest.raises(ErroValidacao):
        contas.solicitar_cadastro("ana.souza", SENHA, "Ana Lima", "outra@empresa.com", "ativos")
    with pytest.raises(ErroValidacao):
        contas.solicitar_cadastro("ana.lima", SENHA, "Ana Lima", "ana@empresa.com", "ativos")
    with pytest.raises(ErroValidacao):
        contas.solicitar_cadastro("admin", SENHA, "Outro Admin", "x@empresa.com", "ativos")


def test_recusar_cadastro_apaga_o_hash(contas):
    pedido = contas.solicitar_cadastro("ana.souza", SENHA, "Ana Souza", "ana@empresa.com", "ativos")
    contas.recusar_cadastro("admin", pedido.id, "Sem vínculo com a empresa")
    registro = contas.cadastro(pedido.id)
    assert (registro.status, registro.hash_senha, registro.decidida_por) == (RECUSADA, "", "admin")
    with pytest.raises(ErroAutenticacao):
        contas._auth.autenticar("ana.souza", SENHA)


def test_usuario_comum_nao_aprova_cadastro(contas):
    _cadastrar(contas)
    pedido = contas.solicitar_cadastro("bruno", SENHA, "Bruno Lima", "bruno@empresa.com", "ativos")
    with pytest.raises(ErroPermissao):
        contas.aprovar_cadastro("ana.souza", pedido.id)


def test_pedido_de_autorizacao_com_senha(contas):
    _cadastrar(contas)
    codigos = {a.codigo for a in contas.solicitaveis_para("ana.souza")}
    assert "ativo.criar" not in codigos
    assert "usuario.editar" not in codigos
    assert "vulnerabilidade.ver" in codigos
    with pytest.raises(ErroAutenticacao):
        contas.solicitar_autorizacoes("ana.souza", "senha-errada", ["vulnerabilidade.ver"])
    pedido = contas.solicitar_autorizacoes("ana.souza", SENHA, ["vulnerabilidade.ver"], "Triagem")
    assert "vulnerabilidade.ver" not in {a.codigo for a in contas.solicitaveis_para("ana.souza")}
    contas.aprovar_autorizacao("admin", pedido.id)
    assert contas.pode("ana.souza", Autorizacao.VER_VULNERABILIDADES)
    assert contas.pedido(pedido.id).status == APROVADA


def test_nao_pode_pedir_administracao(contas):
    _cadastrar(contas)
    with pytest.raises(ErroValidacao):
        contas.solicitar_autorizacoes("ana.souza", SENHA, ["usuario.editar"])


def test_ninguem_aprova_o_proprio_pedido(contas):
    _cadastrar(contas)
    contas.definir_acessos("admin", "ana.souza", ["ativos"], ["autorizacao.aprovar", "risco.ver"])
    pedido = contas.solicitar_autorizacoes("ana.souza", SENHA, ["relatorio.ver"])
    with pytest.raises(ErroValidacao, match="próprio"):
        contas.aprovar_autorizacao("ana.souza", pedido.id)


def test_nao_concede_o_que_nao_possui(contas):
    _cadastrar(contas)
    _cadastrar(contas, "bruno", "vulnerabilidades")
    contas.definir_acessos("admin", "ana.souza", ["ativos"], ["autorizacao.aprovar"])
    pedido = contas.solicitar_autorizacoes("bruno", SENHA, ["relatorio.ver"])
    with pytest.raises(ErroValidacao, match="não possui"):
        contas.aprovar_autorizacao("ana.souza", pedido.id)


def test_so_admin_atribui_administrador(contas):
    _cadastrar(contas)
    contas.definir_acessos("admin", "ana.souza", ["ativos"], ["usuario.editar"])
    _cadastrar(contas, "bruno")
    with pytest.raises(ErroValidacao, match="administrador"):
        contas.definir_acessos("ana.souza", "bruno", ["administrador"], [])
    contas.definir_acessos("admin", "bruno", ["administrador"], [])
    assert contas.usuario("bruno").administrador


def test_sempre_sobra_um_admin(contas):
    with pytest.raises(ErroValidacao):
        contas.definir_acessos("admin", "admin", ["ativos"], [])
    with pytest.raises(ErroValidacao):
        contas.definir_ativo("admin", "admin", False)


def test_conta_desativada_nao_entra_e_perde_acessos(contas):
    _cadastrar(contas)
    contas.definir_ativo("admin", "ana.souza", False)
    assert not contas.pode("ana.souza", Autorizacao.VER_ATIVOS)
    with pytest.raises(ErroAutenticacao, match="desativada"):
        contas._auth.autenticar("ana.souza", SENHA)


def test_criar_usuario_exige_autorizacao(contas):
    _cadastrar(contas)
    with pytest.raises(ErroPermissao):
        contas.criar_usuario("ana.souza", "carlos", SENHA, "Carlos Dias", "carlos@empresa.com", ["ativos"])
    novo = contas.criar_usuario("admin", "carlos", SENHA, "Carlos Dias", "carlos@empresa.com", ["ativos"])
    assert novo.funcoes == ["ativos"]


def test_json_v2_e_migracao_da_v1(tmp_path):
    caminho = tmp_path / "usuarios.json"
    caminho.write_text(json.dumps([{"nome": "admin", "hash_senha": "x", "sal": "00", "iteracoes": 1,
                                    "papel": "admin"}]), encoding="utf-8")
    repo = RepositorioUsuariosJSON(caminho)
    assert repo.obter("admin").funcoes == ["administrador"]
    repo.salvar(repo.obter("admin"))
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    assert conteudo["versao"] == 2 and conteudo["usuarios"][0]["funcoes"] == ["administrador"]


class PainelFalso:
    algoritmo = "merge"

    def __init__(self):
        self.chamadas = []

    def salvar_ativo(self, dados, ativo_id=None):
        self.chamadas.append(("salvar_ativo", ativo_id))
        return 1

    def remover_vulnerabilidade(self, id_registro):
        self.chamadas.append(("remover_vulnerabilidade", id_registro))

    def ativos(self):
        return ["lidos sem restricao"]


def test_proxy_bloqueia_escrita_sem_autorizacao(contas):
    _cadastrar(contas)
    real = PainelFalso()
    painel = PainelProtegido(real, contas, lambda: "ana.souza")
    painel.salvar_ativo({"nome": "x"})
    painel.salvar_ativo({"nome": "x"}, 10)
    with pytest.raises(ErroPermissao):
        painel.remover_vulnerabilidade("10-1")
    assert real.chamadas == [("salvar_ativo", None), ("salvar_ativo", 10)]
    assert painel.ativos() == ["lidos sem restricao"]
    painel.algoritmo = "quick"
    assert real.algoritmo == "quick"
