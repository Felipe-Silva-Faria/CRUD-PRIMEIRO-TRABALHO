from abc import ABC, abstractmethod

from dominio.enums import Severidade, StatusTratamento, TipoAtivo
from dominio.excecoes import ErroValidacao
from dominio.validacao import (validar_id, validar_progresso, validar_texto,
                               validar_texto_livre)


class Entidade(ABC):
    def __init__(self, id_=None):
        self._id = None
        self.id = id_

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, valor):
        self._id = None if valor is None else validar_id(valor)

    @abstractmethod
    def to_dict(self):
        ...

    @abstractmethod
    def resumo(self):
        ...

    def __eq__(self, outro):
        return type(self) is type(outro) and self.to_dict() == outro.to_dict()

    def __repr__(self):
        return f"{type(self).__name__}({self.to_dict()!r})"


class Vulnerabilidade(Entidade):
    def __init__(self, nome, severidade, responsavel="", tratamento="",
                 progresso=0, risco_aceito=False):
        super().__init__(None)
        self.nome = nome
        self.severidade = severidade
        self.responsavel = responsavel
        self.tratamento = tratamento
        self.progresso = progresso
        self.risco_aceito = bool(risco_aceito)

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        self._nome = validar_texto("nome da vulnerabilidade", valor, permitir_digitos=True, maximo=120)

    @property
    def severidade(self):
        return self._severidade

    @severidade.setter
    def severidade(self, valor):
        try:
            self._severidade = Severidade.de_valor(valor)
        except ValueError as erro:
            raise ErroValidacao("severidade", str(erro)) from None

    @property
    def responsavel(self):
        return self._responsavel

    @responsavel.setter
    def responsavel(self, valor):
        self._responsavel = validar_texto("responsavel", valor, obrigatorio=False)

    @property
    def tratamento(self):
        return self._tratamento

    @tratamento.setter
    def tratamento(self, valor):
        self._tratamento = validar_texto_livre("tratamento", valor)

    @property
    def progresso(self):
        return self._progresso

    @progresso.setter
    def progresso(self, valor):
        self._progresso = validar_progresso(valor)

    @property
    def status(self):
        if self.risco_aceito:
            return StatusTratamento.RISCO_ACEITO
        return StatusTratamento.a_partir_do_progresso(self.progresso)

    @property
    def aberta(self):
        return self.status in (StatusTratamento.ABERTA, StatusTratamento.EM_TRATAMENTO)

    def risco_residual(self):
        if not self.aberta:
            return 0.0
        return self.severidade.value * (10 - self.progresso) / 10

    def to_dict(self):
        return {
            "nome": self.nome,
            "severidade": self.severidade.rotulo,
            "responsavel": self.responsavel,
            "tratamento": self.tratamento,
            "progresso": self.progresso,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, dados):
        status = dados.get("status")
        risco_aceito = status is not None and StatusTratamento.de_valor(status) is StatusTratamento.RISCO_ACEITO
        return cls(
            nome=dados.get("nome", ""),
            severidade=dados.get("severidade", ""),
            responsavel=dados.get("responsavel", ""),
            tratamento=dados.get("tratamento", ""),
            progresso=dados.get("progresso", 0),
            risco_aceito=risco_aceito,
        )

    def resumo(self):
        return f"{self.nome} [{self.severidade.rotulo}] - {self.status.value} ({self.progresso}/10)"


class Ativo(Entidade):
    TIPO = TipoAtivo.OUTRO

    def __init__(self, nome, local, vulnerabilidades=None, id_=None):
        super().__init__(id_)
        self.tipo_texto = None
        self.nome = nome
        self.local = local
        self._vulnerabilidades = []
        for vul in vulnerabilidades or []:
            self.adicionar_vulnerabilidade(vul)

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        self._nome = validar_texto("nome", valor, permitir_digitos=True)

    @property
    def local(self):
        return self._local

    @local.setter
    def local(self, valor):
        self._local = validar_texto("local", valor, permitir_digitos=True)

    @property
    def tipo(self):
        return self.TIPO

    @property
    def vulnerabilidades(self):
        return list(self._vulnerabilidades)

    def adicionar_vulnerabilidade(self, vul):
        if isinstance(vul, dict):
            vul = Vulnerabilidade.from_dict(vul)
        if not isinstance(vul, Vulnerabilidade):
            raise ErroValidacao("vulnerabilidades", "item nao e uma vulnerabilidade")
        self._vulnerabilidades.append(vul)
        return vul

    def remover_vulnerabilidade(self, indice):
        if not 0 <= indice < len(self._vulnerabilidades):
            raise ErroValidacao("vulnerabilidade", f"indice {indice} inexistente")
        return self._vulnerabilidades.pop(indice)

    @abstractmethod
    def fator_exposicao(self):
        ...

    @abstractmethod
    def recomendacao(self):
        ...

    def risco_total(self):
        base = sum(v.risco_residual() for v in self._vulnerabilidades)
        return round(base * self.fator_exposicao(), 2)

    def pior_severidade(self):
        abertas = [v.severidade for v in self._vulnerabilidades if v.aberta]
        return max(abertas) if abertas else None

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo_texto or self.tipo.rotulo,
            "local": self.local,
            "vulnerabilidades": [v.to_dict() for v in self._vulnerabilidades],
        }

    def resumo(self):
        return (f"#{self.id} {self.nome} ({self.tipo.rotulo}) em {self.local} - "
                f"{len(self._vulnerabilidades)} vulnerabilidade(s), risco {self.risco_total()}")


_REGISTRO = {}


def registrar_tipo(classe):
    _REGISTRO[classe.TIPO] = classe
    return classe


@registrar_tipo
class Servidor(Ativo):
    TIPO = TipoAtivo.SERVIDOR

    def fator_exposicao(self):
        return 1.5

    def recomendacao(self):
        return "Aplicar patches do SO, fechar portas nao usadas e revisar contas de servico."


@registrar_tipo
class Notebook(Ativo):
    TIPO = TipoAtivo.NOTEBOOK

    def fator_exposicao(self):
        return 1.0

    def recomendacao(self):
        return "Criptografar o disco, manter antivirus/EDR ativo e bloquear tela automaticamente."


@registrar_tipo
class Roteador(Ativo):
    TIPO = TipoAtivo.ROTEADOR

    def fator_exposicao(self):
        return 1.3

    def recomendacao(self):
        return "Trocar senhas padrao, atualizar firmware e desabilitar administracao remota."


@registrar_tipo
class AplicacaoWeb(Ativo):
    TIPO = TipoAtivo.APLICACAO_WEB

    def fator_exposicao(self):
        return 1.4

    def recomendacao(self):
        return "Validar entradas (OWASP Top 10), usar HTTPS e revisar dependencias."


@registrar_tipo
class BancoDeDados(Ativo):
    TIPO = TipoAtivo.BANCO_DE_DADOS

    def fator_exposicao(self):
        return 1.6

    def recomendacao(self):
        return "Restringir acesso por rede, aplicar menor privilegio e criptografar backups."


@registrar_tipo
class AtivoGenerico(Ativo):
    TIPO = TipoAtivo.OUTRO

    def fator_exposicao(self):
        return 1.0

    def recomendacao(self):
        return "Inventariar o ativo e definir um responsavel."


def criar_ativo(dados):
    tipo_original = dados.get("tipo", TipoAtivo.OUTRO)
    tipo = TipoAtivo.de_valor(tipo_original)
    classe = _REGISTRO.get(tipo, AtivoGenerico)
    ativo = classe(
        nome=dados.get("nome", ""),
        local=dados.get("local", ""),
        vulnerabilidades=dados.get("vulnerabilidades", []),
        id_=dados.get("id"),
    )
    if tipo is TipoAtivo.OUTRO and isinstance(tipo_original, str) and tipo_original.strip():
        ativo.tipo_texto = " ".join(tipo_original.split())
    return ativo
