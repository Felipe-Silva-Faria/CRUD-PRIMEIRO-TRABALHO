import json
import os
from tkinter import messagebox
from config import ARQUIVO_TXT
from persistencia import estado


def ler_txt():
    ativos = []
    if not os.path.exists(ARQUIVO_TXT):
        return ativos
    try:
        with open(ARQUIVO_TXT, "r", encoding="utf-8") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if linha == "":
                    continue
                ativos.append(json.loads(linha))
    except (OSError, json.JSONDecodeError) as e:
        print("Erro lendo o txt:", e)
    return ativos


def escrever_txt(ativo):
    with open(ARQUIVO_TXT, "a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(ativo, ensure_ascii=False) + "\n")


def sobrescrever_txt_inteiro(ativos):
    try:
        with open(ARQUIVO_TXT, "w", encoding="utf-8") as arquivo:
            arquivo.writelines(json.dumps(ativo, ensure_ascii=False) + "\n" for ativo in ativos)
        return True
    except OSError as e:
        print("Erro salvando txt:", e)
        return False


def avisar_offline():
    if estado.modo_offline is False:
        estado.modo_offline = True
        messagebox.showwarning(
            "FastAPI indisponivel",
            "Nao foi possivel falar com a FastAPI.\n"
            "O programa vai usar o arquivo " + ARQUIVO_TXT + " como banco de dados."
        )