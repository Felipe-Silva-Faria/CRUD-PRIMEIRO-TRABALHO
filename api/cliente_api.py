import logging
from dataclasses import dataclass, field
import requests
from config import ARQUIVO_TXT, URL_API
from dominio.entidades import criar_ativo
from dominio.excecoes import ApiIndisponivel, AtivoNaoEncontrado, ErroCRUD
from estruturas.fila import Fila
from persistencia.repositorio import RepositorioJsonLines
from servicos.servico_ativos import ServicoAtivos
from utilitarios.funcional import tentar_novamente

logger = logging.getLogger(__name__)

ERROS_DE_REDE = (requests.ConnectionError, requests.Timeout)


@dataclass
class OperacaoPendente:
    metodo: str
    ativo_id: int
    dados: dict = field(default_factory=dict)


def _sucesso(resposta):
    return 200 <= resposta.status_code < 300


class ClienteAPI:
    def __init__(self, url=URL_API, sessao=None, timeout=3, arquivo_local=ARQUIVO_TXT,
                 ao_mudar_conexao=None, tentativas=2):
        self.url = url.rstrip("/")
        self.sessao = sessao or requests.Session()
        self.timeout = timeout
        self._cache = RepositorioJsonLines(arquivo_local)
        self.local = ServicoAtivos(self._cache)
        self.pendentes = Fila()
        self.online = True
        self._ao_mudar_conexao = ao_mudar_conexao or (lambda online: None)
        self._requisitar = tentar_novamente(tentativas, espera=0.3, excecoes=ERROS_DE_REDE)(self._requisitar_uma_vez)

    def _requisitar_uma_vez(self, metodo, caminho="", json=None):
        return self.sessao.request(metodo, self.url + caminho, json=json, timeout=self.timeout)

    def _chamar(self, metodo, caminho="", json=None):
        try:
            resposta = self._requisitar(metodo, caminho, json=json)
        except ERROS_DE_REDE as erro:
            self._definir_online(False)
            raise ApiIndisponivel(str(erro)) from erro
        if resposta.status_code >= 500:
            self._definir_online(False)
            raise ApiIndisponivel(f"HTTP {resposta.status_code}")
        self._definir_online(True)
        return resposta

    def _definir_online(self, online):
        if online != self.online:
            self.online = online
            logger.warning("API %s", "voltou" if online else "indisponivel - usando arquivo local")
            self._ao_mudar_conexao(online)

    def listar(self):
        try:
            if not self.pendentes.esta_vazia():
                self.sincronizar()
            resposta = self._chamar("GET")
            dados = resposta.json()
            self._cache.substituir_tudo([criar_ativo(d) for d in dados])
            return dados
        except ApiIndisponivel:
            return [a.to_dict() for a in self.local.listar()]

    def cadastrar(self, dados):
        try:
            resposta = self._chamar("POST", json=dados)
            if _sucesso(resposta):
                return resposta.json()
            raise ErroCRUD(resposta.json().get("detail", "erro ao cadastrar"))
        except ApiIndisponivel:
            ativo = self.local.cadastrar(dados)
            self.pendentes.enfileirar(OperacaoPendente("POST", ativo.id, ativo.to_dict()))
            return ativo.to_dict()

    def atualizar(self, ativo_id, dados):
        try:
            resposta = self._chamar("PUT", f"/{ativo_id}", json=dados)
            if resposta.status_code == 404:
                raise AtivoNaoEncontrado(ativo_id)
            if _sucesso(resposta):
                return resposta.json()
            raise ErroCRUD(resposta.json().get("detail", "erro ao atualizar"))
        except ApiIndisponivel:
            ativo = self.local.atualizar(ativo_id, dados)
            self.pendentes.enfileirar(OperacaoPendente("PUT", ativo_id, ativo.to_dict()))
            return ativo.to_dict()

    def remover(self, ativo_id):
        try:
            resposta = self._chamar("DELETE", f"/{ativo_id}")
            if resposta.status_code == 404:
                raise AtivoNaoEncontrado(ativo_id)
            return _sucesso(resposta)
        except ApiIndisponivel:
            self.local.remover(ativo_id)
            self.pendentes.enfileirar(OperacaoPendente("DELETE", ativo_id))
            return True

    def sincronizar(self):
        mapa_ids = {}
        enviadas = 0
        restantes = Fila()
        while not self.pendentes.esta_vazia():
            op = self.pendentes.desenfileirar()
            ativo_id = mapa_ids.get(op.ativo_id, op.ativo_id)
            corpo = {k: v for k, v in op.dados.items() if k != "id"}
            try:
                if op.metodo == "POST":
                    resposta = self._chamar("POST", json=corpo)
                    if _sucesso(resposta):
                        mapa_ids[op.ativo_id] = resposta.json()["id"]
                elif op.metodo == "PUT":
                    self._chamar("PUT", f"/{ativo_id}", json=corpo)
                elif op.metodo == "DELETE":
                    self._chamar("DELETE", f"/{ativo_id}")
                enviadas += 1
            except ApiIndisponivel:
                restantes.enfileirar(op)
                while not self.pendentes.esta_vazia():
                    restantes.enfileirar(self.pendentes.desenfileirar())
                self.pendentes = restantes
                raise
        logger.info("Sincronizacao concluida: %d operacao(oes)", enviadas)
        return enviadas
