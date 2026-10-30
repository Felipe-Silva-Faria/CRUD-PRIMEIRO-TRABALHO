from dataclasses import dataclass
import numpy as np
from algoritmos.cvss import nota_de_dict
from dominio.excecoes import ErroValidacao

TOLERANCIA_DETERMINANTE = 1e-12
LIMITE_CONDICAO = 1e8
TOLERANCIA_RESIDUO = 1e-9


@dataclass(frozen=True)
class ResultadoRisco:
    ids: tuple
    nomes: tuple
    vulnerabilidades: tuple
    M: np.ndarray
    v: np.ndarray
    b: np.ndarray
    A: np.ndarray
    x: np.ndarray
    determinante: float
    condicao: float
    residuo: float
    raio_espectral: float

    def ranking(self):
        ordem = np.argsort(-self.x, kind="stable")
        return [(self.ids[i], self.nomes[i], round(float(self.b[i]), 2), round(float(self.x[i]), 2)) for i in ordem]


def _chave_vulnerabilidade(vul):
    vetor = vul.get("vetor_cvss") or ""
    return (str(vul.get("nome", "")).strip().upper(), vetor or str(nota_de_dict(vul)))


def montar_M_v(ativos):
    colunas = {}
    notas = []
    for ativo in ativos:
        for vul in ativo.get("vulnerabilidades", []):
            chave = _chave_vulnerabilidade(vul)
            if chave not in colunas:
                colunas[chave] = len(notas)
                notas.append(nota_de_dict(vul))
    M = np.zeros((len(ativos), len(notas)))
    for i, ativo in enumerate(ativos):
        for vul in ativo.get("vulnerabilidades", []):
            M[i, colunas[_chave_vulnerabilidade(vul)]] = 1.0
    nomes_vul = tuple(chave[0] for chave in sorted(colunas, key=colunas.get))
    return M, np.array(notas, dtype=float), nomes_vul


def risco_proprio(M, v):
    if M.shape[1] != v.shape[0]:
        raise ErroValidacao("matriz", f"M tem {M.shape[1]} colunas, mas v tem {v.shape[0]} notas")
    return M @ v


def montar_A(ids, dependencias):
    indice = {ativo_id: i for i, ativo_id in enumerate(ids)}
    A = np.zeros((len(ids), len(ids)))
    for dep in dependencias:
        origem, destino, peso = dep["origem"], dep["destino"], float(dep["peso"])
        if origem not in indice or destino not in indice:
            continue
        if origem == destino:
            raise ErroValidacao("dependencia", f"o ativo {origem} nao pode depender de si mesmo")
        if not 0.0 < peso < 1.0:
            raise ErroValidacao("dependencia", f"o peso deve estar entre 0 e 1 (exclusivo), recebido {peso}")
        A[indice[destino], indice[origem]] = peso
    return A


def verificar_invertibilidade(I_menos_A):
    n = I_menos_A.shape[0]
    if n == 0:
        return 1.0, 1.0
    determinante = float(np.linalg.det(I_menos_A))
    escala = float(np.prod(np.linalg.norm(I_menos_A, axis=1))) or 1.0
    if abs(determinante) <= TOLERANCIA_DETERMINANTE * escala:
        raise ErroValidacao("dependencia", "det(I - A) = 0: o sistema nao tem solucao unica (revise os ciclos e pesos)")
    condicao = float(np.linalg.cond(I_menos_A))
    if not np.isfinite(condicao) or condicao > LIMITE_CONDICAO:
        raise ErroValidacao("dependencia", f"I - A e mal condicionada (k = {condicao:.3g}): o resultado nao e confiavel")
    return determinante, condicao


def propagar(b, A):
    n = len(b)
    I_menos_A = np.eye(n) - A
    determinante, condicao = verificar_invertibilidade(I_menos_A)
    x = np.linalg.solve(I_menos_A, b) if n else np.zeros(0)
    residuo = float(np.linalg.norm(I_menos_A @ x - b)) if n else 0.0
    if residuo > TOLERANCIA_RESIDUO * max(1.0, float(np.linalg.norm(b))):
        raise ErroValidacao("dependencia", f"residuo alto ({residuo:.3g}): solucao numericamente instavel")
    return x, determinante, condicao, residuo


def somas_parciais(b, A, saltos):
    termo = b.copy()
    total = b.copy()
    resultado = [total.copy()]
    for _ in range(saltos):
        termo = A @ termo
        total = total + termo
        resultado.append(total.copy())
    return resultado


def analisar(ativos, dependencias=()):
    ids = tuple(a["id"] for a in ativos)
    if len(set(ids)) != len(ids):
        raise ErroValidacao("ativos", "ids repetidos")
    M, v, nomes_vul = montar_M_v(ativos)
    b = risco_proprio(M, v)
    A = montar_A(ids, dependencias)
    x, determinante, condicao, residuo = propagar(b, A)
    raio = float(max(abs(np.linalg.eigvals(A)))) if len(ids) else 0.0
    return ResultadoRisco(
        ids=ids,
        nomes=tuple(a.get("nome", "") for a in ativos),
        vulnerabilidades=nomes_vul,
        M=M, v=v, b=b, A=A, x=x,
        determinante=determinante,
        condicao=condicao,
        residuo=residuo,
        raio_espectral=raio,
    )
