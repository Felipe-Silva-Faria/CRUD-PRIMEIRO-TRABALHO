import logging
import time
from dataclasses import dataclass

from algoritmos import risco
from algoritmos.ordenacao import ALGORITMOS, ordenar
from dominio.entidades import Vulnerabilidade, criar_ativo
from dominio.excecoes import AtivoNaoEncontrado, ErroCRUD, ErroValidacao
from estruturas.arvore_bst import ArvoreBinariaBusca
from estruturas.grafo import GrafoDirecionado
from estruturas.tabela_hash import IndiceTexto, TabelaHash
from persistencia import dependencias as deps
from persistencia.relatorios_sql import RelatorioSQL
from servicos.eventos import DADOS_ALTERADOS
from servicos.servico_ativos import CHAVES_ORDENACAO

logger = logging.getLogger(__name__)


class FonteLocal:
    online = True

    def __init__(self, servico_ativos):
        self._servico = servico_ativos

    def listar(self):
        return [a.to_dict() for a in self._servico.listar()]

    def cadastrar(self, dados):
        return self._servico.cadastrar(dados).to_dict()

    def atualizar(self, ativo_id, dados):
        return self._servico.atualizar(ativo_id, dados).to_dict()

    def remover(self, ativo_id):
        self._servico.remover(ativo_id)
        return True


@dataclass(frozen=True)
class RegistroVulnerabilidade:
    ativo: object
    indice: int
    vul: Vulnerabilidade

    @property
    def id(self):
        return f"{self.ativo.id}-{self.indice + 1}"

    @property
    def aberta(self):
        return self.vul.progresso < 10

    @property
    def severidade(self):
        return self.vul.to_dict()["severidade"]

    @property
    def status(self):
        return self.vul.to_dict()["status"]


def separar_id(id_registro):
    ativo_id, numero = str(id_registro).rsplit("-", 1)
    return int(ativo_id), int(numero) - 1


CHAVES_VULNERABILIDADE = {
    "id": lambda r: (r.ativo.id, r.indice),
    "nome": lambda r: r.vul.nome.lower(),
    "cvss": lambda r: r.vul.cvss,
    "ativo": lambda r: r.ativo.nome.lower(),
    "progresso": lambda r: r.vul.progresso,
    "risco": lambda r: r.vul.risco_residual(),
    "status": lambda r: r.status,
}


class PainelVulnerabilidades:
    def __init__(self, fonte, eventos, arquivo_dependencias=deps.ARQUIVO_DEPENDENCIAS,
                 algoritmo="merge"):
        self._fonte = fonte
        self._eventos = eventos
        self._arquivo_deps = arquivo_dependencias
        self.algoritmo = algoritmo
        self.ultima_ordenacao_ms = 0.0
        self._ativos = {}
        self.recarregar()

    def recarregar(self):
        self._ativos = {}
        for dados in self._fonte.listar():
            try:
                ativo = criar_ativo(dados)
            except ErroCRUD as erro:
                logger.warning("ativo ignorado na interface: %s (%s)", dados.get("id"), erro)
                continue
            self._ativos[ativo.id] = ativo
        self._indexar()

    def _indexar(self):
        self._registros = [
            RegistroVulnerabilidade(a, i, v)
            for a in self._ativos.values() for i, v in enumerate(a.vulnerabilidades)
        ]
        self._por_id = TabelaHash()
        self._indice = IndiceTexto()
        for r in self._registros:
            self._por_id[r.id] = r
            self._indice.indexar(r.id, " ".join([
                r.id, r.vul.nome, r.ativo.nome, r.ativo.local, r.vul.responsavel, r.severidade]))
        pares = sorted(((r.vul.cvss, r.id), r) for r in self._registros)
        self._arvore = ArvoreBinariaBusca.construir_balanceada(pares)

    def _alterou(self):
        self.recarregar()
        self._eventos.publicar(DADOS_ALTERADOS)

    @property
    def online(self):
        return getattr(self._fonte, "online", True)

    @property
    def pendentes(self):
        return len(getattr(self._fonte, "pendentes", ()))

    def ativos(self, ordenar_por="nome", reverso=False):
        return self._ordenar(list(self._ativos.values()), CHAVES_ORDENACAO[ordenar_por], reverso)

    def ativo(self, ativo_id):
        try:
            return self._ativos[int(ativo_id)]
        except (KeyError, ValueError):
            raise AtivoNaoEncontrado(ativo_id) from None

    def salvar_ativo(self, dados, ativo_id=None):
        corpo = {"nome": dados.get("nome", ""), "tipo": dados.get("tipo", ""),
                 "local": dados.get("local", ""), "vulnerabilidades": []}
        if ativo_id is not None:
            corpo["vulnerabilidades"] = [v.to_dict() for v in self.ativo(ativo_id).vulnerabilidades]
        criar_ativo({**corpo, "id": ativo_id or 0})
        if ativo_id is None:
            resultado = self._fonte.cadastrar(corpo)
        else:
            resultado = self._fonte.atualizar(int(ativo_id), corpo)
        self._alterou()
        return resultado.get("id", ativo_id)

    def remover_ativo(self, ativo_id):
        ativo_id = int(ativo_id)
        self.ativo(ativo_id)
        self._fonte.remover(ativo_id)
        deps.remover_do_ativo(ativo_id, self._arquivo_deps)
        self._alterou()

    def vulnerabilidade(self, id_registro):
        registro = self._por_id.get(str(id_registro))
        if registro is None:
            raise ErroValidacao("vulnerabilidade", f"{id_registro} nao encontrada")
        return registro

    def vulnerabilidades(self, texto="", severidade=None, cvss_min=None, somente_abertas=False,
                         ordenar_por="cvss", reverso=True, ativo_id=None):
        if cvss_min:
            candidatos = [r for _, r in self._arvore.intervalo((cvss_min, ""), (10.1, ""))]
        else:
            candidatos = [r for _, r in self._arvore.em_ordem()]
        ids = self._indice.buscar(texto)
        if ids is not None:
            candidatos = [r for r in candidatos if r.id in ids]
        if severidade:
            candidatos = [r for r in candidatos if r.severidade == severidade]
        if somente_abertas:
            candidatos = [r for r in candidatos if r.aberta]
        if ativo_id is not None:
            candidatos = [r for r in candidatos if r.ativo.id == int(ativo_id)]
        chave = CHAVES_VULNERABILIDADE.get(ordenar_por, CHAVES_VULNERABILIDADE["cvss"])
        return self._ordenar(candidatos, chave, reverso)

    def mais_criticas(self, quantidade=5):
        resultado = []
        for _, r in self._arvore.em_ordem(reverso=True):
            if r.aberta:
                resultado.append(r)
                if len(resultado) == quantidade:
                    break
        return resultado

    def salvar_vulnerabilidade(self, ativo_id, dados_vul, id_registro=None):
        Vulnerabilidade.from_dict(dados_vul)
        destino = self.ativo(ativo_id)
        if id_registro is not None:
            origem_id, indice = separar_id(id_registro)
            if origem_id != destino.id:
                self._regravar(origem_id, remover=indice)
                id_registro = None
            else:
                self._regravar(destino.id, substituir=(indice, dados_vul))
        if id_registro is None:
            self._regravar(destino.id, acrescentar=dados_vul)
        self._alterou()

    def remover_vulnerabilidade(self, id_registro):
        ativo_id, indice = separar_id(id_registro)
        self._regravar(ativo_id, remover=indice)
        self._alterou()

    def _regravar(self, ativo_id, acrescentar=None, substituir=None, remover=None):
        ativo = self.ativo(ativo_id)
        lista = [v.to_dict() for v in ativo.vulnerabilidades]
        if remover is not None:
            lista.pop(remover)
        if substituir is not None:
            lista[substituir[0]] = substituir[1]
        if acrescentar is not None:
            lista.append(acrescentar)
        dados = {**ativo.to_dict(), "vulnerabilidades": lista}
        dados.pop("id", None)
        self._fonte.atualizar(ativo.id, dados)

    def _ordenar(self, itens, chave, reverso):
        inicio = time.perf_counter()
        resultado = ordenar(itens, chave=chave, reverso=reverso, algoritmo=self.algoritmo)
        self.ultima_ordenacao_ms = (time.perf_counter() - inicio) * 1000
        return resultado

    @staticmethod
    def algoritmos_disponiveis():
        return list(ALGORITMOS)

    def relatorio(self):
        return RelatorioSQL(self._ativos.values())

    def dependencias(self):
        return deps.ler(self._arquivo_deps)

    def adicionar_dependencia(self, origem, destino, peso):
        nova = deps.validar({"origem": origem, "destino": destino, "peso": peso})
        for ativo_id in (nova["origem"], nova["destino"]):
            self.ativo(ativo_id)
        deps.gravar(self.dependencias() + [nova], self._arquivo_deps)
        self.analise_risco()
        self._eventos.publicar(DADOS_ALTERADOS)

    def remover_dependencia(self, origem, destino):
        restantes = [d for d in self.dependencias()
                     if (d["origem"], d["destino"]) != (int(origem), int(destino))]
        deps.gravar(restantes, self._arquivo_deps)
        self._eventos.publicar(DADOS_ALTERADOS)

    def analise_risco(self):
        return risco.analisar([a.to_dict() for a in self._ativos.values()], self.dependencias())

    def grafo(self):
        return GrafoDirecionado.de_dependencias(list(self._ativos), self.dependencias())

    def raio_de_impacto(self, origem):
        analise = self.analise_risco()
        propagado = dict(zip(analise.ids, (round(float(v), 2) for v in analise.x)))
        return [
            {"ativo": self._ativos[aid], "saltos": saltos, "risco_propagado": propagado.get(aid, 0.0)}
            for aid, saltos in self.grafo().bfs(int(origem)).items()
        ]
