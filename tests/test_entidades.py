import pytest

from dominio.entidades import Ativo, AtivoGenerico, BancoDeDados, Servidor, Vulnerabilidade, criar_ativo
from dominio.enums import Severidade, StatusTratamento, TipoAtivo
from dominio.excecoes import ErroValidacao


class TestEnums:
    @pytest.mark.parametrize("entrada, esperado", [
        ("Servidor", TipoAtivo.SERVIDOR), ("banco de dados", TipoAtivo.BANCO_DE_DADOS),
        (2, TipoAtivo.SERVIDOR), ("geladeira", TipoAtivo.OUTRO), (777, TipoAtivo.OUTRO)])
    def test_tipo_de_valor(self, entrada, esperado):
        assert TipoAtivo.de_valor(entrada) is esperado

    @pytest.mark.parametrize("nota, esperado", [
        (0.0, Severidade.NENHUMA), (3.9, Severidade.BAIXA), (6.9, Severidade.MEDIA),
        (7.0, Severidade.ALTA), (9.8, Severidade.CRITICA)])
    def test_severidade_derivada_do_cvss(self, nota, esperado):
        assert Severidade.de_cvss(nota) is esperado


class TestVulnerabilidade:
    def test_cvss_por_nota(self):
        vul = Vulnerabilidade("SMB v1 ativo", "8.1", progresso="3")
        assert vul.cvss == 8.1 and vul.vetor_cvss == ""
        assert vul.severidade is Severidade.ALTA
        assert vul.status is StatusTratamento.EM_TRATAMENTO

    def test_cvss_por_vetor(self):
        vul = Vulnerabilidade("Log4Shell", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H")
        assert vul.cvss == 10.0
        assert vul.vetor_cvss.startswith("CVSS:3.1/")
        assert vul.severidade is Severidade.CRITICA

    def test_alterar_vetor_recalcula_nota(self):
        vul = Vulnerabilidade("Falha", 2.0)
        vul.vetor_cvss = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H"
        assert vul.cvss == 7.5

    def test_alterar_nota_apaga_vetor_antigo(self):
        vul = Vulnerabilidade("Falha", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H")
        vul.cvss = 3.0
        assert vul.vetor_cvss == ""

    @pytest.mark.parametrize("cvss", [-1, 10.5, "alta", None, ""])
    def test_cvss_invalido(self, cvss):
        with pytest.raises(ErroValidacao):
            Vulnerabilidade("Falha", cvss)

    def test_risco_residual_usa_cvss(self):
        assert Vulnerabilidade("X1", 9.8, progresso=0).risco_residual() == 9.8
        assert Vulnerabilidade("X1", 9.8, progresso=5).risco_residual() == 4.9
        assert Vulnerabilidade("X1", 9.8, progresso=10).risco_residual() == 0

    def test_dict_antigo_sem_cvss_e_aceito(self):
        vul = Vulnerabilidade.from_dict({"nome": "Senha padrao", "severidade": "Alta", "progresso": 0})
        assert vul.cvss == 7.0 and vul.severidade is Severidade.ALTA

    def test_dict_sem_nenhuma_severidade_e_recusado(self):
        with pytest.raises(ErroValidacao):
            Vulnerabilidade.from_dict({"nome": "Sem nota"})

    def test_roundtrip_dict(self):
        original = Vulnerabilidade("Senha fraca", "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N", "Joao", "Trocar", 2)
        copia = Vulnerabilidade.from_dict(original.to_dict())
        assert copia == original and copia.cvss == 4.3

    def test_to_dict_expoe_cvss(self):
        dados = Vulnerabilidade("XSS", 6.1).to_dict()
        assert dados["cvss"] == 6.1 and dados["severidade"] == "Média" and "vetor_cvss" in dados


class TestAtivo:
    def test_classe_abstrata_nao_instancia(self):
        with pytest.raises(TypeError):
            Ativo("Algo", "Lugar")

    def test_fabrica_escolhe_subclasse(self, dados_servidor):
        assert isinstance(criar_ativo(dados_servidor), Servidor)
        assert isinstance(criar_ativo({**dados_servidor, "tipo": "Banco de Dados"}), BancoDeDados)
        assert isinstance(criar_ativo({**dados_servidor, "tipo": "Switch"}), AtivoGenerico)

    def test_risco_proprio_e_soma_dos_cvss(self, dados_servidor):
        assert criar_ativo(dados_servidor).risco_proprio() == 15.3

    def test_risco_total_com_progresso_e_fator(self, dados_servidor):
        assert criar_ativo(dados_servidor).risco_total() == round((10.0 + 5.3 * 0.5) * 1.5, 2)

    def test_maior_cvss_ignora_corrigidas(self, dados_notebook):
        ativo = criar_ativo({**dados_notebook, "vulnerabilidades": [
            {"nome": "Corrigida", "cvss": 9.8, "progresso": 10}, {"nome": "Aberta", "cvss": 4.3}]})
        assert ativo.maior_cvss() == 4.3
        assert ativo.pior_severidade() is Severidade.MEDIA

    def test_sem_vulnerabilidades(self, dados_notebook):
        ativo = criar_ativo(dados_notebook)
        assert ativo.maior_cvss() is None and ativo.pior_severidade() is None

    def test_tipo_desconhecido_preserva_texto(self, dados_notebook):
        assert criar_ativo({**dados_notebook, "tipo": "Switch"}).to_dict()["tipo"] == "Switch"
