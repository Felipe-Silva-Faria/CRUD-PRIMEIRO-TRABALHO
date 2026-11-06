from enum import Enum

from dominio.excecoes import ErroValidacao

GRUPO_ADMINISTRACAO = "Administração"


# Lista de autorizacoes (uma para cada acao)
class Autorizacao(Enum):
    VER_ATIVOS = ("ativo.ver", "Visualizar ativos", "Ativos")
    CRIAR_ATIVO = ("ativo.criar", "Adicionar ativo", "Ativos")
    EDITAR_ATIVO = ("ativo.editar", "Editar ativo", "Ativos")
    EXCLUIR_ATIVO = ("ativo.excluir", "Excluir ativo", "Ativos")

    VER_VULNERABILIDADES = ("vulnerabilidade.ver", "Visualizar vulnerabilidades", "Vulnerabilidades")
    CRIAR_VULNERABILIDADE = ("vulnerabilidade.criar", "Adicionar vulnerabilidade", "Vulnerabilidades")
    EDITAR_VULNERABILIDADE = ("vulnerabilidade.editar", "Editar vulnerabilidade", "Vulnerabilidades")
    EXCLUIR_VULNERABILIDADE = ("vulnerabilidade.excluir", "Excluir vulnerabilidade", "Vulnerabilidades")

    VER_RISCOS = ("risco.ver", "Visualizar análise de riscos", "Riscos")
    GERENCIAR_DEPENDENCIAS = ("risco.dependencias", "Adicionar e remover dependências", "Riscos")

    VER_RELATORIOS = ("relatorio.ver", "Visualizar relatórios", "Relatórios")
    EXPORTAR_RELATORIOS = ("relatorio.exportar", "Exportar relatórios (CSV)", "Relatórios")

    VER_USUARIOS = ("usuario.ver", "Visualizar usuários e acessos", GRUPO_ADMINISTRACAO)
    CRIAR_USUARIO = ("usuario.criar", "Criar novos usuários", GRUPO_ADMINISTRACAO)
    EDITAR_USUARIO = ("usuario.editar", "Alterar funções, autorizações e status de usuários",
                      GRUPO_ADMINISTRACAO)
    APROVAR_CADASTRO = ("cadastro.aprovar", "Aprovar solicitações de cadastro", GRUPO_ADMINISTRACAO)
    APROVAR_AUTORIZACAO = ("autorizacao.aprovar", "Aprovar solicitações de autorização de outros usuários",
                           GRUPO_ADMINISTRACAO)

    @property
    def codigo(self):
        return self.value[0]

    @property
    def rotulo(self):
        return self.value[1]

    @property
    def grupo(self):
        return self.value[2]

    @property
    def solicitavel(self):
        return self.grupo != GRUPO_ADMINISTRACAO

    @classmethod
    def de_codigo(cls, codigo):
        for membro in cls:
            if membro.codigo == codigo:
                return membro
        raise ErroValidacao("autorizacao", f"autorizacao desconhecida: {codigo}")

    @classmethod
    def grupos(cls):
        resultado = {}
        for membro in cls:
            resultado.setdefault(membro.grupo, []).append(membro)
        return resultado


def _do_grupo(grupo):
    return frozenset(a for a in Autorizacao if a.grupo == grupo)


# Funcoes padrao (conjunto de autorizacoes)
class Funcao(Enum):
    ATIVOS = ("ativos", "Ativos", _do_grupo("Ativos"), True)
    VULNERABILIDADES = ("vulnerabilidades", "Vulnerabilidades", _do_grupo("Vulnerabilidades"), True)
    ADMINISTRADOR = ("administrador", "Administrador", frozenset(Autorizacao), False)

    @property
    def codigo(self):
        return self.value[0]

    @property
    def rotulo(self):
        return self.value[1]

    @property
    def autorizacoes(self):
        return self.value[2]

    @property
    def solicitavel(self):
        return self.value[3]

    @classmethod
    def de_codigo(cls, codigo):
        for membro in cls:
            if membro.codigo == codigo or membro.rotulo == codigo:
                return membro
        raise ErroValidacao("funcao", f"funcao desconhecida: {codigo}")

    @classmethod
    def solicitaveis(cls):
        return [f for f in cls if f.solicitavel]


# Junta as autorizacoes das funcoes com as extras
def autorizacoes_efetivas(funcoes, extras=()):
    efetivas = set()
    for codigo in funcoes:
        efetivas |= Funcao.de_codigo(codigo).autorizacoes
    for codigo in extras:
        efetivas.add(Autorizacao.de_codigo(codigo))
    return efetivas


# Diz de onde veio cada autorizacao
def origem_das_autorizacoes(funcoes, extras=()):
    origem = {}
    for codigo in funcoes:
        funcao = Funcao.de_codigo(codigo)
        for aut in funcao.autorizacoes:
            origem.setdefault(aut, f"Função {funcao.rotulo}")
    for codigo in extras:
        origem.setdefault(Autorizacao.de_codigo(codigo), "Concedida individualmente")
    return origem
