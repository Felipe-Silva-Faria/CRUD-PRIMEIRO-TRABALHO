import os
import requests
from algoritmos.ordenacao import ALGORITMOS
from api.cliente_api import ClienteAPI
from config import ARQUIVO_TXT, URL_API
from interface.moderna import preferencias
from persistencia.repositorio import RepositorioJsonLines
from persistencia.usuarios import RepositorioUsuariosJSON
from servicos.autenticacao import ServicoAutenticacao
from servicos.eventos import CONEXAO_ALTERADA, BarramentoEventos
from servicos.painel import FonteLocal, PainelVulnerabilidades
from servicos.servico_ativos import ServicoAtivos


def montar(modo_local=False):
    eventos = BarramentoEventos()
    if modo_local:
        fonte = FonteLocal(ServicoAtivos(RepositorioJsonLines(ARQUIVO_TXT)))
        descricao = "local"
    else:
        sessao = requests.Session()
        chave = os.getenv("CRUD_API_KEY", "")
        if chave:
            sessao.headers["X-API-Key"] = chave
        fonte = ClienteAPI(url=URL_API, arquivo_local=ARQUIVO_TXT, sessao=sessao,
                           ao_mudar_conexao=lambda online: eventos.publicar(CONEXAO_ALTERADA, online=online))
        descricao = "api"
    algoritmo = preferencias.ler().get("algoritmo", "merge")
    painel = PainelVulnerabilidades(fonte, eventos, algoritmo=algoritmo if algoritmo in ALGORITMOS else "merge")
    autenticacao = ServicoAutenticacao(RepositorioUsuariosJSON())
    return painel, autenticacao, eventos, descricao


def iniciar(modo_local=False):
    from interface.moderna.app import Aplicacao

    painel, autenticacao, eventos, descricao = montar(modo_local)
    Aplicacao(painel, autenticacao, eventos, descricao).mainloop()
