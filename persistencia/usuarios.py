import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from dominio.excecoes import ErroPersistencia
from dominio.permissoes import Funcao, autorizacoes_efetivas

ARQUIVO_USUARIOS = "usuarios.json"
VERSAO = 2

PENDENTE = "pendente"
APROVADA = "aprovada"
RECUSADA = "recusada"


def agora():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _filtrar(cls, dados):
    return {k: dados[k] for k in cls.__dataclass_fields__ if k in dados}


# Dados do usuario
@dataclass
class Usuario:
    nome: str
    hash_senha: str
    sal: str
    iteracoes: int
    nome_completo: str = ""
    email: str = ""
    funcoes: list = field(default_factory=list)
    autorizacoes_extras: list = field(default_factory=list)
    ativo: bool = True
    criado_em: str = field(default_factory=agora)

    @property
    def papel(self):
        if not self.funcoes:
            return "Sem função"
        return ", ".join(Funcao.de_codigo(f).rotulo for f in self.funcoes)

    @property
    def administrador(self):
        return Funcao.ADMINISTRADOR.codigo in self.funcoes

    def autorizacoes(self):
        if not self.ativo:
            return set()
        return autorizacoes_efetivas(self.funcoes, self.autorizacoes_extras)

    def pode(self, autorizacao):
        return autorizacao in self.autorizacoes()

    def to_dict(self):
        return asdict(self)

    # Converte o formato antigo (papel admin)
    @classmethod
    def from_dict(cls, dados):
        dados = dict(dados)
        if "funcoes" not in dados:
            dados["funcoes"] = [Funcao.ADMINISTRADOR.codigo] if dados.get("papel") == "admin" else []
        return cls(**_filtrar(cls, dados))


# Ficha de solicitacao de cadastro
@dataclass
class SolicitacaoCadastro:
    id: int
    usuario: str
    nome_completo: str
    email: str
    funcao: str
    hash_senha: str
    sal: str
    iteracoes: int
    justificativa: str = ""
    criada_em: str = field(default_factory=agora)
    status: str = PENDENTE
    decidida_por: str = ""
    decidida_em: str = ""
    motivo: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, dados):
        return cls(**_filtrar(cls, dados))


# Pedido de autorizacao
@dataclass
class SolicitacaoAutorizacao:
    id: int
    usuario: str
    autorizacoes: list
    justificativa: str = ""
    criada_em: str = field(default_factory=agora)
    status: str = PENDENTE
    decidida_por: str = ""
    decidida_em: str = ""
    motivo: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, dados):
        return cls(**_filtrar(cls, dados))


# Salva usuarios e solicitacoes no usuarios.json
class RepositorioUsuariosJSON:
    def __init__(self, caminho=ARQUIVO_USUARIOS):
        self.caminho = Path(caminho)
        self._usuarios = {}
        self._cadastros = {}
        self._pedidos = {}
        if self.caminho.exists():
            self._carregar()

    def _carregar(self):
        try:
            conteudo = json.loads(self.caminho.read_text(encoding="utf-8"))
            if isinstance(conteudo, list):
                conteudo = {"usuarios": conteudo}
            for dados in conteudo.get("usuarios", []):
                usuario = Usuario.from_dict(dados)
                self._usuarios[usuario.nome.lower()] = usuario
            for dados in conteudo.get("solicitacoes_cadastro", []):
                pedido = SolicitacaoCadastro.from_dict(dados)
                self._cadastros[pedido.id] = pedido
            for dados in conteudo.get("solicitacoes_autorizacao", []):
                pedido = SolicitacaoAutorizacao.from_dict(dados)
                self._pedidos[pedido.id] = pedido
        except (OSError, json.JSONDecodeError, TypeError, AttributeError) as erro:
            raise ErroPersistencia(f"{self.caminho} ilegivel: {erro}") from erro

    def obter(self, nome):
        return self._usuarios.get((nome or "").strip().lower())

    def salvar(self, usuario):
        self._usuarios[usuario.nome.lower()] = usuario
        self._gravar()
        return usuario

    def listar(self):
        return sorted(self._usuarios.values(), key=lambda u: u.nome.lower())

    def quantidade(self):
        return len(self._usuarios)

    def salvar_cadastro(self, pedido):
        self._cadastros[pedido.id] = pedido
        self._gravar()
        return pedido

    def cadastros(self):
        return sorted(self._cadastros.values(), key=lambda p: p.id)

    def obter_cadastro(self, pedido_id):
        return self._cadastros.get(int(pedido_id))

    def salvar_pedido(self, pedido):
        self._pedidos[pedido.id] = pedido
        self._gravar()
        return pedido

    def pedidos(self):
        return sorted(self._pedidos.values(), key=lambda p: p.id)

    def obter_pedido(self, pedido_id):
        return self._pedidos.get(int(pedido_id))

    def proximo_id(self):
        existentes = [*self._cadastros, *self._pedidos]
        return max(existentes, default=0) + 1

    # Grava o arquivo
    def _gravar(self):
        conteudo = {
            "versao": VERSAO,
            "usuarios": [u.to_dict() for u in self._usuarios.values()],
            "solicitacoes_cadastro": [p.to_dict() for p in self._cadastros.values()],
            "solicitacoes_autorizacao": [p.to_dict() for p in self._pedidos.values()],
        }
        pasta = self.caminho.parent if str(self.caminho.parent) else Path(".")
        pasta.mkdir(parents=True, exist_ok=True)
        descritor, temporario = tempfile.mkstemp(dir=pasta, prefix=".tmp_", suffix=".json")
        try:
            with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
                json.dump(conteudo, arquivo, indent=2, ensure_ascii=False)
            os.replace(temporario, self.caminho)
        except OSError as erro:
            Path(temporario).unlink(missing_ok=True)
            raise ErroPersistencia(f"falha ao gravar {self.caminho}: {erro}") from erro


# Versao em memoria para os testes
class RepositorioUsuariosMemoria(RepositorioUsuariosJSON):
    def __init__(self):
        self._usuarios = {}
        self._cadastros = {}
        self._pedidos = {}

    def _gravar(self):
        pass
