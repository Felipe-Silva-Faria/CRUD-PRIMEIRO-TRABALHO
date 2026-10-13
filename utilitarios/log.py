import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

FORMATO = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_configurado = False


def configurar_logs(pasta="logs", nivel=logging.INFO):
    global _configurado
    if _configurado:
        return
    Path(pasta).mkdir(exist_ok=True)
    arquivo = RotatingFileHandler(Path(pasta) / "crud.log", maxBytes=1_000_000,
                                  backupCount=3, encoding="utf-8")
    arquivo.setFormatter(logging.Formatter(FORMATO))
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(FORMATO))
    raiz = logging.getLogger()
    raiz.setLevel(nivel)
    raiz.addHandler(arquivo)
    raiz.addHandler(console)
    _configurado = True


def obter_logger(nome):
    return logging.getLogger(nome)
