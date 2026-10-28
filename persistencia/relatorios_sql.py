from persistencia.repositorio import RepositorioSQLite

_RESIDUAL = "v.cvss * (10 - v.progresso) / 10.0"


class RelatorioSQL(RepositorioSQLite):
    def __init__(self, ativos=()):
        super().__init__(":memory:")
        for ativo in ativos:
            self.salvar(ativo)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()

    def _consultar(self, sql, parametros=()):
        return [dict(linha) for linha in self._conexao.execute(sql, parametros)]

    def resumo(self):
        linha = self._consultar(
            f"""
            SELECT COUNT(*)                                                   AS total,
                   SUM(CASE WHEN v.progresso < 10 THEN 1 ELSE 0 END)           AS abertas,
                   SUM(CASE WHEN v.progresso < 10 AND v.cvss >= 9 THEN 1 ELSE 0 END) AS criticas,
                   ROUND(AVG(CASE WHEN v.progresso < 10 THEN {_RESIDUAL} END), 2) AS risco_medio,
                   ROUND(MAX(v.cvss), 1)                                       AS cvss_max
            FROM vulnerabilidades v
            """  # noqa: S608 - so constantes internas no f-string
        )[0]
        linha["ativos"] = self._conexao.execute("SELECT COUNT(*) FROM ativos").fetchone()[0]
        for chave in ("total", "abertas", "criticas"):
            linha[chave] = linha[chave] or 0
        linha["risco_medio"] = linha["risco_medio"] or 0.0
        return linha

    def por_severidade(self, somente_abertas=False):
        filtro = "WHERE progresso < 10" if somente_abertas else ""
        return self._consultar(
            f"""
            SELECT severidade, COUNT(*) AS total, ROUND(AVG(cvss), 1) AS cvss_medio
            FROM vulnerabilidades {filtro}
            GROUP BY severidade
            ORDER BY MIN(cvss) DESC
            """  # noqa: S608
        )

    def por_status(self):
        return self._consultar(
            "SELECT status, COUNT(*) AS total FROM vulnerabilidades GROUP BY status ORDER BY total DESC"
        )

    def por_faixa_cvss(self):
        return self._consultar(
            """
            SELECT CAST(cvss AS INTEGER) AS faixa, COUNT(*) AS total
            FROM vulnerabilidades
            GROUP BY faixa
            ORDER BY faixa
            """
        )

    def top_ativos(self, limite=5):
        return self._consultar(
            f"""
            SELECT a.id, a.nome, a.tipo, a.local,
                   COUNT(v.id)                                           AS abertas,
                   SUM(CASE WHEN v.cvss >= 9 THEN 1 ELSE 0 END)          AS criticas,
                   COALESCE(MAX(v.cvss), 0)                              AS cvss_max,
                   ROUND(COALESCE(SUM({_RESIDUAL}), 0), 2)               AS risco_residual
            FROM ativos a
            LEFT JOIN vulnerabilidades v ON v.ativo_id = a.id AND v.progresso < 10
            GROUP BY a.id, a.nome, a.tipo, a.local
            ORDER BY abertas DESC, risco_residual DESC
            LIMIT ?
            """,  # noqa: S608
            (int(limite),),
        )

    def risco_por_local(self):
        return self._consultar(
            f"""
            SELECT a.local,
                   COUNT(DISTINCT a.id)                 AS ativos,
                   COUNT(v.id)                          AS abertas,
                   ROUND(SUM({_RESIDUAL}), 2)           AS risco_residual
            FROM ativos a
            INNER JOIN vulnerabilidades v ON v.ativo_id = a.id
            WHERE v.progresso < 10
            GROUP BY a.local
            HAVING SUM({_RESIDUAL}) > 0
            ORDER BY risco_residual DESC
            """  # noqa: S608
        )

    def por_tipo_de_ativo(self):
        return self._consultar(
            """
            SELECT a.tipo, COUNT(v.id) AS total, ROUND(AVG(v.cvss), 1) AS cvss_medio
            FROM vulnerabilidades v
            JOIN ativos a ON a.id = v.ativo_id
            GROUP BY a.tipo
            ORDER BY total DESC
            """
        )

    def ativos_sem_vulnerabilidades(self):
        return self._consultar(
            """
            SELECT a.id, a.nome, a.tipo
            FROM ativos a
            LEFT JOIN vulnerabilidades v ON v.ativo_id = a.id
            WHERE v.id IS NULL
            ORDER BY a.nome
            """
        )

    def buscar_por_responsavel(self, responsavel):
        return self._consultar(
            """
            SELECT a.nome AS ativo, v.nome, v.cvss, v.progresso
            FROM vulnerabilidades v JOIN ativos a ON a.id = v.ativo_id
            WHERE v.responsavel = ?
            ORDER BY v.cvss DESC
            """,
            (responsavel,),
        )

    def vulnerabilidades_detalhadas(self):
        return self._consultar(
            f"""
            SELECT a.id AS ativo_id, a.nome AS ativo, a.tipo, a.local,
                   v.nome AS vulnerabilidade, v.cvss, v.severidade, v.vetor_cvss,
                   v.responsavel, v.progresso, v.status,
                   ROUND({_RESIDUAL}, 2) AS risco_residual
            FROM vulnerabilidades v
            INNER JOIN ativos a ON a.id = v.ativo_id
            ORDER BY v.cvss DESC, a.nome
            """  # noqa: S608
        )
