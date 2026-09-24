import random
from tkinter import messagebox
import requests
from persistencia.banco_txt import avisar_offline, escrever_txt, ler_txt, sobrescrever_txt_inteiro
from config import URL_API
from persistencia import estado

## solicita ativos
def pegar_ativos():
    try:
        resposta = requests.get(URL_API, timeout=3)
        if resposta.status_code == 200:
            estado.modo_offline = False
            return resposta.json()
        avisar_offline()
        return ler_txt()
    except Exception as e:
        print("Erro na api:", e)
        avisar_offline()
        return ler_txt()

# envia ativos
def mandar_ativo(dados):
    try:
        resposta = requests.post(URL_API, json=dados, timeout=3)
        if resposta.status_code == 200:
            estado.modo_offline = False
            return True
    except Exception as e:
        print("Erro na api:", e)
        avisar_offline()

    # bypass da fastapi --> gera o id aqui e grava no arquivo
    ids_usados = []
    for ativo in ler_txt():
        ids_usados.append(ativo["id"])
    novo_id = random.randint(10000, 99999)
    while novo_id in ids_usados:
        novo_id = random.randint(10000, 99999)
    novo_ativo = {
        "id": novo_id,
        "nome": dados["nome"],
        "tipo": dados["tipo"],
        "local": dados["local"],
        "vulnerabilidades": dados["vulnerabilidades"]
    }
    try:
        escrever_txt(novo_ativo)
        return True
    except Exception as e:
        messagebox.showerror("Erro", "Nao deu pra salvar nem no txt:\n" + str(e))
        return False


# deletar ativo
def deletar_ativo_api_ou_txt(ativo_id):
    try:
        resposta = requests.delete(f"{URL_API}/{ativo_id}", timeout=3)
        if resposta.status_code == 200:
            return True
        if resposta.status_code in [404, 405]:
            avisar_offline()
    except Exception as e:
        print("Erro na api:", e)
        avisar_offline()

    ativos = ler_txt()
    novos_ativos = [a for a in ativos if a["id"] != ativo_id]
    if len(novos_ativos) < len(ativos):
        return sobrescrever_txt_inteiro(novos_ativos)
    return False


# atualizar ativo (PUT)
def atualizar_ativo_api_ou_txt(ativo_id, dados):
    try:
        resposta = requests.put(f"{URL_API}/{ativo_id}", json=dados, timeout=3)
        if resposta.status_code == 200:
            return True
        if resposta.status_code in [404, 405]:
            avisar_offline()
    except Exception as e:
        print("Erro na api:", e)
        avisar_offline()

    ativos = ler_txt()
    atualizado = False
    for i, a in enumerate(ativos):
        if a["id"] == ativo_id:
            ativos[i] = {
                "id": ativo_id,
                "nome": dados["nome"],
                "tipo": dados["tipo"],
                "local": dados["local"],
                "vulnerabilidades": dados["vulnerabilidades"]
            }
            atualizado = True
            break
    if atualizado:
        return sobrescrever_txt_inteiro(ativos)
    return False
