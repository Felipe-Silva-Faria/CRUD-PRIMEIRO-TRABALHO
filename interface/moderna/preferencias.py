import json
from pathlib import Path

ARQUIVO = Path("preferencias_interface.json")


def ler():
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def gravar(**valores):
    dados = {**ler(), **valores}
    try:
        ARQUIVO.write_text(json.dumps(dados, indent=2), encoding="utf-8")
    except OSError:
        pass
