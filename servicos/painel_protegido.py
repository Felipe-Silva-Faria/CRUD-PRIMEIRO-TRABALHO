from dominio.permissoes import Autorizacao


# Confere a autorizacao antes de salvar ou excluir
class PainelProtegido:
    def __init__(self, painel, contas, usuario_atual):
        object.__setattr__(self, "_painel", painel)
        object.__setattr__(self, "_contas", contas)
        object.__setattr__(self, "_usuario_atual", usuario_atual)

    def _exigir(self, autorizacao):
        self._contas.exigir(self._usuario_atual(), autorizacao)

    def pode(self, autorizacao):
        return self._contas.pode(self._usuario_atual(), autorizacao)

    def salvar_ativo(self, dados, ativo_id=None):
        self._exigir(Autorizacao.CRIAR_ATIVO if ativo_id is None else Autorizacao.EDITAR_ATIVO)
        return self._painel.salvar_ativo(dados, ativo_id)

    def remover_ativo(self, ativo_id):
        self._exigir(Autorizacao.EXCLUIR_ATIVO)
        return self._painel.remover_ativo(ativo_id)

    def salvar_vulnerabilidade(self, ativo_id, dados_vul, id_registro=None):
        self._exigir(Autorizacao.CRIAR_VULNERABILIDADE if id_registro is None
                     else Autorizacao.EDITAR_VULNERABILIDADE)
        return self._painel.salvar_vulnerabilidade(ativo_id, dados_vul, id_registro)

    def remover_vulnerabilidade(self, id_registro):
        self._exigir(Autorizacao.EXCLUIR_VULNERABILIDADE)
        return self._painel.remover_vulnerabilidade(id_registro)

    def adicionar_dependencia(self, origem, destino, peso):
        self._exigir(Autorizacao.GERENCIAR_DEPENDENCIAS)
        return self._painel.adicionar_dependencia(origem, destino, peso)

    def remover_dependencia(self, origem, destino):
        self._exigir(Autorizacao.GERENCIAR_DEPENDENCIAS)
        return self._painel.remover_dependencia(origem, destino)

    def __getattr__(self, nome):
        return getattr(self._painel, nome)

    def __setattr__(self, nome, valor):
        setattr(self._painel, nome, valor)
