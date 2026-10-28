class No:
    __slots__ = ("chave", "direita", "esquerda", "valor")

    def __init__(self, chave, valor):
        self.chave = chave
        self.valor = valor
        self.esquerda = None
        self.direita = None


class ArvoreBinariaBusca:
    def __init__(self):
        self._raiz = None
        self._tamanho = 0

    @classmethod
    def construir_balanceada(cls, pares_ordenados):
        arvore = cls()

        def montar(inicio, fim):
            if inicio > fim:
                return None
            meio = (inicio + fim) // 2
            no = No(*pares_ordenados[meio])
            no.esquerda = montar(inicio, meio - 1)
            no.direita = montar(meio + 1, fim)
            return no

        arvore._raiz = montar(0, len(pares_ordenados) - 1)
        arvore._tamanho = len(pares_ordenados)
        return arvore

    def inserir(self, chave, valor=None):
        if self._raiz is None:
            self._raiz = No(chave, valor)
            self._tamanho = 1
            return
        atual = self._raiz
        while True:
            if chave == atual.chave:
                atual.valor = valor
                return
            lado = "esquerda" if chave < atual.chave else "direita"
            proximo = getattr(atual, lado)
            if proximo is None:
                setattr(atual, lado, No(chave, valor))
                self._tamanho += 1
                return
            atual = proximo

    def buscar(self, chave):
        atual = self._raiz
        while atual is not None:
            if chave == atual.chave:
                return atual.valor
            atual = atual.esquerda if chave < atual.chave else atual.direita
        raise KeyError(chave)

    def __contains__(self, chave):
        try:
            self.buscar(chave)
            return True
        except KeyError:
            return False

    def remover(self, chave):
        def _remover(no, chave):
            if no is None:
                raise KeyError(chave)
            if chave < no.chave:
                no.esquerda = _remover(no.esquerda, chave)
            elif chave > no.chave:
                no.direita = _remover(no.direita, chave)
            else:
                if no.esquerda is None:
                    return no.direita
                if no.direita is None:
                    return no.esquerda
                sucessor = no.direita
                while sucessor.esquerda is not None:
                    sucessor = sucessor.esquerda
                no.chave, no.valor = sucessor.chave, sucessor.valor
                no.direita = _remover(no.direita, sucessor.chave)
            return no

        self._raiz = _remover(self._raiz, chave)
        self._tamanho -= 1

    def em_ordem(self, reverso=False):
        primeiro, segundo = ("direita", "esquerda") if reverso else ("esquerda", "direita")
        pilha, atual = [], self._raiz
        while pilha or atual is not None:
            while atual is not None:
                pilha.append(atual)
                atual = getattr(atual, primeiro)
            atual = pilha.pop()
            yield atual.chave, atual.valor
            atual = getattr(atual, segundo)

    def intervalo(self, minimo, maximo):
        resultado = []

        def visitar(no):
            if no is None:
                return
            if minimo < no.chave:
                visitar(no.esquerda)
            if minimo <= no.chave <= maximo:
                resultado.append((no.chave, no.valor))
            if no.chave < maximo:
                visitar(no.direita)

        visitar(self._raiz)
        return resultado

    def altura(self):
        altura, nivel = 0, [self._raiz] if self._raiz else []
        while nivel:
            altura += 1
            nivel = [f for no in nivel for f in (no.esquerda, no.direita) if f is not None]
        return altura

    def __len__(self):
        return self._tamanho
