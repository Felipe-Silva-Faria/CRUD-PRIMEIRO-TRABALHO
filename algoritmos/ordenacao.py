import random


def _identidade(x):
    return x


def _finalizar(lista, reverso):
    if reverso:
        lista.reverse()
    return lista


def bubble_sort(itens, chave=_identidade, reverso=False):
    lista = list(itens)
    n = len(lista)
    for passada in range(n - 1):
        trocou = False
        for i in range(n - 1 - passada):
            if chave(lista[i + 1]) < chave(lista[i]):
                lista[i], lista[i + 1] = lista[i + 1], lista[i]
                trocou = True
        if not trocou:
            break
    return _finalizar(lista, reverso)


def selection_sort(itens, chave=_identidade, reverso=False):
    lista = list(itens)
    n = len(lista)
    for i in range(n - 1):
        menor = i
        for j in range(i + 1, n):
            if chave(lista[j]) < chave(lista[menor]):
                menor = j
        lista[i], lista[menor] = lista[menor], lista[i]
    return _finalizar(lista, reverso)


def insertion_sort(itens, chave=_identidade, reverso=False):
    lista = list(itens)
    for i in range(1, len(lista)):
        atual = lista[i]
        k = chave(atual)
        j = i - 1
        while j >= 0 and k < chave(lista[j]):
            lista[j + 1] = lista[j]
            j -= 1
        lista[j + 1] = atual
    return _finalizar(lista, reverso)


def merge_sort(itens, chave=_identidade, reverso=False):
    def ordenar(lista):
        if len(lista) <= 1:
            return lista
        meio = len(lista) // 2
        return intercalar(ordenar(lista[:meio]), ordenar(lista[meio:]))

    def intercalar(esquerda, direita):
        resultado = []
        i = j = 0
        while i < len(esquerda) and j < len(direita):
            if chave(direita[j]) < chave(esquerda[i]):
                resultado.append(direita[j])
                j += 1
            else:
                resultado.append(esquerda[i])
                i += 1
        resultado.extend(esquerda[i:])
        resultado.extend(direita[j:])
        return resultado

    return _finalizar(ordenar(list(itens)), reverso)


def quick_sort(itens, chave=_identidade, reverso=False, aleatorio=None):
    sorteio = aleatorio or random.Random(0)

    def ordenar(lista):
        if len(lista) <= 1:
            return lista
        pivo = chave(sorteio.choice(lista))
        menores, iguais, maiores = [], [], []
        for item in lista:
            k = chave(item)
            if k < pivo:
                menores.append(item)
            elif pivo < k:
                maiores.append(item)
            else:
                iguais.append(item)
        return ordenar(menores) + iguais + ordenar(maiores)

    return _finalizar(ordenar(list(itens)), reverso)


def merge_sort_iterativo(itens, chave=_identidade, reverso=False):
    origem = list(itens)
    n = len(origem)
    destino = [None] * n
    largura = 1
    while largura < n:
        for inicio in range(0, n, 2 * largura):
            meio = min(inicio + largura, n)
            fim = min(inicio + 2 * largura, n)
            i, j, k = inicio, meio, inicio
            while i < meio and j < fim:
                if chave(origem[j]) < chave(origem[i]):
                    destino[k] = origem[j]
                    j += 1
                else:
                    destino[k] = origem[i]
                    i += 1
                k += 1
            destino[k:fim] = origem[i:meio] if i < meio else origem[j:fim]
        origem, destino = destino, origem
        largura *= 2
    return _finalizar(origem, reverso)


_LIMITE_INSERCAO = 16


def quick_sort_hoare(itens, chave=_identidade, reverso=False):
    lista = list(itens)
    chaves = [chave(x) for x in lista]

    def trocar(a, b):
        lista[a], lista[b] = lista[b], lista[a]
        chaves[a], chaves[b] = chaves[b], chaves[a]

    def insercao(inicio, fim):
        for i in range(inicio + 1, fim + 1):
            j = i
            while j > inicio and chaves[j] < chaves[j - 1]:
                trocar(j, j - 1)
                j -= 1

    def mediana_de_tres(inicio, fim):
        meio = (inicio + fim) // 2
        if chaves[meio] < chaves[inicio]:
            trocar(meio, inicio)
        if chaves[fim] < chaves[inicio]:
            trocar(fim, inicio)
        if chaves[fim] < chaves[meio]:
            trocar(fim, meio)
        return chaves[meio]

    def particionar(inicio, fim):
        pivo = mediana_de_tres(inicio, fim)
        i, j = inicio - 1, fim + 1
        while True:
            i += 1
            while chaves[i] < pivo:
                i += 1
            j -= 1
            while pivo < chaves[j]:
                j -= 1
            if i >= j:
                return j
            trocar(i, j)

    def ordenar(inicio, fim):
        while fim - inicio >= _LIMITE_INSERCAO:
            corte = particionar(inicio, fim)
            if corte - inicio < fim - corte:
                ordenar(inicio, corte)
                inicio = corte + 1
            else:
                ordenar(corte + 1, fim)
                fim = corte
        insercao(inicio, fim)

    if len(lista) > 1:
        ordenar(0, len(lista) - 1)
    return _finalizar(lista, reverso)


ALGORITMOS = {
    "bolha": bubble_sort,
    "selecao": selection_sort,
    "insercao": insertion_sort,
    "merge": merge_sort,
    "quick": quick_sort,
    "merge_iterativo": merge_sort_iterativo,
    "quick_hoare": quick_sort_hoare,
}


def ordenar(itens, chave=_identidade, reverso=False, algoritmo="merge"):
    try:
        funcao = ALGORITMOS[algoritmo]
    except KeyError:
        raise ValueError(f"Algoritmo desconhecido: {algoritmo}. Opcoes: {sorted(ALGORITMOS)}") from None
    return funcao(itens, chave=chave, reverso=reverso)
