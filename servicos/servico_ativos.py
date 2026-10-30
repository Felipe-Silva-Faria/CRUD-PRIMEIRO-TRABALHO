import logging
import random
from datetime import datetime
from algoritmos.busca import busca_por_prefixo
from algoritmos.ordenacao import ordenar
from dominio.entidades import criar_ativo
from dominio.enums import normalizar_chave
from dominio.excecoes import ErroCRUD, ErroValidacao
from estruturas.fila import FilaLimitada
from utilitarios.funcional import todos

logger = logging.getLogger(__name__)

ID_MINIMO, ID_MAXIMO = 10000, 99999

CHAVES_ORDENACAO = {
    "id": lambda a: a.id,
    "nome": lambda a: normalizar_chave(a.nome),
    "tipo": lambda a: a.tipo.rotulo,
    "local": lambda a: normalizar_chave(a.local),
    "vulnerabilidades": lambda a: len(a.vulnerabilidades),
    "cvss": lambda a: a.maior_cvss() or 0.0,
    "risco": lambda a: a.risco_total(),
}


class ServicoAtivos:
    def __init__(self, repositorio, aleatorio=None, tamanho_historico=200):
        self._repo = repositorio
        self._aleatorio = aleatorio or random.Random()
        self.historico = FilaLimitada(tamanho_historico)

    def _registrar(self, acao, ativo_id, detalhe=""):
        evento = {"quando": datetime.now().isoformat(timespec="seconds"),
                  "acao": acao, "ativo_id": ativo_id, "detalhe": detalhe}
        self.historico.enfileirar(evento)
        logger.info("%s ativo %s %s", acao, ativo_id, detalhe)

    def gerar_id(self):
        usados = self._repo.ids()
        if len(usados) >= ID_MAXIMO - ID_MINIMO + 1:
            raise ErroCRUD("Nao ha mais ids disponiveis")
        while True:
            candidato = self._aleatorio.randint(ID_MINIMO, ID_MAXIMO)
            if candidato not in usados:
                return candidato

    def cadastrar(self, dados):
        dados = dict(dados)
        dados["id"] = self.gerar_id()
        ativo = criar_ativo(dados)
        self._repo.salvar(ativo)
        self._registrar("CADASTRO", ativo.id, ativo.nome)
        return ativo

    def obter(self, ativo_id):
        return self._repo.obter(ativo_id)

    def atualizar(self, ativo_id, dados):
        self._repo.obter(ativo_id)
        dados = dict(dados)
        dados["id"] = ativo_id
        ativo = criar_ativo(dados)
        self._repo.salvar(ativo)
        self._registrar("ATUALIZACAO", ativo_id, ativo.nome)
        return ativo

    def remover(self, ativo_id):
        ativo = self._repo.obter(ativo_id)
        self._repo.remover(ativo_id)
        self._registrar("REMOCAO", ativo_id, ativo.nome)
        return ativo

    def adicionar_vulnerabilidade(self, ativo_id, dados_vul):
        ativo = self._repo.obter(ativo_id)
        vul = ativo.adicionar_vulnerabilidade(dados_vul)
        self._repo.salvar(ativo)
        self._registrar("VULNERABILIDADE+", ativo_id, vul.nome)
        return ativo

    def remover_vulnerabilidade(self, ativo_id, indice):
        ativo = self._repo.obter(ativo_id)
        vul = ativo.remover_vulnerabilidade(indice)
        self._repo.salvar(ativo)
        self._registrar("VULNERABILIDADE-", ativo_id, vul.nome)
        return ativo

    def listar(self, predicados=(), ordenar_por=None, reverso=False, algoritmo="merge"):
        ativos = [a for a in self._repo.listar() if todos(*predicados)(a)]
        if ordenar_por is None:
            return ativos
        if ordenar_por not in CHAVES_ORDENACAO:
            raise ErroValidacao("ordenar_por", f"use um de {sorted(CHAVES_ORDENACAO)}")
        return ordenar(ativos, chave=CHAVES_ORDENACAO[ordenar_por], reverso=reverso, algoritmo=algoritmo)

    def buscar_por_prefixo(self, prefixo):
        chave = CHAVES_ORDENACAO["nome"]
        ordenados = ordenar(self._repo.listar(), chave=chave)
        return busca_por_prefixo(ordenados, normalizar_chave(prefixo), chave=chave)

    def relatorio_risco(self, limite=None):
        ranking = self.listar(ordenar_por="risco", reverso=True)
        return ranking[:limite] if limite else ranking
