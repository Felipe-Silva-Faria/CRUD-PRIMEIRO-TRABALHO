from tkinter import messagebox

from api.cliente_api import ClienteAPI
from config import ARQUIVO_TXT, URL_API
from dominio.excecoes import ErroCRUD
from persistencia import estado
from persistencia.banco_txt import avisar_offline


def _ao_mudar_conexao(online):
    if online:
        estado.modo_offline = False
    else:
        avisar_offline()


cliente = ClienteAPI(url=URL_API, arquivo_local=ARQUIVO_TXT, ao_mudar_conexao=_ao_mudar_conexao)


def _mostrar_erro(erro):
    messagebox.showerror("Erro", str(erro))


def pegar_ativos():
    return cliente.listar()


def mandar_ativo(dados):
    try:
        cliente.cadastrar(dados)
        return True
    except ErroCRUD as erro:
        _mostrar_erro(erro)
        return False


def deletar_ativo_api_ou_txt(ativo_id):
    try:
        return cliente.remover(ativo_id)
    except ErroCRUD as erro:
        _mostrar_erro(erro)
        return False


def atualizar_ativo_api_ou_txt(ativo_id, dados):
    try:
        cliente.atualizar(ativo_id, dados)
        return True
    except ErroCRUD as erro:
        _mostrar_erro(erro)
        return False
