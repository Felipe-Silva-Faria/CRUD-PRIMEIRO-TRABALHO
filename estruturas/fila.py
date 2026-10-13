from dominio.excecoes import FilaVaziaError
from estruturas.lista_encadeada import ListaEncadeada


class Fila:
    def __init__(self, itens=()):
        self._dados = ListaEncadeada()
        for item in itens:
            self.enfileirar(item)

    def enfileirar(self, item):
        self._dados.adicionar_no_fim(item)

    def desenfileirar(self):
        if self.esta_vazia():
            raise FilaVaziaError("fila vazia")
        return self._dados.remover_do_inicio()

    def espiar(self):
        if self.esta_vazia():
            raise FilaVaziaError("fila vazia")
        return self._dados.primeiro()

    def esta_vazia(self):
        return len(self._dados) == 0

    def __len__(self):
        return len(self._dados)

    def __iter__(self):
        return iter(self._dados)

    def __repr__(self):
        return f"{type(self).__name__}({list(self)!r})"


class FilaLimitada(Fila):
    def __init__(self, capacidade, itens=()):
        if capacidade < 1:
            raise ValueError("capacidade deve ser >= 1")
        self.capacidade = capacidade
        super().__init__(itens)

    def enfileirar(self, item):
        if len(self) >= self.capacidade:
            self.desenfileirar()
        super().enfileirar(item)
