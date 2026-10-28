import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

_CAMPOS_PADRAO = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}


class FormatadorJSON(logging.Formatter):
    def format(self, registro):
        evento = {
            "quando": datetime.fromtimestamp(registro.created, timezone.utc).isoformat(),
            "nivel": registro.levelname,
            "modulo": registro.name,
            "mensagem": registro.getMessage(),
        }
        for chave, valor in vars(registro).items():
            if chave not in _CAMPOS_PADRAO and chave not in evento:
                evento[chave] = valor
        if registro.exc_info:
            evento["excecao"] = self.formatException(registro.exc_info)
        return json.dumps(evento, ensure_ascii=False, default=str)


def ativar_log_json(pasta=None):
    raiz = logging.getLogger()
    if getattr(raiz, "_log_json_ativo", False):
        return raiz
    if raiz.level == logging.NOTSET or raiz.level > logging.INFO:
        raiz.setLevel(logging.INFO)
    pasta = Path(pasta or os.getenv("CRUD_LOGS", "logs"))
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        manipulador = RotatingFileHandler(pasta / "crud.jsonl", maxBytes=1_000_000,
                                          backupCount=5, encoding="utf-8")
        manipulador.setFormatter(FormatadorJSON())
        raiz.addHandler(manipulador)
    except OSError as erro:
        raiz.warning("log JSON desativado: %s", erro)
    raiz._log_json_ativo = True
    return raiz


def evento_seguranca(logger, evento, nivel=logging.WARNING, **campos):
    logger.log(nivel, evento, extra={"evento_seguranca": evento, **campos})
