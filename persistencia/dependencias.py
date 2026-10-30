import json
import os
import tempfile
from pathlib import Path
from dominio.excecoes import ErroValidacao

ARQUIVO_DEPENDENCIAS = "dependencias.json"


def validar(dependencia):
    try:
        origem = int(dependencia["origem"])
        destino = int(dependencia["destino"])
        peso = float(str(dependencia["peso"]).replace(",", "."))
    except (KeyError, TypeError, ValueError):
        raise ErroValidacao("dependencia", "informe origem, destino (ids inteiros) e peso (numero)") from None
    if origem == destino:
        raise ErroValidacao("dependencia", "um ativo nao pode depender de si mesmo")
    if not 0.0 < peso < 1.0:
        raise ErroValidacao("dependencia", "o peso deve estar entre 0 e 1 (exclusivo)")
    return {"origem": origem, "destino": destino, "peso": round(peso, 4)}


def ler(caminho=ARQUIVO_DEPENDENCIAS):
    caminho = Path(caminho)
    if not caminho.exists():
        return []
    with caminho.open("r", encoding="utf-8") as arquivo:
        return [validar(d) for d in json.load(arquivo)]


def gravar(dependencias, caminho=ARQUIVO_DEPENDENCIAS):
    caminho = Path(caminho)
    validas = {}
    for d in dependencias:
        d = validar(d)
        validas[(d["origem"], d["destino"])] = d
    pasta = caminho.parent if str(caminho.parent) else Path(".")
    descritor, temporario = tempfile.mkstemp(dir=pasta, prefix=".tmp_", suffix=".json")
    with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
        json.dump(list(validas.values()), arquivo, ensure_ascii=False, indent=2)
    os.replace(temporario, caminho)
    return list(validas.values())


def remover_do_ativo(ativo_id, caminho=ARQUIVO_DEPENDENCIAS):
    restantes = [d for d in ler(caminho) if ativo_id not in (d["origem"], d["destino"])]
    return gravar(restantes, caminho)
