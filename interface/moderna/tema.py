from tkinter import ttk

from config import COR_VIOLETA, COR_VIOLETA_CLARO

FUNDO = "#0b0a12"
PAINEL = "#110f19"
CARTAO = "#17141f"
CARTAO_ALTO = "#1e1a2a"
BORDA = "#2b2540"
VIOLETA = COR_VIOLETA
VIOLETA_CLARO = COR_VIOLETA_CLARO
VIOLETA_HOVER = "#8b5cf6"
VIOLETA_ESCURO = "#2e1065"
TEXTO = "#ece9f7"
TEXTO_SUAVE = "#9b96b3"
TEXTO_APAGADO = "#6b6585"
VERDE = "#22c55e"
VERMELHO = "#ef4444"

CORES_SEVERIDADE = {"Crítica": "#e5484d", "Alta": "#f76b15", "Média": "#f5a524",
                    "Baixa": "#8b7cf6", "Nenhuma": "#6b6585"}
ORDEM_SEVERIDADE = ["Crítica", "Alta", "Média", "Baixa", "Nenhuma"]

FAMILIA = "Segoe UI"
F_TITULO = (FAMILIA, 18, "bold")
F_SUBTITULO = (FAMILIA, 10)
F_NORMAL = (FAMILIA, 10)
F_NEGRITO = (FAMILIA, 10, "bold")
F_PEQUENA = (FAMILIA, 9)
F_METRICA = (FAMILIA, 24, "bold")
F_DESTAQUE = (FAMILIA, 26, "bold")


def cor_severidade(rotulo):
    return CORES_SEVERIDADE.get(rotulo, TEXTO_SUAVE)


def cor_progresso(progresso):
    return VERMELHO if progresso == 0 else VERDE if progresso == 10 else CORES_SEVERIDADE["Média"]


def misturar(cor, fundo=CARTAO, alfa=0.25):
    c = [int(cor[i:i + 2], 16) for i in (1, 3, 5)]
    f = [int(fundo[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a * alfa + b * (1 - alfa)):02x}" for a, b in zip(c, f))


def configurar_estilos(raiz):
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    estilo.configure(".", background=PAINEL, foreground=TEXTO, font=F_NORMAL,
                     fieldbackground=CARTAO_ALTO, bordercolor=BORDA)
    estilo.configure("Treeview", background=CARTAO, fieldbackground=CARTAO, foreground=TEXTO,
                     rowheight=30, borderwidth=0, font=F_NORMAL)
    estilo.map("Treeview", background=[("selected", VIOLETA_ESCURO)], foreground=[("selected", TEXTO)])
    estilo.configure("Treeview.Heading", background=CARTAO_ALTO, foreground=TEXTO_SUAVE,
                     relief="flat", font=F_NEGRITO, padding=(8, 6))
    estilo.map("Treeview.Heading", background=[("active", BORDA)])
    estilo.configure("TNotebook", background=PAINEL, borderwidth=0)
    estilo.configure("TNotebook.Tab", background=PAINEL, foreground=TEXTO_SUAVE, padding=(16, 8), borderwidth=0)
    estilo.map("TNotebook.Tab", background=[("selected", CARTAO_ALTO)],
               foreground=[("selected", VIOLETA_CLARO)])
    for widget in ("TCombobox", "TSpinbox"):
        estilo.configure(widget, fieldbackground=CARTAO_ALTO, background=CARTAO_ALTO, foreground=TEXTO,
                         arrowcolor=VIOLETA_CLARO, bordercolor=BORDA, lightcolor=BORDA, darkcolor=BORDA, padding=6)
        estilo.map(widget, fieldbackground=[("readonly", CARTAO_ALTO)], foreground=[("readonly", TEXTO)])
    raiz.option_add("*TCombobox*Listbox.background", CARTAO_ALTO)
    raiz.option_add("*TCombobox*Listbox.foreground", TEXTO)
    raiz.option_add("*TCombobox*Listbox.selectBackground", VIOLETA)
    estilo.configure("Violeta.Horizontal.TProgressbar", troughcolor=CARTAO_ALTO, background=VIOLETA,
                     bordercolor=CARTAO_ALTO, lightcolor=VIOLETA, darkcolor=VIOLETA)
    estilo.configure("Vertical.TScrollbar", background=CARTAO_ALTO, troughcolor=CARTAO,
                     arrowcolor=TEXTO_SUAVE, bordercolor=CARTAO)
    for widget in ("TCheckbutton", "TRadiobutton"):
        estilo.configure(widget, background=CARTAO, foreground=TEXTO)
        estilo.map(widget, background=[("active", CARTAO)])
    return estilo
