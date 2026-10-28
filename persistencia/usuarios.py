import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from dominio.excecoes import ErroPersistencia

ARQUIVO_USUARIOS = "usuarios.json"


@dataclass
class Usuario:
    nome: str
    hash_senha: str
    sal: str
    iteracoes: int
    papel: str = "admin"

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, dados):
        return cls(**{k: dados[k] for k in cls.__dataclass_fields__ if k in dados})


class RepositorioUsuariosJSON:
    def __init__(self, caminho=ARQUIVO_USUARIOS):
        self.caminho = Path(caminho)
        self._usuarios = {}
        if self.caminho.exists():
            try:
                for dados in json.loads(self.caminho.read_text(encoding="utf-8")):
                    usuario = Usuario.from_dict(dados)
                    self._usuarios[usuario.nome.lower()] = usuario
            except (OSError, json.JSONDecodeError, TypeError) as erro:
                raise ErroPersistencia(f"{self.caminho} ilegivel: {erro}") from erro

    def obter(self, nome):
        return self._usuarios.get((nome or "").strip().lower())

    def salvar(self, usuario):
        self._usuarios[usuario.nome.lower()] = usuario
        self._gravar()
        return usuario

    def quantidade(self):
        return len(self._usuarios)

    def _gravar(self):
        pasta = self.caminho.parent if str(self.caminho.parent) else Path(".")
        pasta.mkdir(parents=True, exist_ok=True)
        descritor, temporario = tempfile.mkstemp(dir=pasta, prefix=".tmp_", suffix=".json")
        try:
            with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
                json.dump([u.to_dict() for u in self._usuarios.values()], arquivo, indent=2)
            os.replace(temporario, self.caminho)
        except OSError as erro:
            Path(temporario).unlink(missing_ok=True)
            raise ErroPersistencia(f"falha ao gravar {self.caminho}: {erro}") from erro


class RepositorioUsuariosMemoria(RepositorioUsuariosJSON):
    def __init__(self):
        self._usuarios = {}

    def _gravar(self):
        pass
