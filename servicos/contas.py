import logging
import re

from dominio.excecoes import ErroCRUD, ErroValidacao
from dominio.permissoes import GRUPO_ADMINISTRACAO, Autorizacao, Funcao
from dominio.validacao import validar_texto, validar_texto_livre
from persistencia.usuarios import (
    APROVADA,
    PENDENTE,
    RECUSADA,
    SolicitacaoAutorizacao,
    SolicitacaoCadastro,
    Usuario,
    agora,
)
from servicos.autenticacao import validar_nome_usuario
from utilitarios.auditoria import evento_seguranca

logger = logging.getLogger(__name__)

_RE_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")
LIMITE_CADASTROS_PENDENTES = 50
TAMANHO_JUSTIFICATIVA = 300


class ErroPermissao(ErroCRUD):
    def __init__(self, autorizacao):
        self.autorizacao = autorizacao
        super().__init__(f"Acesso negado: você não tem a autorização '{autorizacao.rotulo}'.")


# Valida o email
def validar_email(email):
    email = (email or "").strip().lower()
    if len(email) > 254 or not _RE_EMAIL.match(email):
        raise ErroValidacao("email", "formato invalido (ex.: nome@empresa.com)")
    return email


class ServicoContas:
    def __init__(self, repositorio, autenticacao):
        self._repo = repositorio
        self._auth = autenticacao

    def usuario(self, nome):
        usuario = self._repo.obter(nome)
        if usuario is None:
            raise ErroValidacao("usuario", f"{nome} nao encontrado")
        return usuario

    def usuarios(self):
        return self._repo.listar()

    def cadastros(self):
        return self._repo.cadastros()

    def cadastro(self, pedido_id):
        return self._repo.obter_cadastro(pedido_id)

    def pedidos(self):
        return self._repo.pedidos()

    def pedido(self, pedido_id):
        return self._repo.obter_pedido(pedido_id)

    def pode(self, nome, autorizacao):
        usuario = self._repo.obter(nome)
        return usuario is not None and usuario.pode(autorizacao)

    # Bloqueia se o usuario nao tiver a autorizacao
    def exigir(self, nome, autorizacao):
        if not self.pode(nome, autorizacao):
            evento_seguranca(logger, "authz_fail", usuario=nome, autorizacao=autorizacao.codigo)
            raise ErroPermissao(autorizacao)

    def _exigir_administrador(self, nome, acao):
        usuario = self._repo.obter(nome)
        if usuario is None or not usuario.ativo or not usuario.administrador:
            evento_seguranca(logger, "authz_fail", usuario=nome, acao=acao)
            raise ErroValidacao("permissao", f"somente um administrador pode {acao}")

    # Solicitacao de cadastro (tela de login)
    def solicitar_cadastro(self, usuario, senha, nome_completo, email, funcao, justificativa=""):
        nome = validar_nome_usuario(usuario)
        nome_completo = validar_texto("nome", nome_completo)
        email = validar_email(email)
        funcao = Funcao.de_codigo(funcao)
        if not funcao.solicitavel:
            raise ErroValidacao("funcao", f"a função {funcao.rotulo} não pode ser solicitada")
        justificativa = validar_texto_livre("justificativa", justificativa, TAMANHO_JUSTIFICATIVA)

        pendentes = self.cadastros_pendentes()
        if len(pendentes) >= LIMITE_CADASTROS_PENDENTES:
            raise ErroValidacao("cadastro", "muitas solicitações pendentes; tente mais tarde")
        ocupado = self._repo.obter(nome) is not None or any(p.usuario.lower() == nome.lower() for p in pendentes)
        if ocupado:
            raise ErroValidacao("usuario", "nome de usuário indisponível")
        if any(u.email == email for u in self._repo.listar()) or any(p.email == email for p in pendentes):
            raise ErroValidacao("email", "já existe uma conta ou solicitação com este e-mail")

        hash_senha, sal, iteracoes = self._auth.gerar_credenciais(senha)
        pedido = SolicitacaoCadastro(self._repo.proximo_id(), nome, nome_completo, email, funcao.codigo,
                                     hash_senha, sal, iteracoes, justificativa)
        self._repo.salvar_cadastro(pedido)
        evento_seguranca(logger, "user_signup_requested", logging.INFO, usuario=nome, funcao=funcao.codigo)
        return pedido

    def cadastros_pendentes(self):
        return [p for p in self._repo.cadastros() if p.status == PENDENTE]

    # Aprova o cadastro e cria o usuario
    def aprovar_cadastro(self, ator, pedido_id, funcao=None):
        self.exigir(ator, Autorizacao.APROVAR_CADASTRO)
        pedido = self._pedido_cadastro_pendente(pedido_id)
        funcao = Funcao.de_codigo(funcao or pedido.funcao)
        if funcao is Funcao.ADMINISTRADOR:
            self._exigir_administrador(ator, "atribuir a função Administrador")
        if self._repo.obter(pedido.usuario) is not None:
            raise ErroValidacao("usuario", "o nome de usuário já foi ocupado; recuse esta solicitação")
        usuario = Usuario(pedido.usuario, pedido.hash_senha, pedido.sal, pedido.iteracoes,
                          nome_completo=pedido.nome_completo, email=pedido.email, funcoes=[funcao.codigo])
        self._repo.salvar(usuario)
        self._decidir(pedido, ator, APROVADA, f"função {funcao.rotulo}")
        self._repo.salvar_cadastro(pedido)
        evento_seguranca(logger, "user_created", logging.INFO, usuario=usuario.nome,
                         aprovado_por=ator, funcoes=[funcao.codigo])
        return usuario

    # Recusa o cadastro
    def recusar_cadastro(self, ator, pedido_id, motivo=""):
        self.exigir(ator, Autorizacao.APROVAR_CADASTRO)
        pedido = self._pedido_cadastro_pendente(pedido_id)
        self._decidir(pedido, ator, RECUSADA, validar_texto_livre("motivo", motivo, TAMANHO_JUSTIFICATIVA))
        pedido.hash_senha = pedido.sal = ""
        self._repo.salvar_cadastro(pedido)
        evento_seguranca(logger, "user_signup_rejected", logging.INFO, usuario=pedido.usuario, recusado_por=ator)
        return pedido

    def _pedido_cadastro_pendente(self, pedido_id):
        pedido = self._repo.obter_cadastro(pedido_id)
        if pedido is None or pedido.status != PENDENTE:
            raise ErroValidacao("solicitacao", "solicitação não encontrada ou já decidida")
        return pedido

    @staticmethod
    def _decidir(pedido, ator, status, motivo=""):
        pedido.status, pedido.decidida_por, pedido.decidida_em, pedido.motivo = status, ator, agora(), motivo

    # Admin cria usuario direto
    def criar_usuario(self, ator, usuario, senha, nome_completo, email, funcoes):
        self.exigir(ator, Autorizacao.CRIAR_USUARIO)
        funcoes = [Funcao.de_codigo(f) for f in funcoes]
        if not funcoes:
            raise ErroValidacao("funcao", "escolha ao menos uma função")
        if Funcao.ADMINISTRADOR in funcoes:
            self._exigir_administrador(ator, "atribuir a função Administrador")
        nome_completo = validar_texto("nome", nome_completo)
        email = validar_email(email)
        if any(u.email == email for u in self._repo.listar()):
            raise ErroValidacao("email", "já existe uma conta com este e-mail")
        novo = self._auth.criar_usuario(usuario, senha, nome_completo=nome_completo, email=email,
                                        funcoes=[f.codigo for f in funcoes])
        evento_seguranca(logger, "privilege_permissions_changed", logging.INFO, usuario=novo.nome,
                         por=ator, de=[], para=novo.funcoes)
        return novo

    # Autorizacoes que o usuario ainda pode pedir
    def solicitaveis_para(self, nome):
        usuario = self.usuario(nome)
        possui = usuario.autorizacoes()
        em_andamento = {c for p in self.pedidos_de(nome) if p.status == PENDENTE for c in p.autorizacoes}
        return [a for a in Autorizacao if a.solicitavel and a not in possui and a.codigo not in em_andamento]

    # Pedido de autorizacao (pede a senha)
    def solicitar_autorizacoes(self, nome, senha, codigos, justificativa=""):
        if not codigos:
            raise ErroValidacao("autorizacao", "marque ao menos uma autorização")
        self._auth.autenticar(nome, senha)
        pedidas = [Autorizacao.de_codigo(c) for c in codigos]
        permitidas = set(self.solicitaveis_para(nome))
        invalidas = [a.rotulo for a in pedidas if a not in permitidas]
        if invalidas:
            raise ErroValidacao("autorizacao", "não podem ser solicitadas: " + ", ".join(invalidas))
        pedido = SolicitacaoAutorizacao(self._repo.proximo_id(), self.usuario(nome).nome,
                                        [a.codigo for a in pedidas],
                                        validar_texto_livre("justificativa", justificativa, TAMANHO_JUSTIFICATIVA))
        self._repo.salvar_pedido(pedido)
        evento_seguranca(logger, "authz_requested", logging.INFO, usuario=pedido.usuario,
                         autorizacoes=pedido.autorizacoes)
        return pedido

    def pedidos_de(self, nome):
        return [p for p in self._repo.pedidos() if p.usuario.lower() == (nome or "").lower()]

    def pedidos_pendentes(self):
        return [p for p in self._repo.pedidos() if p.status == PENDENTE]

    # Aprova o pedido de autorizacao
    def aprovar_autorizacao(self, ator, pedido_id):
        self.exigir(ator, Autorizacao.APROVAR_AUTORIZACAO)
        pedido = self._pedido_pendente(pedido_id)
        if pedido.usuario.lower() == ator.lower():
            raise ErroValidacao("solicitacao", "ninguém pode aprovar o próprio pedido (segregação de funções)")
        aprovador = self.usuario(ator)
        pedidas = [Autorizacao.de_codigo(c) for c in pedido.autorizacoes]
        faltando = [a.rotulo for a in pedidas if not aprovador.pode(a)]
        if faltando:
            raise ErroValidacao("solicitacao", "você não pode conceder o que não possui: " + ", ".join(faltando))
        if any(not a.solicitavel for a in pedidas):
            raise ErroValidacao("solicitacao",
                                f"autorizações do grupo {GRUPO_ADMINISTRACAO} não são concedidas por pedido")
        alvo = self.usuario(pedido.usuario)
        antes = list(alvo.autorizacoes_extras)
        alvo.autorizacoes_extras = sorted(set(antes) | set(pedido.autorizacoes))
        self._repo.salvar(alvo)
        self._decidir(pedido, ator, APROVADA)
        self._repo.salvar_pedido(pedido)
        evento_seguranca(logger, "privilege_permissions_changed", logging.INFO, usuario=alvo.nome,
                         por=ator, de=antes, para=alvo.autorizacoes_extras)
        return pedido

    # Recusa o pedido de autorizacao
    def recusar_autorizacao(self, ator, pedido_id, motivo=""):
        self.exigir(ator, Autorizacao.APROVAR_AUTORIZACAO)
        pedido = self._pedido_pendente(pedido_id)
        self._decidir(pedido, ator, RECUSADA, validar_texto_livre("motivo", motivo, TAMANHO_JUSTIFICATIVA))
        self._repo.salvar_pedido(pedido)
        evento_seguranca(logger, "authz_request_rejected", logging.INFO, usuario=pedido.usuario, por=ator)
        return pedido

    def _pedido_pendente(self, pedido_id):
        pedido = self._repo.obter_pedido(pedido_id)
        if pedido is None or pedido.status != PENDENTE:
            raise ErroValidacao("solicitacao", "solicitação não encontrada ou já decidida")
        return pedido

    # Altera funcoes e autorizacoes do usuario
    def definir_acessos(self, ator, alvo_nome, funcoes, extras):
        self.exigir(ator, Autorizacao.EDITAR_USUARIO)
        alvo = self.usuario(alvo_nome)
        novas_funcoes = sorted({Funcao.de_codigo(f).codigo for f in funcoes})
        novos_extras = sorted({Autorizacao.de_codigo(c).codigo for c in extras})
        admin = Funcao.ADMINISTRADOR.codigo

        mexe_em_admin = (admin in novas_funcoes) != alvo.administrador
        extras_sensiveis = any(not Autorizacao.de_codigo(c).solicitavel
                               for c in set(novos_extras) ^ set(alvo.autorizacoes_extras))
        if mexe_em_admin or extras_sensiveis:
            self._exigir_administrador(ator, "alterar acessos de administração")
        if alvo.administrador and admin not in novas_funcoes:
            if alvo.nome.lower() == ator.lower():
                raise ErroValidacao("funcao", "você não pode remover a função Administrador de si mesmo")
            self._garantir_outro_admin(alvo)
        if not novas_funcoes and not novos_extras:
            raise ErroValidacao("funcao", "o usuário precisa de ao menos uma função ou autorização")

        antes = {"funcoes": alvo.funcoes, "extras": alvo.autorizacoes_extras}
        alvo.funcoes, alvo.autorizacoes_extras = novas_funcoes, novos_extras
        self._repo.salvar(alvo)
        evento_seguranca(logger, "privilege_permissions_changed", logging.INFO, usuario=alvo.nome, por=ator,
                         de=antes, para={"funcoes": novas_funcoes, "extras": novos_extras})
        return alvo

    # Ativa ou desativa a conta
    def definir_ativo(self, ator, alvo_nome, ativo):
        self.exigir(ator, Autorizacao.EDITAR_USUARIO)
        alvo = self.usuario(alvo_nome)
        if alvo.nome.lower() == ator.lower():
            raise ErroValidacao("usuario", "você não pode desativar a própria conta")
        if not ativo and alvo.administrador:
            self._exigir_administrador(ator, "desativar um administrador")
            self._garantir_outro_admin(alvo)
        alvo.ativo = bool(ativo)
        self._repo.salvar(alvo)
        evento_seguranca(logger, "user_updated", logging.INFO, usuario=alvo.nome, por=ator, ativo=alvo.ativo)
        return alvo

    # Nao deixa o sistema ficar sem admin
    def _garantir_outro_admin(self, alvo):
        outros = [u for u in self._repo.listar()
                  if u.ativo and u.administrador and u.nome.lower() != alvo.nome.lower()]
        if not outros:
            raise ErroValidacao("funcao", "o sistema precisa de pelo menos um administrador ativo")
