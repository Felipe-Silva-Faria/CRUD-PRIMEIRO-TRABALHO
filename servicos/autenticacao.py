import hashlib
import hmac
import logging
import secrets
import time

from dominio.excecoes import ErroCRUD, ErroValidacao
from persistencia.usuarios import Usuario
from utilitarios.auditoria import evento_seguranca

logger = logging.getLogger(__name__)

ITERACOES_PADRAO = 600_000
TAMANHO_MIN_SENHA = 8


class ErroAutenticacao(ErroCRUD):
    pass


class ContaBloqueada(ErroAutenticacao):
    def __init__(self, segundos):
        self.segundos = int(segundos)
        super().__init__(f"Conta bloqueada temporariamente. Tente em {self.segundos} s.")


def gerar_hash(senha, sal, iteracoes):
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, iteracoes).hex()


class ServicoAutenticacao:
    def __init__(self, repositorio, iteracoes=ITERACOES_PADRAO, max_tentativas=5,
                 bloqueio_segundos=60, relogio=time.monotonic):
        self._repo = repositorio
        self._iteracoes = iteracoes
        self._max = max_tentativas
        self._bloqueio = bloqueio_segundos
        self._relogio = relogio
        self._falhas = {}
        self._sal_falso = secrets.token_bytes(16)

    def primeiro_acesso(self):
        return self._repo.quantidade() == 0

    def criar_usuario(self, nome, senha, papel="admin"):
        nome = (nome or "").strip()
        if len(nome) < 3 or not nome.replace(".", "").replace("_", "").isalnum():
            raise ErroValidacao("usuario", "minimo 3 caracteres (letras, numeros, '.' ou '_')")
        if len(senha or "") < TAMANHO_MIN_SENHA:
            raise ErroValidacao("senha", f"minimo {TAMANHO_MIN_SENHA} caracteres")
        if self._repo.obter(nome) is not None:
            raise ErroValidacao("usuario", "ja existe")
        sal = secrets.token_bytes(16)
        usuario = Usuario(nome, gerar_hash(senha, sal, self._iteracoes), sal.hex(), self._iteracoes, papel)
        self._repo.salvar(usuario)
        evento_seguranca(logger, "user_created", logging.INFO, usuario=nome)
        return usuario

    def autenticar(self, nome, senha):
        chave = (nome or "").strip().lower()
        self._verificar_bloqueio(chave)
        usuario = self._repo.obter(chave) if chave else None
        if usuario is None:
            gerar_hash(senha or "", self._sal_falso, self._iteracoes)
            valido = False
        else:
            calculado = gerar_hash(senha or "", bytes.fromhex(usuario.sal), usuario.iteracoes)
            valido = hmac.compare_digest(calculado, usuario.hash_senha)
        if not valido:
            self._registrar_falha(chave)
            raise ErroAutenticacao("Usuário ou senha inválidos.")
        self._falhas.pop(chave, None)
        evento_seguranca(logger, "authn_login_success", logging.INFO, usuario=chave)
        return usuario

    def _verificar_bloqueio(self, chave):
        quantidade, quando = self._falhas.get(chave, (0, 0.0))
        if quantidade < self._max:
            return
        restante = self._bloqueio - (self._relogio() - quando)
        if restante > 0:
            raise ContaBloqueada(restante)
        self._falhas.pop(chave, None)

    def _registrar_falha(self, chave):
        quantidade = self._falhas.get(chave, (0, 0.0))[0] + 1
        self._falhas[chave] = (quantidade, self._relogio())
        evento_seguranca(logger, "authn_login_fail", usuario=chave, tentativas=quantidade)
        if quantidade >= self._max:
            evento_seguranca(logger, "authn_login_lock", logging.ERROR, usuario=chave)
