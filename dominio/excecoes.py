class ErroCRUD(Exception):
    pass


class ErroValidacao(ErroCRUD):
    def __init__(self, campo, mensagem):
        self.campo = campo
        self.mensagem = mensagem
        super().__init__(f"{campo}: {mensagem}")


class AtivoNaoEncontrado(ErroCRUD):
    def __init__(self, ativo_id):
        self.ativo_id = ativo_id
        super().__init__(f"Ativo {ativo_id} nao encontrado")


class ErroPersistencia(ErroCRUD):
    pass


class ApiIndisponivel(ErroCRUD):
    pass


class FilaVaziaError(IndexError):
    pass
