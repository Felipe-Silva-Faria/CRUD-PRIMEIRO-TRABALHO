import functools
import logging
import time
from functools import reduce

from dominio.enums import Severidade, TipoAtivo, normalizar_chave

logger = logging.getLogger(__name__)


def compor(*funcoes):
    def identidade(x):
        return x
    return reduce(lambda f, g: lambda x: f(g(x)), funcoes, identidade)


def todos(*predicados):
    return lambda item: all(p(item) for p in predicados)


def algum(*predicados):
    return lambda item: any(p(item) for p in predicados)


def negar(predicado):
    return lambda item: not predicado(item)


def por_tipo(tipo):
    alvo = TipoAtivo.de_valor(tipo)
    return lambda ativo: ativo.tipo == alvo


def por_texto(texto):
    chave = normalizar_chave(texto)
    return lambda ativo: chave in normalizar_chave(ativo.nome) or chave in normalizar_chave(ativo.local)


def por_severidade_minima(severidade):
    minima = Severidade.de_valor(severidade)
    return lambda ativo: (ativo.pior_severidade() or 0) >= minima


def com_vulnerabilidades_abertas():
    return lambda ativo: any(v.aberta for v in ativo.vulnerabilidades)


def filtrar(itens, predicado):
    return list(filter(predicado, itens))


def mapear(itens, funcao):
    return list(map(funcao, itens))


def agrupar_por(itens, chave):
    grupos = {}
    for item in itens:
        grupos.setdefault(chave(item), []).append(item)
    return grupos


def somar(itens, funcao):
    return reduce(lambda acumulado, item: acumulado + funcao(item), itens, 0)


def cronometrar(funcao):
    @functools.wraps(funcao)
    def embrulho(*args, **kwargs):
        inicio = time.perf_counter()
        try:
            return funcao(*args, **kwargs)
        finally:
            gasto = (time.perf_counter() - inicio) * 1000
            logger.debug("%s levou %.2f ms", funcao.__name__, gasto)
    return embrulho


def tentar_novamente(tentativas=3, espera=0.2, excecoes=(Exception,), dormir=time.sleep):
    if tentativas < 1:
        raise ValueError("tentativas deve ser >= 1")

    def decorador(funcao):
        nome = getattr(funcao, "__name__", repr(funcao))

        @functools.wraps(funcao)
        def embrulho(*args, **kwargs):
            atraso = espera
            for numero in range(1, tentativas + 1):
                try:
                    return funcao(*args, **kwargs)
                except excecoes as erro:
                    if numero == tentativas:
                        raise
                    logger.warning("%s falhou (%s). Tentativa %d/%d", nome, erro, numero, tentativas)
                    dormir(atraso)
                    atraso *= 2
        return embrulho
    return decorador


def achatar(estrutura):
    if not isinstance(estrutura, (list, tuple)):
        return [estrutura]
    resultado = []
    for item in estrutura:
        resultado.extend(achatar(item))
    return resultado


def contar_vulnerabilidades(ativos, indice=0):
    if indice >= len(ativos):
        return 0
    return len(ativos[indice].vulnerabilidades) + contar_vulnerabilidades(ativos, indice + 1)


def risco_recursivo(ativos):
    if not ativos:
        return 0.0
    if len(ativos) == 1:
        return ativos[0].risco_total()
    meio = len(ativos) // 2
    return round(risco_recursivo(ativos[:meio]) + risco_recursivo(ativos[meio:]), 2)
