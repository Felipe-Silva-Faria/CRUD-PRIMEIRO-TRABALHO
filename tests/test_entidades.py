import pytest

from dominio.entidades import (Ativo, AtivoGenerico, BancoDeDados, Servidor,
                               Vulnerabilidade, criar_ativo)
from dominio.enums import Severidade, StatusTratamento, TipoAtivo
from dominio.excecoes import ErroValidacao


class TestEnums:
    @pytest.mark.parametrize("entrada, esperado", [
        ("Servidor", TipoAtivo.SERVIDOR),
        ("banco de dados", TipoAtivo.BANCO_DE_DADOS),
        ("Aplicação Web", TipoAtivo.APLICACAO_WEB),
        (2, TipoAtivo.SERVIDOR),
        ("1", TipoAtivo.NOTEBOOK),
        ("geladeira", TipoAtivo.OUTRO),
        (777, TipoAtivo.OUTRO),
    ])
    def test_tipo_de_valor(self, entrada, esperado):
        assert TipoAtivo.de_valor(entrada) is esperado

    @pytest.mark.parametrize("entrada", ["Crítica", "critica", " CRITICA ", 4])
    def test_severidade_tolerante_a_formato(self, entrada):
        assert Severidade.de_valor(entrada) is Severidade.CRITICA

    def test_severidade_invalida(self):
        with pytest.raises(ValueError):
            Severidade.de_valor("gravissima")

    def test_severidades_sao_comparaveis(self):
        assert Severidade.BAIXA < Severidade.MEDIA < Severidade.ALTA < Severidade.CRITICA

    @pytest.mark.parametrize("progresso, status", [
        (0, StatusTratamento.ABERTA), (5, StatusTratamento.EM_TRATAMENTO), (10, StatusTratamento.CORRIGIDA)])
    def test_status_derivado_do_progresso(self, progresso, status):
        assert StatusTratamento.a_partir_do_progresso(progresso) is status


class TestVulnerabilidade:
    def test_criacao_valida(self):
        vul = Vulnerabilidade("SMB v1 ativo", "alta", progresso="3")
        assert vul.severidade is Severidade.ALTA
        assert vul.progresso == 3
        assert vul.status is StatusTratamento.EM_TRATAMENTO

    @pytest.mark.parametrize("progresso", [-1, 11, "abc", None, True])
    def test_progresso_invalido(self, progresso):
        with pytest.raises(ErroValidacao) as erro:
            Vulnerabilidade("Falha", "Baixa", progresso=progresso)
        assert erro.value.campo == "progresso"

    def test_risco_residual_cai_com_o_progresso(self):
        assert Vulnerabilidade("X1", "Crítica", progresso=0).risco_residual() == 4
        assert Vulnerabilidade("X1", "Crítica", progresso=5).risco_residual() == 2
        assert Vulnerabilidade("X1", "Crítica", progresso=10).risco_residual() == 0

    def test_risco_aceito_nao_conta(self):
        vul = Vulnerabilidade.from_dict({"nome": "Porta 8080", "severidade": "Alta", "status": "Risco aceito"})
        assert vul.status is StatusTratamento.RISCO_ACEITO
        assert vul.risco_residual() == 0

    def test_roundtrip_dict(self):
        original = Vulnerabilidade("Senha fraca", "Média", "Joao", "Trocar senha", 2)
        assert Vulnerabilidade.from_dict(original.to_dict()) == original


class TestAtivoPolimorfismo:
    def test_classe_abstrata_nao_instancia(self):
        with pytest.raises(TypeError):
            Ativo("Algo", "Lugar")

    def test_fabrica_escolhe_subclasse(self, dados_servidor):
        assert isinstance(criar_ativo(dados_servidor), Servidor)
        assert isinstance(criar_ativo({**dados_servidor, "tipo": "Banco de Dados"}), BancoDeDados)
        assert isinstance(criar_ativo({**dados_servidor, "tipo": "???"}), AtivoGenerico)

    def test_mesmo_metodo_resultados_diferentes(self, dados_servidor):
        servidor = criar_ativo(dados_servidor)
        generico = criar_ativo({**dados_servidor, "tipo": "Outro"})
        assert servidor.risco_total() > generico.risco_total()
        assert servidor.recomendacao() != generico.recomendacao()

    def test_to_dict_compativel_com_formato_antigo(self, dados_servidor):
        dados = criar_ativo({**dados_servidor, "id": 12345}).to_dict()
        assert set(dados) == {"id", "nome", "tipo", "local", "vulnerabilidades"}
        assert dados["tipo"] == "Servidor"

    def test_hostname_com_digitos_e_aceito(self, dados_servidor):
        assert criar_ativo({**dados_servidor, "nome": "SRV-01"}).nome == "SRV-01"

    @pytest.mark.parametrize("campo, valor", [
        ("nome", ""), ("nome", "SRV@01"), ("nome", "<script>"),
        ("local", "   "), ("local", "A"), ("local", "Sala@2")])
    def test_validacao_de_campos(self, dados_servidor, campo, valor):
        with pytest.raises(ErroValidacao):
            criar_ativo({**dados_servidor, campo: valor})

    def test_espacos_sao_normalizados(self, dados_notebook):
        ativo = criar_ativo({**dados_notebook, "nome": "  Notebook    RH  "})
        assert ativo.nome == "Notebook RH"

    def test_lista_de_vulnerabilidades_e_protegida(self, dados_servidor):
        ativo = criar_ativo(dados_servidor)
        ativo.vulnerabilidades.clear()
        assert len(ativo.vulnerabilidades) == 2

    def test_pior_severidade(self, dados_servidor, dados_notebook):
        assert criar_ativo(dados_servidor).pior_severidade() is Severidade.CRITICA
        assert criar_ativo(dados_notebook).pior_severidade() is None


def test_tipo_desconhecido_preserva_texto_original(dados_notebook):
    ativo = criar_ativo({**dados_notebook, "tipo": "Switch"})
    assert isinstance(ativo, AtivoGenerico)
    assert ativo.to_dict()["tipo"] == "Switch"


def test_local_aceita_numero(dados_notebook):
    assert criar_ativo({**dados_notebook, "local": "Sala 2"}).local == "Sala 2"
