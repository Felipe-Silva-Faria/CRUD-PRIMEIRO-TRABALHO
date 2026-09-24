from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random

app = FastAPI()


class Vulnerabilidade(BaseModel):
    nome: str
    severidade: str
    responsavel: str = ""
    tratamento: str = ""
    progresso: int = 0


class AtivoCreate(BaseModel):
    nome: str
    tipo: str
    local: str
    vulnerabilidades: list[Vulnerabilidade] = []


class Ativo(AtivoCreate):
    id: int


lugar = []


# gera um id de 5 digitos que ainda nao existe
def gerar_id():
    ids_usados = []
    for ativo in lugar:
        ids_usados.append(ativo["id"])
    novo_id = random.randint(10000, 99999)
    while novo_id in ids_usados:
        novo_id = random.randint(10000, 99999)
    return novo_id


# procura o indice do ativo pelo id
def achar_indice(ativo_id: int):
    for i, ativo in enumerate(lugar):
        if ativo["id"] == ativo_id:
            return i
    return -1


@app.post("/ativos")
def add_ativo(ativo: AtivoCreate):
    novo_id = gerar_id()
    novo_ativo = {
        "id": novo_id,
        "nome": ativo.nome,
        "tipo": ativo.tipo,
        "local": ativo.local,
        "vulnerabilidades": ativo.vulnerabilidades
    }
    lugar.append(novo_ativo)
    print(f"Recebido e salvo no FastAPI: {ativo.nome} com ID {novo_id}")
    return {"mensagem": "Ativo Salvo com sucesso!", "dados": novo_ativo}


@app.get("/ativos")
def lista_ativos():
    return lugar


@app.get("/ativos/{ativo_id}")
def pegar_ativo(ativo_id: int):
    indice = achar_indice(ativo_id)
    if indice == -1:
        raise HTTPException(status_code=404, detail="Ativo nao encontrado")
    return lugar[indice]


@app.put("/ativos/{ativo_id}")
def atualizar_ativo(ativo_id: int, ativo: AtivoCreate):
    indice = achar_indice(ativo_id)
    if indice == -1:
        raise HTTPException(status_code=404, detail="Ativo nao encontrado")
    ativo_atualizado = {
        "id": ativo_id,
        "nome": ativo.nome,
        "tipo": ativo.tipo,
        "local": ativo.local,
        "vulnerabilidades": ativo.vulnerabilidades
    }
    lugar[indice] = ativo_atualizado
    print(f"Atualizado no FastAPI: {ativo.nome} com ID {ativo_id}")
    return {"mensagem": "Ativo atualizado com sucesso!", "dados": ativo_atualizado}


@app.delete("/ativos/{ativo_id}")
def deletar_ativo(ativo_id: int):
    indice = achar_indice(ativo_id)
    if indice == -1:
        raise HTTPException(status_code=404, detail="Ativo nao encontrado")
    removido = lugar.pop(indice)
    print(f"Deletado no FastAPI: {removido['nome']} com ID {ativo_id}")
    return {"mensagem": "Ativo deletado com sucesso!", "dados": removido}
