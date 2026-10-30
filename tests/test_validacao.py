import pytest
from dominio.excecoes import ErroValidacao
from dominio.validacao import validar_progresso, validar_texto, validar_texto_livre


@pytest.mark.parametrize("valor", ["Jo", "Maria da Silva", "D'Avila", "Sao-Paulo", "Ângela Ribeiro"])
def test_textos_validos(valor):
    assert validar_texto("nome", valor) == valor


@pytest.mark.parametrize("valor", ["", "   ", "A", "x" * 61, "Ana2", "a@b", "<b>", "DROP;TABLE"])
def test_textos_invalidos(valor):
    with pytest.raises(ErroValidacao):
        validar_texto("nome", valor)


def test_limites_de_tamanho():
    assert validar_texto("nome", "ab")
    assert validar_texto("nome", "a" * 60)


def test_digitos_quando_permitido():
    assert validar_texto("host", "SRV-01", permitir_digitos=True) == "SRV-01"


def test_campo_opcional_vazio():
    assert validar_texto("responsavel", "  ", obrigatorio=False) == ""


@pytest.mark.parametrize("valor, esperado", [(0, 0), ("10", 10), (" 7 ", 7)])
def test_progresso_valido(valor, esperado):
    assert validar_progresso(valor) == esperado


def test_texto_livre_rejeita_controle():
    with pytest.raises(ErroValidacao):
        validar_texto_livre("tratamento", "abc\x00def")
