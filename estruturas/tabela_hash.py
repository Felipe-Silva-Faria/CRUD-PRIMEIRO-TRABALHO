import re
from dominio.enums import normalizar_chave


class TabelaHash:
    _CAPACIDADE_INICIAL = 8
    _FATOR_CARGA_MAX = 0.75

    def __init__(self):
        self._baldes = [[] for _ in range(self._CAPACIDADE_INICIAL)]
        self._tamanho = 0

    def _indice(self, chave):
        return hash(chave) % len(self._baldes)

    def _redimensionar(self):
        antigos = self._baldes
        self._baldes = [[] for _ in range(len(antigos) * 2)]
        for balde in antigos:
            for chave, valor in balde:
                self._baldes[self._indice(chave)].append((chave, valor))

    def __setitem__(self, chave, valor):
        balde = self._baldes[self._indice(chave)]
        for i, (k, _) in enumerate(balde):
            if k == chave:
                balde[i] = (chave, valor)
                return
        balde.append((chave, valor))
        self._tamanho += 1
        if self._tamanho / len(self._baldes) > self._FATOR_CARGA_MAX:
            self._redimensionar()

    def __getitem__(self, chave):
        for k, v in self._baldes[self._indice(chave)]:
            if k == chave:
                return v
        raise KeyError(chave)

    def __delitem__(self, chave):
        balde = self._baldes[self._indice(chave)]
        for i, (k, _) in enumerate(balde):
            if k == chave:
                del balde[i]
                self._tamanho -= 1
                return
        raise KeyError(chave)

    def get(self, chave, padrao=None):
        try:
            return self[chave]
        except KeyError:
            return padrao

    def __contains__(self, chave):
        return any(k == chave for k, _ in self._baldes[self._indice(chave)])

    def __len__(self):
        return self._tamanho

    def itens(self):
        return [(k, v) for balde in self._baldes for k, v in balde]

    @property
    def fator_carga(self):
        return self._tamanho / len(self._baldes)

    @property
    def maior_balde(self):
        return max(len(b) for b in self._baldes)


_RE_PALAVRA = re.compile(r"[\w\-]+")


def _tokens(texto):
    return {t.lower() for t in _RE_PALAVRA.findall(normalizar_chave(texto or "").replace("_", " "))}


class IndiceTexto:
    TAMANHO_MIN_PREFIXO = 2

    def __init__(self):
        self._indice = TabelaHash()
        self._termos_por_id = {}

    def _prefixos(self, palavra):
        return {palavra[:i] for i in range(self.TAMANHO_MIN_PREFIXO, len(palavra) + 1)}

    def indexar(self, ident, texto):
        self.remover(ident)
        termos = set()
        for palavra in _tokens(texto):
            termos |= self._prefixos(palavra) or {palavra}
        for termo in termos:
            conjunto = self._indice.get(termo)
            if conjunto is None:
                conjunto = set()
                self._indice[termo] = conjunto
            conjunto.add(ident)
        self._termos_por_id[ident] = termos

    def remover(self, ident):
        for termo in self._termos_por_id.pop(ident, ()):
            conjunto = self._indice.get(termo)
            if conjunto is not None:
                conjunto.discard(ident)

    def buscar(self, consulta):
        palavras = _tokens(consulta)
        if not palavras:
            return None
        resultado = None
        for palavra in palavras:
            ids = self._indice.get(palavra, set())
            resultado = set(ids) if resultado is None else resultado & ids
            if not resultado:
                return set()
        return resultado
