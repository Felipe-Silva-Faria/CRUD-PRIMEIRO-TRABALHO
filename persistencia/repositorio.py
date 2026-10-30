import json
import logging
import os
import sqlite3
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from dominio.entidades import criar_ativo
from dominio.excecoes import AtivoNaoEncontrado, ErroCRUD, ErroPersistencia

logger = logging.getLogger(__name__)


class RepositorioAtivos(ABC):
    @abstractmethod
    def listar(self):
        ...

    @abstractmethod
    def obter(self, ativo_id):
        ...

    @abstractmethod
    def salvar(self, ativo):
        ...

    @abstractmethod
    def remover(self, ativo_id):
        ...

    def existe(self, ativo_id):
        try:
            self.obter(ativo_id)
            return True
        except AtivoNaoEncontrado:
            return False

    def ids(self):
        return {ativo.id for ativo in self.listar()}


class RepositorioMemoria(RepositorioAtivos):
    def __init__(self, ativos=()):
        self._dados = {}
        for ativo in ativos:
            self.salvar(ativo)

    def listar(self):
        return list(self._dados.values())

    def obter(self, ativo_id):
        try:
            return self._dados[ativo_id]
        except KeyError:
            raise AtivoNaoEncontrado(ativo_id) from None

    def salvar(self, ativo):
        if ativo.id is None:
            raise ErroPersistencia("ativo sem id")
        self._dados[ativo.id] = ativo
        return ativo

    def remover(self, ativo_id):
        if self._dados.pop(ativo_id, None) is None:
            raise AtivoNaoEncontrado(ativo_id)

    def ids(self):
        return set(self._dados)


class RepositorioJsonLines(RepositorioMemoria):
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self._linhas_invalidas = []
        super().__init__()
        self._carregar()

    def _carregar(self):
        if not self.caminho.exists():
            return
        with self.caminho.open("r", encoding="utf-8") as arquivo:
            for numero, linha in enumerate(arquivo, start=1):
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    ativo = criar_ativo(json.loads(linha))
                except (json.JSONDecodeError, ErroCRUD) as erro:
                    logger.warning("Linha %d de %s ignorada: %s", numero, self.caminho, erro)
                    self._linhas_invalidas.append(linha)
                    continue
                self._dados[ativo.id] = ativo

    def _gravar(self):
        pasta = self.caminho.parent if str(self.caminho.parent) else Path(".")
        pasta.mkdir(parents=True, exist_ok=True)
        descritor, temporario = tempfile.mkstemp(dir=pasta, prefix=".tmp_", suffix=".jsonl")
        try:
            with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
                for linha in self._linhas_invalidas:
                    arquivo.write(linha + "\n")
                for ativo in self._dados.values():
                    arquivo.write(json.dumps(ativo.to_dict(), ensure_ascii=False) + "\n")
            os.replace(temporario, self.caminho)
        except OSError as erro:
            Path(temporario).unlink(missing_ok=True)
            raise ErroPersistencia(f"falha ao gravar {self.caminho}: {erro}") from erro

    def salvar(self, ativo):
        super().salvar(ativo)
        self._gravar()
        return ativo

    def remover(self, ativo_id):
        super().remover(ativo_id)
        self._gravar()

    def substituir_tudo(self, ativos):
        self._dados = {a.id: a for a in ativos}
        self._gravar()


class RepositorioSQLite(RepositorioAtivos):
    _ESQUEMA = """
    CREATE TABLE IF NOT EXISTS ativos (
        id     INTEGER PRIMARY KEY,
        nome   TEXT NOT NULL,
        tipo   TEXT NOT NULL,
        local  TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS vulnerabilidades (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        ativo_id    INTEGER NOT NULL REFERENCES ativos(id) ON DELETE CASCADE,
        ordem       INTEGER NOT NULL,
        nome        TEXT NOT NULL,
        severidade  TEXT NOT NULL,
        responsavel TEXT NOT NULL DEFAULT '',
        tratamento  TEXT NOT NULL DEFAULT '',
        progresso   INTEGER NOT NULL DEFAULT 0 CHECK (progresso BETWEEN 0 AND 10),
        status      TEXT NOT NULL,
        cvss        REAL CHECK (cvss IS NULL OR cvss BETWEEN 0 AND 10),
        vetor_cvss  TEXT NOT NULL DEFAULT ''
    );
    CREATE INDEX IF NOT EXISTS idx_vul_ativo ON vulnerabilidades(ativo_id);
    """

    _COLUNAS_NOVAS: ClassVar[dict[str, str]] = {
        "cvss": "ALTER TABLE vulnerabilidades ADD COLUMN cvss REAL",
        "vetor_cvss": "ALTER TABLE vulnerabilidades ADD COLUMN vetor_cvss TEXT NOT NULL DEFAULT ''",
    }

    def __init__(self, caminho=":memory:"):
        self._conexao = sqlite3.connect(str(caminho), check_same_thread=False)
        self._conexao.row_factory = sqlite3.Row
        self._conexao.execute("PRAGMA foreign_keys = ON")
        self._conexao.executescript(self._ESQUEMA)
        self._migrar()

    def _migrar(self):
        existentes = {linha["name"] for linha in self._conexao.execute("PRAGMA table_info(vulnerabilidades)")}
        with self._conexao:
            for coluna, comando in self._COLUNAS_NOVAS.items():
                if coluna not in existentes:
                    self._conexao.execute(comando)

    def _montar(self, linha):
        vuls = self._conexao.execute(
            "SELECT nome, severidade, cvss, vetor_cvss, responsavel, tratamento, progresso, status "
            "FROM vulnerabilidades WHERE ativo_id = ? ORDER BY ordem", (linha["id"],)
        ).fetchall()
        dados = dict(linha)
        dados["vulnerabilidades"] = [dict(v) for v in vuls]
        return criar_ativo(dados)

    def listar(self):
        linhas = self._conexao.execute("SELECT id, nome, tipo, local FROM ativos ORDER BY rowid").fetchall()
        return [self._montar(linha) for linha in linhas]

    def obter(self, ativo_id):
        linha = self._conexao.execute(
            "SELECT id, nome, tipo, local FROM ativos WHERE id = ?", (ativo_id,)
        ).fetchone()
        if linha is None:
            raise AtivoNaoEncontrado(ativo_id)
        return self._montar(linha)

    def salvar(self, ativo):
        if ativo.id is None:
            raise ErroPersistencia("ativo sem id")
        dados = ativo.to_dict()
        try:
            with self._conexao:
                self._conexao.execute(
                    "INSERT INTO ativos (id, nome, tipo, local) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET nome=excluded.nome, tipo=excluded.tipo, local=excluded.local",
                    (dados["id"], dados["nome"], dados["tipo"], dados["local"]),
                )
                self._conexao.execute("DELETE FROM vulnerabilidades WHERE ativo_id = ?", (ativo.id,))
                self._conexao.executemany(
                    "INSERT INTO vulnerabilidades (ativo_id, ordem, nome, severidade, cvss, vetor_cvss, "
                    "responsavel, tratamento, progresso, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [(ativo.id, ordem, v["nome"], v["severidade"], v["cvss"], v["vetor_cvss"],
                      v["responsavel"], v["tratamento"], v["progresso"], v["status"])
                     for ordem, v in enumerate(dados["vulnerabilidades"])],
                )
        except sqlite3.Error as erro:
            raise ErroPersistencia(str(erro)) from erro
        return ativo

    def remover(self, ativo_id):
        with self._conexao:
            cursor = self._conexao.execute("DELETE FROM ativos WHERE id = ?", (ativo_id,))
        if cursor.rowcount == 0:
            raise AtivoNaoEncontrado(ativo_id)

    def ids(self):
        return {linha[0] for linha in self._conexao.execute("SELECT id FROM ativos")}

    def fechar(self):
        self._conexao.close()
