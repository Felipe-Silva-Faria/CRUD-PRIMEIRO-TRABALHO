from dataclasses import dataclass, replace

import config


def _canal_linear(canal_8bits):
    c = canal_8bits / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(cor_hex):
    cor = cor_hex.lstrip("#")
    if len(cor) != 6:
        raise ValueError(f"cor invalida: {cor_hex!r}")
    r, g, b = (int(cor[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _canal_linear(r) + 0.7152 * _canal_linear(g) + 0.0722 * _canal_linear(b)


def razao_contraste(cor_a, cor_b):
    clara, escura = sorted((luminancia(cor_a), luminancia(cor_b)), reverse=True)
    return round((clara + 0.05) / (escura + 0.05), 2)


def atende_wcag_aa(cor_texto, cor_fundo, texto_grande=False):
    minimo = 3.0 if texto_grande else 4.5
    return razao_contraste(cor_texto, cor_fundo) >= minimo


@dataclass(frozen=True)
class Tema:
    nome: str
    fundo: str
    painel: str
    destaque: str
    destaque_claro: str
    texto: str
    erro: str
    foco: str
    fonte_familia: str = "Segoe UI"
    fonte_tamanho: int = 11

    def fonte(self, delta=0, peso="normal"):
        return (self.fonte_familia, self.fonte_tamanho + delta, peso)

    def com_escala(self, passos):
        tamanho = min(24, max(8, self.fonte_tamanho + passos))
        return replace(self, fonte_tamanho=tamanho)

    def problemas_de_contraste(self):
        pares = {
            "texto/fundo": (self.texto, self.fundo),
            "texto/painel": (self.texto, self.painel),
            "texto/botao": (self.texto, self.destaque),
            "erro/painel": (self.erro, self.painel),
        }
        return [nome for nome, (t, f) in pares.items() if not atende_wcag_aa(t, f)]


TEMA_PADRAO = Tema(
    nome="Violeta",
    fundo=config.COR_FUNDO,
    painel=config.COR_PAINEL,
    destaque=config.COR_VIOLETA,
    destaque_claro=config.COR_VIOLETA_CLARO,
    texto=config.COR_TEXTO,
    erro="#ff8a8a",
    foco="#ffd84d",
)

TEMA_ALTO_CONTRASTE = Tema(
    nome="Alto contraste",
    fundo="#000000",
    painel="#000000",
    destaque="#1a1a1a",
    destaque_claro="#ffff00",
    texto="#ffffff",
    erro="#ff6b6b",
    foco="#00ffff",
    fonte_tamanho=13,
)

TEMAS = (TEMA_PADRAO, TEMA_ALTO_CONTRASTE)
