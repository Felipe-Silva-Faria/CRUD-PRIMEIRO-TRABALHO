from collections import deque


class GrafoDirecionado:
    def __init__(self):
        self._adjacencia = {}
        self._pesos = {}

    @classmethod
    def de_dependencias(cls, ids, dependencias):
        grafo = cls()
        for ativo_id in ids:
            grafo.adicionar_vertice(ativo_id)
        validos = set(ids)
        for dep in dependencias:
            if dep["origem"] in validos and dep["destino"] in validos:
                grafo.adicionar_aresta(dep["origem"], dep["destino"], dep.get("peso", 1.0))
        return grafo

    def adicionar_vertice(self, v):
        self._adjacencia.setdefault(v, [])

    def adicionar_aresta(self, origem, destino, peso=1.0):
        self.adicionar_vertice(origem)
        self.adicionar_vertice(destino)
        if destino not in self._adjacencia[origem]:
            self._adjacencia[origem].append(destino)
        self._pesos[(origem, destino)] = peso

    def vizinhos(self, v):
        return list(self._adjacencia.get(v, []))

    def peso(self, origem, destino):
        return self._pesos.get((origem, destino))

    @property
    def vertices(self):
        return list(self._adjacencia)

    def arestas(self):
        return [(o, d) for o, ds in self._adjacencia.items() for d in ds]

    def bfs(self, origem):
        if origem not in self._adjacencia:
            return {}
        distancia = {origem: 0}
        fila = deque([origem])
        while fila:
            atual = fila.popleft()
            for viz in self._adjacencia[atual]:
                if viz not in distancia:
                    distancia[viz] = distancia[atual] + 1
                    fila.append(viz)
        return distancia

    def caminho_mais_curto(self, origem, destino):
        if origem not in self._adjacencia or destino not in self._adjacencia:
            return []
        pai = {origem: None}
        fila = deque([origem])
        while fila:
            atual = fila.popleft()
            if atual == destino:
                break
            for viz in self._adjacencia[atual]:
                if viz not in pai:
                    pai[viz] = atual
                    fila.append(viz)
        if destino not in pai:
            return []
        caminho, v = [], destino
        while v is not None:
            caminho.append(v)
            v = pai[v]
        return caminho[::-1]

    def dfs(self, origem):
        if origem not in self._adjacencia:
            return []
        visitados, ordem, pilha = set(), [], [origem]
        while pilha:
            atual = pilha.pop()
            if atual in visitados:
                continue
            visitados.add(atual)
            ordem.append(atual)
            for viz in reversed(self._adjacencia[atual]):
                if viz not in visitados:
                    pilha.append(viz)
        return ordem

    def encontrar_ciclo(self):
        branco, cinza, preto = 0, 1, 2
        cor = dict.fromkeys(self._adjacencia, branco)
        pai = {}
        for inicio in self._adjacencia:
            if cor[inicio] != branco:
                continue
            pilha = [(inicio, iter(self._adjacencia[inicio]))]
            cor[inicio] = cinza
            while pilha:
                v, filhos = pilha[-1]
                proximo = next(filhos, None)
                if proximo is None:
                    cor[v] = preto
                    pilha.pop()
                elif cor[proximo] == cinza:
                    ciclo, x = [proximo], v
                    while x != proximo:
                        ciclo.append(x)
                        x = pai[x]
                    ciclo.append(proximo)
                    return ciclo[::-1]
                elif cor[proximo] == branco:
                    pai[proximo] = v
                    cor[proximo] = cinza
                    pilha.append((proximo, iter(self._adjacencia[proximo])))
        return []
