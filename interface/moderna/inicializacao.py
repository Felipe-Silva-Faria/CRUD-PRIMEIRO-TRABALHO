import os

import requests

from algoritmos.ordenacao import ALGORITMOS
from api.cliente_api import ClienteAPI
from config import ARQUIVO_TXT, URL_API
from interface.moderna import preferencias
from persistencia.repositorio import RepositorioJsonLines
from persistencia.usuarios import RepositorioUsuariosJSON
from servicos.autenticacao import ServicoAutenticacao
from servicos.contas import ServicoContas
from servicos.eventos import CONEXAO_ALTERADA, BarramentoEventos
from servicos.painel import FonteLocal, PainelVulnerabilidades
from servicos.painel_protegido import PainelProtegido
from servicos.servico_ativos import ServicoAtivos


# Confere a chave da API
def _verificar_chave(sessao):
    try:
        resposta = sessao.get(URL_API, timeout=3)
    except requests.RequestException:
        return
    if resposta.status_code == 401:
        tem_chave = "X-API-Key" in sessao.headers
        motivo = ("a chave definida em CRUD_API_KEY e diferente da chave da API"
                  if tem_chave else "a variavel CRUD_API_KEY nao esta definida neste terminal/execucao")
        raise SystemExit(
            f"A API em {URL_API} exige chave e recusou o acesso (401): {motivo}.\n"
            "Use a MESMA CRUD_API_KEY no terminal da API e na interface, "
            "ou suba a API sem a variavel. Para usar so o arquivo local: python main.py --local"
        )


# Cria os objetos do sistema
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
        _verificar_chave(sessao)
        fonte = ClienteAPI(url=URL_API, arquivo_local=ARQUIVO_TXT, sessao=sessao,
                           ao_mudar_conexao=lambda online: eventos.publicar(CONEXAO_ALTERADA, online=online))
        descricao = "api"
    algoritmo = preferencias.ler().get("algoritmo", "merge")
    painel = PainelVulnerabilidades(fonte, eventos, algoritmo=algoritmo if algoritmo in ALGORITMOS else "merge")
    repo_usuarios = RepositorioUsuariosJSON()
    autenticacao = ServicoAutenticacao(repo_usuarios)
    contas = ServicoContas(repo_usuarios, autenticacao)
    return painel, autenticacao, eventos, descricao, contas


# Abre a janela
def iniciar(modo_local=False):
    from interface.moderna.app import Aplicacao

    painel, autenticacao, eventos, descricao, contas = montar(modo_local)
    sessao = {}

    def usuario_atual():
        app = sessao.get("app")
        return app.nome_usuario if app is not None else ""

    protegido = PainelProtegido(painel, contas, usuario_atual)
    sessao["app"] = Aplicacao(protegido, autenticacao, eventos, descricao, contas)
    sessao["app"].mainloop()
