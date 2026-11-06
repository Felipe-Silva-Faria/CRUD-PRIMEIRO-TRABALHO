import logging
import tkinter as tk
from tkinter import messagebox

from dominio.excecoes import ErroCRUD
from dominio.permissoes import Autorizacao
from interface.moderna import NOME_EXIBICAO, preferencias, tema
from interface.moderna.componentes import AreaRolavel, BarraLateral, Botao, Rotulo, limpar
from interface.moderna.paginas.acessos import PaginaAcessos
from interface.moderna.paginas.ativos import PaginaAtivos
from interface.moderna.paginas.base import mensagem_de
from interface.moderna.paginas.configuracoes import PaginaConfiguracoes
from interface.moderna.paginas.dashboard import PaginaDashboard
from interface.moderna.paginas.detalhes import PaginaDetalhes
from interface.moderna.paginas.login import PaginaLogin
from interface.moderna.paginas.minha_conta import PaginaMinhaConta
from interface.moderna.paginas.nova_vulnerabilidade import PaginaNovaVulnerabilidade
from interface.moderna.paginas.relatorios import PaginaRelatorios
from interface.moderna.paginas.riscos import PaginaRiscos
from interface.moderna.paginas.vulnerabilidades import PaginaVulnerabilidades
from servicos.contas import ErroPermissao
from servicos.eventos import CONEXAO_ALTERADA, DADOS_ALTERADOS
from utilitarios.auditoria import evento_seguranca

logger = logging.getLogger(__name__)

PAGINAS = {
    "dashboard": PaginaDashboard,
    "vulnerabilidades": PaginaVulnerabilidades,
    "nova_vulnerabilidade": PaginaNovaVulnerabilidade,
    "detalhes": PaginaDetalhes,
    "ativos": PaginaAtivos,
    "riscos": PaginaRiscos,
    "relatorios": PaginaRelatorios,
    "configuracoes": PaginaConfiguracoes,
    "acessos": PaginaAcessos,
    "minha_conta": PaginaMinhaConta,
}

PERMISSAO_PAGINA = {
    "dashboard": None,
    "vulnerabilidades": Autorizacao.VER_VULNERABILIDADES,
    "detalhes": Autorizacao.VER_VULNERABILIDADES,
    "ativos": Autorizacao.VER_ATIVOS,
    "riscos": Autorizacao.VER_RISCOS,
    "relatorios": Autorizacao.VER_RELATORIOS,
    "configuracoes": None,
    "acessos": Autorizacao.VER_USUARIOS,
    "minha_conta": None,
}

MENU = [
    ("dashboard", "▦", "Dashboard"),
    ("vulnerabilidades", "⚠", "Vulnerabilidades"),
    ("ativos", "▣", "Ativos"),
    ("riscos", "◈", "Riscos"),
    ("relatorios", "▤", "Relatórios"),
    ("acessos", "⛨", "Acessos"),
    ("minha_conta", "☺", "Minha conta"),
    ("configuracoes", "⚙", "Configurações"),
]
ITEM_DE_MENU = {"nova_vulnerabilidade": "vulnerabilidades", "detalhes": "vulnerabilidades"}


def autorizacao_da_pagina(nome, parametros):
    if nome == "nova_vulnerabilidade":
        return (Autorizacao.EDITAR_VULNERABILIDADE if parametros.get("id_registro")
                else Autorizacao.CRIAR_VULNERABILIDADE)
    return PERMISSAO_PAGINA.get(nome)


class Aplicacao(tk.Tk):
    def __init__(self, painel, autenticacao, eventos, descricao_conexao="", contas=None):
        super().__init__()
        self.painel = painel
        self.autenticacao = autenticacao
        self.contas = contas
        self.eventos = eventos
        self.descricao_conexao = descricao_conexao
        self.preferencias = preferencias.ler()
        self.usuario = None
        self._paginas, self._atual = {}, None
        self.title(NOME_EXIBICAO)
        largura = min(1320, self.winfo_screenwidth() - 60)
        altura = min(820, self.winfo_screenheight() - 100)
        self.geometry(f"{largura}x{altura}")
        self.minsize(min(1000, largura), min(560, altura))
        self.configure(bg=tema.FUNDO)
        tema.configurar_estilos(self)
        self.bind_all("<MouseWheel>", self._rolar_pagina)
        eventos.assinar(DADOS_ALTERADOS, lambda **_: self.after_idle(self._recarregar_atual))
        eventos.assinar(CONEXAO_ALTERADA, lambda **_: self.after_idle(self.atualizar_indicador))
        self.mostrar_login()

    @property
    def nome_usuario(self):
        return self.usuario.nome if self.usuario else ""

    def pode(self, autorizacao):
        if autorizacao is None:
            return self.usuario is not None
        return self.contas is not None and self.contas.pode(self.nome_usuario, autorizacao)

    def exigir(self, autorizacao):
        self.contas.exigir(self.nome_usuario, autorizacao)

    # Menu so com as paginas permitidas
    def _itens_do_menu(self):
        itens = [item for item in MENU if self.pode(PERMISSAO_PAGINA[item[0]])]
        if any(chave == "acessos" for chave, _i, _t in itens):
            itens = [item for item in itens if item[0] != "minha_conta"]
        return itens

    def mostrar_login(self):
        limpar(self)
        self._paginas.clear()
        self._atual = None
        PaginaLogin(self, self).pack(fill="both", expand=True)

    def iniciar_sessao(self, usuario):
        self.usuario = usuario
        limpar(self)
        self._montar_casca()
        self.navegar("dashboard")

    # Atualiza o menu se as autorizacoes mudarem
    def atualizar_usuario(self):
        if self.usuario is None or self.contas is None:
            return
        self.usuario = self.contas.usuario(self.usuario.nome)
        atual = next((n for n, p in self._paginas.items() if p is self._atual), "dashboard")
        self._lateral.destroy()
        self._lateral = BarraLateral(self, self._itens_do_menu(), self.navegar, titulo=NOME_EXIBICAO)
        self._lateral.pack(side="left", fill="y", before=self._separador)
        self._lateral.marcar(ITEM_DE_MENU.get(atual, atual))
        self.atualizar_indicador()

    def _sair(self):
        if messagebox.askyesno("Sair", "Encerrar a sessão?", parent=self):
            self.usuario = None
            self.mostrar_login()

    def _montar_casca(self):
        self._lateral = BarraLateral(self, self._itens_do_menu(), self.navegar, titulo=NOME_EXIBICAO)
        self._lateral.pack(side="left", fill="y")
        self._separador = tk.Frame(self, bg=tema.BORDA, width=1)
        self._separador.pack(side="left", fill="y")
        direita = tk.Frame(self, bg=tema.PAINEL)
        direita.pack(side="left", fill="both", expand=True)

        barra = tk.Frame(direita, bg=tema.PAINEL, height=60)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        busca = tk.Frame(barra, bg=tema.CARTAO_ALTO, highlightthickness=1, highlightbackground=tema.BORDA)
        busca.pack(side="left", padx=24, pady=12)
        Rotulo(busca, " ⌕ ", tema.F_NEGRITO, tema.TEXTO_SUAVE).pack(side="left")
        self._busca = tk.Entry(busca, bg=tema.CARTAO_ALTO, fg=tema.TEXTO, relief="flat",
                               insertbackground=tema.TEXTO, font=tema.F_NORMAL, width=46)
        self._busca.pack(side="left", ipady=5, padx=(0, 8))
        self._busca.bind("<Return>", lambda _e: self.navegar("vulnerabilidades", texto=self._busca.get()))

        Botao(barra, "Sair", self._sair, "secundario", pady=4).pack(side="right", padx=(8, 24))
        usuario = tk.Frame(barra, bg=tema.PAINEL)
        usuario.pack(side="right")
        avatar = tk.Canvas(usuario, width=36, height=36, bg=tema.PAINEL, highlightthickness=0)
        avatar.create_oval(2, 2, 34, 34, fill=tema.VIOLETA, outline="")
        avatar.create_text(18, 18, text=self.usuario.nome[:1].upper(), fill=tema.TEXTO, font=tema.F_NEGRITO)
        avatar.pack(side="left", padx=8)
        textos = tk.Frame(usuario, bg=tema.PAINEL)
        textos.pack(side="left")
        Rotulo(textos, self.usuario.nome, tema.F_NEGRITO).pack(anchor="w")
        self._rotulo_papel = Rotulo(textos, self.usuario.papel, tema.F_PEQUENA, tema.TEXTO_SUAVE)
        self._rotulo_papel.pack(anchor="w")
        self._indicador = Rotulo(barra, "", tema.F_PEQUENA)
        self._indicador.pack(side="right", padx=16)
        self.atualizar_indicador()

        tk.Frame(direita, bg=tema.BORDA, height=1).pack(fill="x")
        self._conteudo = tk.Frame(direita, bg=tema.PAINEL)
        self._conteudo.pack(fill="both", expand=True)

    def atualizar_indicador(self):
        if not hasattr(self, "_indicador") or not self._indicador.winfo_exists():
            return
        if self.descricao_conexao == "local":
            texto, cor = "● Modo local (arquivo)", tema.TEXTO_SUAVE
        elif self.painel.online:
            texto, cor = "● API conectada", tema.VERDE
        else:
            texto, cor = f"● API offline - {self.painel.pendentes} pendente(s)", tema.VERMELHO
        self._indicador.configure(text=texto, fg=cor)
        if self.usuario is not None and hasattr(self, "_rotulo_papel"):
            self._rotulo_papel.configure(text=self.usuario.papel)

    # Troca de pagina (confere a autorizacao)
    def navegar(self, nome, **parametros):
        if self.usuario is None:
            return
        necessaria = autorizacao_da_pagina(nome, parametros)
        if not self.pode(necessaria):
            evento_seguranca(logger, "authz_fail", usuario=self.nome_usuario, pagina=nome,
                             autorizacao=necessaria.codigo if necessaria else "")
            messagebox.showwarning(
                "Acesso negado",
                f"Você não tem a autorização '{necessaria.rotulo}'.\n"
                "Ela pode ser solicitada na página Minha conta.", parent=self)
            return
        pagina = self._paginas.get(nome)
        if pagina is None:
            area = AreaRolavel(self._conteudo)
            classe = PAGINAS[nome]
            pagina = classe(area.interior, self)
            pagina.pack(fill="both", expand=True)
            pagina.area = area
            self._paginas[nome] = pagina
        if self._atual is not None and self._atual is not pagina:
            self._atual.area.pack_forget()
        self._atual = pagina
        pagina.area.pack(fill="both", expand=True)
        self._lateral.marcar(ITEM_DE_MENU.get(nome, nome))
        pagina.atualizar(**parametros)
        self.atualizar_indicador()

    def _rolar_pagina(self, evento):
        if self._atual is not None:
            self._atual.area.rolar(evento)

    def _recarregar_atual(self):
        if self._atual is not None and self._atual.winfo_exists():
            self._atual.recarregar()
        self.atualizar_indicador()

    def report_callback_exception(self, tipo, valor, rastro):
        if isinstance(valor, ErroPermissao):
            messagebox.showwarning("Acesso negado", f"{valor}\nEla pode ser solicitada na página Minha conta.",
                                   parent=self)
        elif isinstance(valor, ErroCRUD):
            messagebox.showerror(NOME_EXIBICAO, mensagem_de(valor), parent=self)
        else:
            logger.error("erro inesperado na interface", exc_info=(tipo, valor, rastro))
            messagebox.showerror(NOME_EXIBICAO, f"Erro inesperado: {valor}\nDetalhes no log.", parent=self)
