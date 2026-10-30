import math
import re
from dataclasses import dataclass

from dominio.excecoes import ErroValidacao

VERSOES_SUPORTADAS = ("3.0", "3.1")

PESOS = {
    "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
    "AC": {"L": 0.77, "H": 0.44},
    "PR": {"N": 0.85, "L": 0.62, "H": 0.27},
    "UI": {"N": 0.85, "R": 0.62},
    "S": {"U": "U", "C": "C"},
    "C": {"H": 0.56, "L": 0.22, "N": 0.0},
    "I": {"H": 0.56, "L": 0.22, "N": 0.0},
    "A": {"H": 0.56, "L": 0.22, "N": 0.0},
}

PR_ESCOPO_ALTERADO = {"N": 0.85, "L": 0.68, "H": 0.5}

ORDEM_METRICAS = ("AV", "AC", "PR", "UI", "S", "C", "I", "A")

NOMES_METRICAS = {
    "AV": "Vetor de ataque",
    "AC": "Complexidade do ataque",
    "PR": "Privilegios necessarios",
    "UI": "Interacao do usuario",
    "S": "Escopo",
    "C": "Confidencialidade",
    "I": "Integridade",
    "A": "Disponibilidade",
}

FAIXAS = (
    (0.0, 0.0, "Nenhuma"),
    (0.1, 3.9, "Baixa"),
    (4.0, 6.9, "Média"),
    (7.0, 8.9, "Alta"),
    (9.0, 10.0, "Crítica"),
)

NOTA_MINIMA_DA_FAIXA = {"BAIXA": 0.1, "MEDIA": 4.0, "ALTA": 7.0, "CRITICA": 9.0}

_PADRAO_NOTA = re.compile(r"^\d{1,2}([.,]\d)?$")


@dataclass(frozen=True)
class ResultadoCVSS:
    nota: float
    vetor: str
    impacto: float
    explorabilidade: float

    @property
    def faixa(self):
        return faixa_qualitativa(self.nota)


def arredondar_para_cima(valor):
    inteiro = round(valor * 100000)
    if inteiro % 10000 == 0:
        return inteiro / 100000.0
    return (math.floor(inteiro / 10000) + 1) / 10.0


def validar_nota(nota):
    if isinstance(nota, bool):
        raise ErroValidacao("cvss", "a nota deve ser um numero entre 0.0 e 10.0")
    try:
        valor = float(str(nota).strip().replace(",", "."))
    except (TypeError, ValueError):
        raise ErroValidacao("cvss", "a nota deve ser um numero entre 0.0 e 10.0") from None
    if math.isnan(valor) or not 0.0 <= valor <= 10.0:
        raise ErroValidacao("cvss", "a nota deve estar entre 0.0 e 10.0")
    if not math.isclose(round(valor, 1), valor, abs_tol=1e-9):
        raise ErroValidacao("cvss", "a nota CVSS tem apenas uma casa decimal")
    return round(valor, 1)


def faixa_qualitativa(nota):
    nota = validar_nota(nota)
    for minimo, maximo, rotulo in FAIXAS:
        if minimo <= nota <= maximo:
            return rotulo
    raise ErroValidacao("cvss", f"nota fora das faixas: {nota}")


def interpretar_vetor(vetor):
    if not isinstance(vetor, str) or not vetor.strip():
        raise ErroValidacao("vetor_cvss", "vetor vazio")
    partes = vetor.strip().upper().split("/")
    cabecalho = partes[0]
    if not cabecalho.startswith("CVSS:"):
        raise ErroValidacao("vetor_cvss", "o vetor deve comecar com CVSS:3.1/ ou CVSS:3.0/")
    versao = cabecalho[5:]
    if versao not in VERSOES_SUPORTADAS:
        raise ErroValidacao("vetor_cvss", f"versao CVSS {versao!r} nao suportada (use 3.0 ou 3.1)")
    metricas = {}
    for parte in partes[1:]:
        if ":" not in parte:
            raise ErroValidacao("vetor_cvss", f"trecho invalido: {parte!r}")
        chave, valor = parte.split(":", 1)
        if chave not in PESOS:
            raise ErroValidacao("vetor_cvss", f"metrica desconhecida: {chave!r}")
        if chave in metricas:
            raise ErroValidacao("vetor_cvss", f"metrica repetida: {chave!r}")
        if valor not in PESOS[chave]:
            opcoes = "/".join(PESOS[chave])
            raise ErroValidacao("vetor_cvss", f"valor invalido para {chave}: {valor!r} (use {opcoes})")
        metricas[chave] = valor
    faltando = [m for m in ORDEM_METRICAS if m not in metricas]
    if faltando:
        raise ErroValidacao("vetor_cvss", f"metricas obrigatorias ausentes: {', '.join(faltando)}")
    return versao, metricas


def montar_vetor(metricas, versao="3.1"):
    if versao not in VERSOES_SUPORTADAS:
        raise ErroValidacao("vetor_cvss", f"versao CVSS {versao!r} nao suportada")
    faltando = [m for m in ORDEM_METRICAS if m not in metricas]
    if faltando:
        raise ErroValidacao("vetor_cvss", f"metricas obrigatorias ausentes: {', '.join(faltando)}")
    vetor = f"CVSS:{versao}/" + "/".join(f"{m}:{metricas[m]}" for m in ORDEM_METRICAS)
    interpretar_vetor(vetor)
    return vetor


def _arredondar(valor, versao):
    if versao == "3.0":
        return math.ceil(round(valor * 10, 10)) / 10
    return arredondar_para_cima(valor)


def calcular_cvss(vetor):
    versao, m = interpretar_vetor(vetor)
    escopo_alterado = m["S"] == "C"

    iss = 1 - (1 - PESOS["C"][m["C"]]) * (1 - PESOS["I"][m["I"]]) * (1 - PESOS["A"][m["A"]])

    if escopo_alterado:
        impacto = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
        privilegios = PR_ESCOPO_ALTERADO[m["PR"]]
    else:
        impacto = 6.42 * iss
        privilegios = PESOS["PR"][m["PR"]]

    explorabilidade = 8.22 * PESOS["AV"][m["AV"]] * PESOS["AC"][m["AC"]] * privilegios * PESOS["UI"][m["UI"]]

    if impacto <= 0:
        nota = 0.0
    elif escopo_alterado:
        nota = _arredondar(min(1.08 * (impacto + explorabilidade), 10), versao)
    else:
        nota = _arredondar(min(impacto + explorabilidade, 10), versao)

    return ResultadoCVSS(
        nota=nota,
        vetor=montar_vetor(m, versao),
        impacto=round(max(impacto, 0.0), 1),
        explorabilidade=round(explorabilidade, 1),
    )


def interpretar_entrada(texto):
    if isinstance(texto, (int, float)) and not isinstance(texto, bool):
        return validar_nota(texto), ""
    if texto is None or not str(texto).strip():
        raise ErroValidacao("cvss", "informe a nota (ex.: 9.8) ou o vetor (ex.: CVSS:3.1/AV:N/...)")
    texto = str(texto).strip()
    if texto.upper().startswith("CVSS:"):
        resultado = calcular_cvss(texto)
        return resultado.nota, resultado.vetor
    if _PADRAO_NOTA.match(texto):
        return validar_nota(texto), ""
    raise ErroValidacao("cvss", "use uma nota de 0.0 a 10.0 ou um vetor CVSS:3.1/...")


def nota_de_rotulo_legado(rotulo):
    from dominio.enums import normalizar_chave
    chave = normalizar_chave(rotulo)
    if chave not in NOTA_MINIMA_DA_FAIXA:
        raise ErroValidacao("cvss", f"severidade antiga invalida: {rotulo!r}")
    return NOTA_MINIMA_DA_FAIXA[chave]


def nota_de_dict(vulnerabilidade):
    vetor = vulnerabilidade.get("vetor_cvss") or ""
    if vetor:
        return calcular_cvss(vetor).nota
    if vulnerabilidade.get("cvss") is not None:
        return validar_nota(vulnerabilidade["cvss"])
    return nota_de_rotulo_legado(vulnerabilidade.get("severidade", ""))


def formatar(nota, com_faixa=True):
    nota = validar_nota(nota)
    texto = f"{nota:.1f}"
    return f"{texto} ({faixa_qualitativa(nota)})" if com_faixa else texto


def descrever_vetor(vetor):
    _versao, metricas = interpretar_vetor(vetor)
    return {NOMES_METRICAS[m]: metricas[m] for m in ORDEM_METRICAS}
