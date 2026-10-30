import re
from dominio.excecoes import ErroValidacao

_PADRAO_SEM_DIGITOS = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ .'\-]+$")
_PADRAO_COM_DIGITOS = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ0-9 .'_\-]+$")

TAMANHO_MINIMO = 2
TAMANHO_MAXIMO = 60
PROGRESSO_MINIMO = 0
PROGRESSO_MAXIMO = 10


def limpar_espacos(texto):
    return " ".join(str(texto).split())


def validar_texto(campo, valor, permitir_digitos=False, obrigatorio=True,
                  minimo=TAMANHO_MINIMO, maximo=TAMANHO_MAXIMO):
    if valor is None:
        valor = ""
    texto = limpar_espacos(valor)
    if texto == "":
        if obrigatorio:
            raise ErroValidacao(campo, "campo obrigatorio")
        return ""
    if not minimo <= len(texto) <= maximo:
        raise ErroValidacao(campo, f"deve ter entre {minimo} e {maximo} caracteres")
    padrao = _PADRAO_COM_DIGITOS if permitir_digitos else _PADRAO_SEM_DIGITOS
    if not padrao.match(texto):
        regra = "letras, numeros" if permitir_digitos else "apenas letras"
        raise ErroValidacao(campo, f"caracteres invalidos (use {regra}, espaco, - . ')")
    return texto


def validar_texto_livre(campo, valor, maximo=500):
    texto = limpar_espacos(valor or "")
    if len(texto) > maximo:
        raise ErroValidacao(campo, f"maximo de {maximo} caracteres")
    if any(not c.isprintable() for c in texto):
        raise ErroValidacao(campo, "contem caracteres de controle")
    return texto


def validar_progresso(valor):
    if isinstance(valor, bool):
        raise ErroValidacao("progresso", "deve ser um numero inteiro")
    try:
        numero = int(str(valor).strip())
    except (TypeError, ValueError):
        raise ErroValidacao("progresso", "deve ser um numero inteiro") from None
    if not PROGRESSO_MINIMO <= numero <= PROGRESSO_MAXIMO:
        raise ErroValidacao("progresso", f"deve estar entre {PROGRESSO_MINIMO} e {PROGRESSO_MAXIMO}")
    return numero


def validar_id(valor):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ErroValidacao("id", "deve ser um inteiro positivo")
    return valor
