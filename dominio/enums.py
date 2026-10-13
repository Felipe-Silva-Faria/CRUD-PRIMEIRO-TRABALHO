import unicodedata
from enum import Enum, IntEnum


def normalizar_chave(texto):
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")
    return "_".join(sem_acento.strip().upper().split())


class TipoAtivo(IntEnum):
    NOTEBOOK = 1
    SERVIDOR = 2
    ROTEADOR = 3
    APLICACAO_WEB = 4
    BANCO_DE_DADOS = 5
    OUTRO = 99

    @property
    def rotulo(self):
        return _ROTULOS_TIPO[self]

    @classmethod
    def de_valor(cls, valor):
        if isinstance(valor, cls):
            return valor
        if isinstance(valor, int) or (isinstance(valor, str) and valor.strip().isdigit()):
            try:
                return cls(int(valor))
            except ValueError:
                return cls.OUTRO
        if isinstance(valor, str):
            return cls.__members__.get(normalizar_chave(valor), cls.OUTRO)
        return cls.OUTRO


_ROTULOS_TIPO = {
    TipoAtivo.NOTEBOOK: "Notebook",
    TipoAtivo.SERVIDOR: "Servidor",
    TipoAtivo.ROTEADOR: "Roteador",
    TipoAtivo.APLICACAO_WEB: "Aplicacao Web",
    TipoAtivo.BANCO_DE_DADOS: "Banco de Dados",
    TipoAtivo.OUTRO: "Outro",
}


class Severidade(IntEnum):
    BAIXA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4

    @property
    def rotulo(self):
        return ("Baixa", "Média", "Alta", "Crítica")[self.value - 1]

    @classmethod
    def de_valor(cls, valor):
        if isinstance(valor, cls):
            return valor
        if isinstance(valor, int) or (isinstance(valor, str) and valor.strip().isdigit()):
            return cls(int(valor))
        chave = normalizar_chave(valor)
        if chave not in cls.__members__:
            raise ValueError(f"Severidade invalida: {valor!r}")
        return cls.__members__[chave]


class StatusTratamento(Enum):
    ABERTA = "Aberta"
    EM_TRATAMENTO = "Em tratamento"
    CORRIGIDA = "Corrigida"
    RISCO_ACEITO = "Risco aceito"

    @classmethod
    def a_partir_do_progresso(cls, progresso):
        if progresso <= 0:
            return cls.ABERTA
        if progresso >= 10:
            return cls.CORRIGIDA
        return cls.EM_TRATAMENTO

    @classmethod
    def de_valor(cls, valor):
        if isinstance(valor, cls):
            return valor
        chave = normalizar_chave(valor)
        if chave in cls.__members__:
            return cls.__members__[chave]
        for membro in cls:
            if normalizar_chave(membro.value) == chave:
                return membro
        raise ValueError(f"Status invalido: {valor!r}")
