from bisect import bisect_left


def _identidade(x):
    return x


def busca_linear(itens, alvo, chave=_identidade):
    for indice, item in enumerate(itens):
        if chave(item) == alvo:
            return indice
    return -1


def busca_binaria(itens_ordenados, alvo, chave=_identidade):
    inicio, fim = 0, len(itens_ordenados) - 1
    while inicio <= fim:
        meio = (inicio + fim) // 2
        valor = chave(itens_ordenados[meio])
        if valor == alvo:
            return meio
        if valor < alvo:
            inicio = meio + 1
        else:
            fim = meio - 1
    return -1


def busca_binaria_recursiva(itens_ordenados, alvo, chave=_identidade, inicio=0, fim=None):
    if fim is None:
        fim = len(itens_ordenados) - 1
    if inicio > fim:
        return -1
    meio = (inicio + fim) // 2
    valor = chave(itens_ordenados[meio])
    if valor == alvo:
        return meio
    if valor < alvo:
        return busca_binaria_recursiva(itens_ordenados, alvo, chave, meio + 1, fim)
    return busca_binaria_recursiva(itens_ordenados, alvo, chave, inicio, meio - 1)


def busca_por_prefixo(itens_ordenados, prefixo, chave=_identidade):
    inicio = bisect_left(itens_ordenados, prefixo, key=chave)
    resultado = []
    for item in itens_ordenados[inicio:]:
        if not chave(item).startswith(prefixo):
            break
        resultado.append(item)
    return resultado


def indexar(itens, chave):
    return {chave(item): item for item in itens}
