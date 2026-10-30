import hmac
import logging
import os
import time
from fastapi import FastAPI, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from algoritmos.cvss import calcular_cvss, nota_de_rotulo_legado
from dominio.excecoes import AtivoNaoEncontrado, ErroPersistencia, ErroValidacao
from persistencia.repositorio import RepositorioJsonLines, RepositorioMemoria, RepositorioSQLite
from servicos.servico_ativos import CHAVES_ORDENACAO, ServicoAtivos
from utilitarios.auditoria import ativar_log_json, evento_seguranca
from utilitarios.funcional import por_cvss_minimo, por_severidade_minima, por_texto, por_tipo

logger = logging.getLogger("api.app_rest")


class VulnerabilidadeEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    cvss: float | None = Field(default=None, ge=0.0, le=10.0)
    vetor_cvss: str | None = None
    severidade: str | None = None
    responsavel: str = ""
    tratamento: str = ""
    progresso: int = Field(default=0, ge=0, le=10)
    status: str | None = None

    @field_validator("vetor_cvss")
    @classmethod
    def vetor_valido(cls, valor):
        if not valor:
            return None
        try:
            return calcular_cvss(valor).vetor
        except ErroValidacao as erro:
            raise ValueError(erro.mensagem) from erro

    @model_validator(mode="after")
    def exige_cvss(self):
        if self.cvss is None and not self.vetor_cvss:
            if not self.severidade:
                raise ValueError("informe cvss (0.0 a 10.0) ou vetor_cvss (CVSS:3.1/...)")
            try:
                self.cvss = nota_de_rotulo_legado(self.severidade)
            except ErroValidacao as erro:
                raise ValueError(erro.mensagem) from erro
        return self


class AtivoEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=60)
    tipo: str
    local: str = Field(min_length=2, max_length=60)
    vulnerabilidades: list[VulnerabilidadeEntrada] = []


class VulnerabilidadeSaida(BaseModel):
    nome: str
    cvss: float
    vetor_cvss: str
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
    vulnerabilidades: list[VulnerabilidadeSaida]
    maior_cvss: float | None
    risco_proprio: float
    risco: float
    recomendacao: str


def _saida(ativo):
    return AtivoSaida(**ativo.to_dict(), maior_cvss=ativo.maior_cvss(), risco_proprio=ativo.risco_proprio(),
                      risco=ativo.risco_total(), recomendacao=ativo.recomendacao())


def _entrada_para_dict(entrada):
    return entrada.model_dump(exclude={"severidade"} if isinstance(entrada, VulnerabilidadeEntrada) else None)


def _ativo_para_dict(entrada):
    dados = entrada.model_dump(exclude={"vulnerabilidades"})
    dados["vulnerabilidades"] = [_entrada_para_dict(v) for v in entrada.vulnerabilidades]
    return dados


def repositorio_padrao():
    tipo = os.getenv("CRUD_REPOSITORIO", "sqlite")
    if tipo == "memoria":
        return RepositorioMemoria()
    if tipo == "jsonl":
        return RepositorioJsonLines(os.getenv("CRUD_ARQUIVO", "banco_api.jsonl"))
    return RepositorioSQLite(os.getenv("CRUD_ARQUIVO", "banco_api.db"))


def criar_app(servico=None, chave_api=None):
    servico = servico or ServicoAtivos(repositorio_padrao())
    chave_api = os.getenv("CRUD_API_KEY", "") if chave_api is None else chave_api
    app = FastAPI(title="CRUD Ativos de TI", version="3.0.0")

    @app.middleware("http")
    async def _monitorar(request: Request, call_next):
        inicio = time.perf_counter()
        if chave_api and request.url.path != "/health":
            recebida = request.headers.get("X-API-Key", "")
            if not hmac.compare_digest(recebida, chave_api):
                evento_seguranca(logger, "authz_fail", rota=request.url.path,
                                 ip=request.client.host if request.client else "?")
                return JSONResponse(status_code=401, content={"detail": "nao autorizado"})
        resposta = await call_next(request)
        logger.info("requisicao", extra={
            "metodo": request.method, "rota": request.url.path, "status": resposta.status_code,
            "duracao_ms": round((time.perf_counter() - inicio) * 1000, 2)})
        return resposta

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
        return {"status": "ok", "versao": app.version}

    @app.get("/cvss/calcular")
    def calcular(vetor: str = Query(..., min_length=10)):
        resultado = calcular_cvss(vetor)
        return {"vetor": resultado.vetor, "cvss": resultado.nota, "severidade": resultado.faixa,
                "impacto": resultado.impacto, "explorabilidade": resultado.explorabilidade}

    @app.get("/ativos", response_model=list[AtivoSaida])
    def listar(
        tipo: str | None = None,
        busca: str | None = Query(None, min_length=1),
        severidade_minima: str | None = None,
        cvss_minimo: float | None = Query(None, ge=0.0, le=10.0),
        ordenar_por: str | None = Query(None, description=f"um de {sorted(CHAVES_ORDENACAO)}"),
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
        if cvss_minimo is not None:
            predicados.append(por_cvss_minimo(round(cvss_minimo, 1)))
        ativos = servico.listar(predicados, ordenar_por=ordenar_por, reverso=(ordem == "desc"))
        return [_saida(a) for a in ativos[deslocamento:deslocamento + limite]]

    @app.get("/ativos/{ativo_id}", response_model=AtivoSaida)
    def obter(ativo_id: int):
        return _saida(servico.obter(ativo_id))

    @app.post("/ativos", response_model=AtivoSaida, status_code=status.HTTP_201_CREATED)
    def cadastrar(entrada: AtivoEntrada, response: Response):
        ativo = servico.cadastrar(_ativo_para_dict(entrada))
        response.headers["Location"] = f"/ativos/{ativo.id}"
        return _saida(ativo)

    @app.put("/ativos/{ativo_id}", response_model=AtivoSaida)
    def atualizar(ativo_id: int, entrada: AtivoEntrada):
        return _saida(servico.atualizar(ativo_id, _ativo_para_dict(entrada)))

    @app.delete("/ativos/{ativo_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remover(ativo_id: int):
        servico.remover(ativo_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/ativos/{ativo_id}/vulnerabilidades", response_model=list[VulnerabilidadeSaida])
    def listar_vulnerabilidades(ativo_id: int):
        return [v.to_dict() for v in servico.obter(ativo_id).vulnerabilidades]

    @app.post("/ativos/{ativo_id}/vulnerabilidades", response_model=AtivoSaida,
              status_code=status.HTTP_201_CREATED)
    def adicionar_vulnerabilidade(ativo_id: int, entrada: VulnerabilidadeEntrada):
        return _saida(servico.adicionar_vulnerabilidade(ativo_id, _entrada_para_dict(entrada)))

    @app.delete("/ativos/{ativo_id}/vulnerabilidades/{indice}", status_code=status.HTTP_204_NO_CONTENT)
    def remover_vulnerabilidade(ativo_id: int, indice: int):
        servico.remover_vulnerabilidade(ativo_id, indice)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/relatorios/risco", response_model=list[AtivoSaida])
    def relatorio_risco(limite: int = Query(10, ge=1, le=100)):
        return [_saida(a) for a in servico.relatorio_risco(limite)]

    app.state.servico = servico
    return app


if os.getenv("CRUD_LOG_JSON") == "1":
    ativar_log_json()
app = criar_app()
