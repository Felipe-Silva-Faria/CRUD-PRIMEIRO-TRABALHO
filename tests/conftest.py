import os
import random

import pytest

from persistencia.repositorio import RepositorioMemoria
from servicos.servico_ativos import ServicoAtivos

os.environ.setdefault("CRUD_REPOSITORIO", "memoria")


@pytest.fixture
def dados_servidor():
    return {
        "nome": "Servidor Web",
        "tipo": "Servidor",
        "local": "Data Center",
        "vulnerabilidades": [
            {"nome": "CVE-2021-44228 Log4Shell", "severidade": "Crítica",
             "responsavel": "Ana Souza", "tratamento": "Atualizar log4j", "progresso": 0},
            {"nome": "TLS 1.0 habilitado", "severidade": "Media",
             "responsavel": "", "tratamento": "", "progresso": 5},
        ],
    }


@pytest.fixture
def dados_notebook():
    return {"nome": "Notebook Financeiro", "tipo": "Notebook", "local": "Sala Dois", "vulnerabilidades": []}


@pytest.fixture
def servico():
    return ServicoAtivos(RepositorioMemoria(), aleatorio=random.Random(123))
