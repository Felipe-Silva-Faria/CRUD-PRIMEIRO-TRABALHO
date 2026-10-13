import os
from typing import List, Optional

from fastapi import FastAPI, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from dominio.enums import Severidade
from dominio.excecoes import AtivoNaoEncontrado, ErroPersistencia, ErroValidacao
from persistencia.repositorio import RepositorioJsonLines, RepositorioMemoria, RepositorioSQLite
from servicos.servico_ativos import CHAVES_ORDENACAO, ServicoAtivos
from utilitarios.funcional import por_severidade_minima, por_texto, por_tipo


class VulnerabilidadeEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    severidade: str
    responsavel: str = ""
    tratamento: str = ""
    progresso: int = Field(default=0, ge=0, le=10)
    status: Optional[str] = None

    @field_validator("severidade")
    @classmethod
    def severidade_valida(cls, valor):
        try:
            return Severidade.de_valor(valor).rotulo
        except ValueError as erro:
            raise ValueError("use Baixa, Média, Alta ou Crítica") from erro


class AtivoEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=60)
    tipo: str
    local: str = Field(min_length=2, max_length=60)
    vulnerabilidades: List[VulnerabilidadeEntrada] = []


class VulnerabilidadeSaida(BaseModel):
    nome: str
    severidade: str
    responsavel: str
    tratamento: str
    progresso: int
    status: str


class AtivoSaida(BaseModel):
    id: int
    nome: str
    tipo: str
    local: str
    vulnerabilidades: List[VulnerabilidadeSaida]
    risco: float
    recomendacao: str


def _saida(ativo):
    return AtivoSaida(**ativo.to_dict(), risco=ativo.risco_total(), recomendacao=ativo.recomendacao())


def repositorio_padrao():
    tipo = os.getenv("CRUD_REPOSITORIO", "sqlite")
    if tipo == "memoria":
        return RepositorioMemoria()
    if tipo == "jsonl":
        return RepositorioJsonLines(os.getenv("CRUD_ARQUIVO", "banco_api.jsonl"))
    return RepositorioSQLite(os.getenv("CRUD_ARQUIVO", "banco_api.db"))


def criar_app(servico=None):
    servico = servico or ServicoAtivos(repositorio_padrao())
    app = FastAPI(title="CRUD Ativos de TI", version="2.0.0")

    @app.exception_handler(AtivoNaoEncontrado)
    async def _nao_encontrado(request: Request, erro: AtivoNaoEncontrado):
        return JSONResponse(status_code=404, content={"detail": str(erro)})

    @app.exception_handler(ErroValidacao)
    async def _invalido(request: Request, erro: ErroValidacao):
        return JSONResponse(status_code=422, content={"detail": erro.mensagem, "campo": erro.campo})

    @app.exception_handler(ErroPersistencia)
    async def _persistencia(request: Request, erro: ErroPersistencia):
        return JSONResponse(status_code=503, content={"detail": "armazenamento indisponivel"})

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ativos", response_model=List[AtivoSaida])
    def listar(
        tipo: Optional[str] = None,
        busca: Optional[str] = Query(None, min_length=1, description="trecho do nome ou local"),
        severidade_minima: Optional[str] = None,
        ordenar_por: Optional[str] = Query(None, description=f"um de {sorted(CHAVES_ORDENACAO)}"),
        ordem: str = Query("asc", pattern="^(asc|desc)$"),
        limite: int = Query(100, ge=1, le=1000),
        deslocamento: int = Query(0, ge=0),
    ):
        predicados = []
        if tipo:
            predicados.append(por_tipo(tipo))
        if busca:
            predicados.append(por_texto(busca))
        if severidade_minima:
            try:
                predicados.append(por_severidade_minima(severidade_minima))
            except ValueError as erro:
                raise ErroValidacao("severidade_minima", str(erro)) from None
        ativos = servico.listar(predicados, ordenar_por=ordenar_por, reverso=(ordem == "desc"))
        return [_saida(a) for a in ativos[deslocamento:deslocamento + limite]]

    @app.get("/ativos/{ativo_id}", response_model=AtivoSaida)
    def obter(ativo_id: int):
        return _saida(servico.obter(ativo_id))

    @app.post("/ativos", response_model=AtivoSaida, status_code=status.HTTP_201_CREATED)
    def cadastrar(entrada: AtivoEntrada, response: Response):
        ativo = servico.cadastrar(entrada.model_dump())
        response.headers["Location"] = f"/ativos/{ativo.id}"
        return _saida(ativo)

    @app.put("/ativos/{ativo_id}", response_model=AtivoSaida)
    def atualizar(ativo_id: int, entrada: AtivoEntrada):
        return _saida(servico.atualizar(ativo_id, entrada.model_dump()))

    @app.delete("/ativos/{ativo_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remover(ativo_id: int):
        servico.remover(ativo_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/ativos/{ativo_id}/vulnerabilidades", response_model=List[VulnerabilidadeSaida])
    def listar_vulnerabilidades(ativo_id: int):
        return [v.to_dict() for v in servico.obter(ativo_id).vulnerabilidades]

    @app.post("/ativos/{ativo_id}/vulnerabilidades", response_model=AtivoSaida,
              status_code=status.HTTP_201_CREATED)
    def adicionar_vulnerabilidade(ativo_id: int, entrada: VulnerabilidadeEntrada):
        return _saida(servico.adicionar_vulnerabilidade(ativo_id, entrada.model_dump()))

    @app.delete("/ativos/{ativo_id}/vulnerabilidades/{indice}", status_code=status.HTTP_204_NO_CONTENT)
    def remover_vulnerabilidade(ativo_id: int, indice: int):
        servico.remover_vulnerabilidade(ativo_id, indice)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/relatorios/risco", response_model=List[AtivoSaida])
    def relatorio_risco(limite: int = Query(10, ge=1, le=100)):
        return [_saida(a) for a in servico.relatorio_risco(limite)]

    app.state.servico = servico
    return app


app = criar_app()
