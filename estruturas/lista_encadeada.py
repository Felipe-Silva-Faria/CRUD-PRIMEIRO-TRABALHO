class No:
    __slots__ = ("valor", "proximo")

    def __init__(self, valor, proximo=None):
        self.valor = valor
        self.proximo = proximo

    def __repr__(self):
        return f"No({self.valor!r})"


class ListaEncadeada:
    def __init__(self, itens=()):
        self._cabeca = None
        self._cauda = None
        self._tamanho = 0
        for item in itens:
            self.adicionar_no_fim(item)

    def adicionar_no_inicio(self, valor):
        novo = No(valor, self._cabeca)
        self._cabeca = novo
        if self._cauda is None:
            self._cauda = novo
        self._tamanho += 1

    def adicionar_no_fim(self, valor):
        novo = No(valor)
        if self._cauda is None:
            self._cabeca = self._cauda = novo
        else:
            self._cauda.proximo = novo
            self._cauda = novo
        self._tamanho += 1

    def remover_do_inicio(self):
        if self._cabeca is None:
            raise IndexError("remover de lista vazia")
        removido = self._cabeca
        self._cabeca = removido.proximo
        if self._cabeca is None:
            self._cauda = None
        self._tamanho -= 1
        return removido.valor

    def remover_primeiro(self, predicado):
        anterior, atual = None, self._cabeca
        while atual is not None:
            if predicado(atual.valor):
                if anterior is None:
                    self._cabeca = atual.proximo
                else:
                    anterior.proximo = atual.proximo
                if atual is self._cauda:
                    self._cauda = anterior
                self._tamanho -= 1
                return atual.valor
            anterior, atual = atual, atual.proximo
        return None

    def buscar(self, predicado):
        for valor in self:
            if predicado(valor):
                return valor
        return None

    def primeiro(self):
        if self._cabeca is None:
            raise IndexError("lista vazia")
        return self._cabeca.valor

    def __getitem__(self, indice):
        if indice < 0:
            indice += self._tamanho
        if not 0 <= indice < self._tamanho:
            raise IndexError("indice fora da lista")
        atual = self._cabeca
        for _ in range(indice):
            atual = atual.proximo
        return atual.valor

    def inverter(self):
        anterior, atual = None, self._cabeca
        self._cauda = self._cabeca
        while atual is not None:
            proximo = atual.proximo
            atual.proximo = anterior
            anterior, atual = atual, proximo
        self._cabeca = anterior

    def para_lista(self):
        return list(self)

    def __iter__(self):
        atual = self._cabeca
        while atual is not None:
            yield atual.valor
            atual = atual.proximo

    def __len__(self):
        return self._tamanho

    def __bool__(self):
        return self._tamanho > 0

    def __contains__(self, valor):
        return any(v == valor for v in self)

    def __repr__(self):
        return "ListaEncadeada([" + " -> ".join(repr(v) for v in self) + "])"
