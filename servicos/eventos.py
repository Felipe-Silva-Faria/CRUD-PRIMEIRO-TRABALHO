import logging

logger = logging.getLogger(__name__)

DADOS_ALTERADOS = "dados_alterados"
CONEXAO_ALTERADA = "conexao_alterada"


class BarramentoEventos:
    def __init__(self):
        self._assinantes = {}

    def assinar(self, evento, callback):
        self._assinantes.setdefault(evento, []).append(callback)

        def cancelar():
            if callback in self._assinantes.get(evento, []):
                self._assinantes[evento].remove(callback)

        return cancelar

    def publicar(self, evento, **dados):
        for callback in list(self._assinantes.get(evento, [])):
            try:
                callback(**dados)
            except Exception:  # noqa: BLE001 - um assinante com erro nao derruba os outros
                logger.exception("assinante de '%s' falhou", evento)
