import random
import time
from algoritmos.busca import busca_binaria, busca_linear, indexar
from algoritmos.ordenacao import ALGORITMOS
from estruturas.arvore_bst import ArvoreBinariaBusca
from estruturas.tabela_hash import TabelaHash


class Contavel:
    comparacoes = 0
    __slots__ = ("valor",)

    def __init__(self, valor):
        self.valor = valor

    def __lt__(self, outro):
        Contavel.comparacoes += 1
        return self.valor < outro.valor

    def __eq__(self, outro):
        return self.valor == outro.valor


def gerar_ids(n, semente=42):
    return random.Random(semente).sample(range(10000, 99999), n)


def cronometrar(funcao, repeticoes=5):
    melhor = float("inf")
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        funcao()
        melhor = min(melhor, time.perf_counter() - inicio)
    return melhor * 1000


def comparar_buscas(tamanhos=(1_000, 10_000, 50_000)):
    print("\n=== BUSCA de 200 ids (tempo total em ms) ===")
    print(f"{'n':>8} | {'linear O(n)':>12} | {'binaria O(log n)':>16} | {'dict O(1)':>10}")
    for n in tamanhos:
        ids = gerar_ids(n)
        ordenados = sorted(ids)
        indice = indexar(ids, chave=lambda x: x)
        alvos = random.Random(1).sample(ids, 200)
        t_lin = cronometrar(lambda ids=ids, alvos=alvos: [busca_linear(ids, a) for a in alvos], 3)
        t_bin = cronometrar(lambda ordenados=ordenados, alvos=alvos: [busca_binaria(ordenados, a) for a in alvos], 3)
        t_dic = cronometrar(lambda indice=indice, alvos=alvos: [a in indice for a in alvos], 3)
        print(f"{n:>8} | {t_lin:>12.2f} | {t_bin:>16.3f} | {t_dic:>10.3f}")


def comparar_ordenacoes(tamanhos=(100, 500, 1_000, 2_000)):
    print("\n=== ORDENACAO: numero de comparacoes ===")
    nomes = list(ALGORITMOS)
    print(f"{'n':>6} | " + " | ".join(f"{nome:>10}" for nome in nomes))
    for n in tamanhos:
        dados = [Contavel(x) for x in gerar_ids(n)]
        linha = []
        for nome in nomes:
            Contavel.comparacoes = 0
            ALGORITMOS[nome](dados)
            linha.append(f"{Contavel.comparacoes:>10}")
        print(f"{n:>6} | " + " | ".join(linha))
    print("Repare: dobrar n ~quadruplica bolha/selecao/insercao (n^2),"
          " mas so ~dobra merge/quick (n log n).")


def comparar_melhor_pior_caso(n=1_000):
    print(f"\n=== INSERCAO com n={n}: o formato da entrada importa ===")
    casos = {
        "ja ordenada (melhor)": list(range(n)),
        "aleatoria (medio)": gerar_ids(n),
        "invertida (pior)": list(range(n, 0, -1)),
    }
    for nome, dados in casos.items():
        Contavel.comparacoes = 0
        ALGORITMOS["insercao"]([Contavel(x) for x in dados])
        print(f"{nome:<22} {Contavel.comparacoes:>8} comparacoes")


def comparar_geracao_id(n=20_000):
    print(f"\n=== Verificar 'id ja usado' com {n} ativos cadastrados ===")
    ids = gerar_ids(n)
    como_lista, como_set = list(ids), set(ids)
    testes = random.Random(7).sample(range(10000, 99999), 500)
    t_lista = cronometrar(lambda: [t in como_lista for t in testes], 3)
    t_set = cronometrar(lambda: [t in como_set for t in testes], 3)
    print(f"lista (codigo antigo): {t_lista:8.2f} ms   set (codigo novo): {t_set:8.3f} ms")


def comparar_estruturas_s4(tamanhos=(1_000, 4_000, 16_000)):
    print("\n=== S4: 500 buscas (ms) e altura da arvore ===")
    print(f"{'n':>7} | {'TabelaHash':>10} | {'dict':>8} | {'altura BST bal.':>15} | {'altura degenerada':>17}")
    for n in tamanhos:
        ids = gerar_ids(n)
        tabela = TabelaHash()
        for i in ids:
            tabela[i] = i
        como_dict = dict.fromkeys(ids)
        alvos = random.Random(3).sample(ids, 500)
        t_hash = cronometrar(lambda tabela=tabela, alvos=alvos: [tabela[a] for a in alvos], 3)
        t_dict = cronometrar(lambda como_dict=como_dict, alvos=alvos: [como_dict[a] for a in alvos], 3)
        balanceada = ArvoreBinariaBusca.construir_balanceada([(i, i) for i in sorted(ids)])
        print(f"{n:>7} | {t_hash:>10.3f} | {t_dict:>8.3f} | {balanceada.altura():>15} | {n:>17}")
    print("Repare: a hash fica ~constante quando n cresce (O(1)); a altura balanceada cresce"
          " como log2(n), enquanto a degenerada cresce igual a n.")


if __name__ == "__main__":
    comparar_buscas()
    comparar_ordenacoes()
    comparar_melhor_pior_caso()
    comparar_geracao_id()
    comparar_estruturas_s4()
