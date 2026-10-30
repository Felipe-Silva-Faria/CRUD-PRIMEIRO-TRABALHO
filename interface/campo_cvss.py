import tkinter as tk
from tkinter import ttk
from algoritmos.cvss import (
    NOMES_METRICAS,
    ORDEM_METRICAS,
    PESOS,
    calcular_cvss,
    formatar,
    interpretar_entrada,
    interpretar_vetor,
    montar_vetor,
)
from dominio.excecoes import ErroValidacao

OPCOES = {
    "AV": {"N": "Rede", "A": "Rede adjacente", "L": "Local", "P": "Fisico"},
    "AC": {"L": "Baixa", "H": "Alta"},
    "PR": {"N": "Nenhum", "L": "Baixo", "H": "Alto"},
    "UI": {"N": "Nenhuma", "R": "Requerida"},
    "S": {"U": "Inalterado", "C": "Alterado"},
    "C": {"N": "Nenhum", "L": "Baixo", "H": "Alto"},
    "I": {"N": "Nenhum", "L": "Baixo", "H": "Alto"},
    "A": {"N": "Nenhum", "L": "Baixo", "H": "Alto"},
}

PADRAO = {"AV": "N", "AC": "L", "PR": "N", "UI": "N", "S": "U", "C": "N", "I": "N", "A": "N"}


class CampoCVSS(tk.Frame):
    def __init__(self, master, bg="#2b0033", fg="#ffffff", erro="#ff8a8a", **kwargs):
        super().__init__(master, bg=bg, **kwargs)
        self._bg = bg
        self._fg = fg
        self._cor_erro = erro
        self.variavel = tk.StringVar()

        linha = tk.Frame(self, bg=bg)
        linha.pack(fill="x")
        self.entrada = tk.Entry(linha, textvariable=self.variavel, width=48)
        self.entrada.pack(side="left", fill="x", expand=True)
        tk.Button(linha, text="Calculadora", command=self.abrir_calculadora).pack(side="left", padx=(6, 0))

        self.rotulo = tk.Label(self, text="Nota 0.0-10.0 ou vetor CVSS:3.1/...", bg=bg, fg=fg, anchor="w")
        self.rotulo.pack(fill="x")
        self.variavel.trace_add("write", lambda *_: self._atualizar_previa())

    def _atualizar_previa(self):
        texto = self.variavel.get().strip()
        if not texto:
            self.rotulo.config(text="Nota 0.0-10.0 ou vetor CVSS:3.1/...", fg=self._fg)
            return
        try:
            nota, _vetor = interpretar_entrada(texto)
        except ErroValidacao as erro:
            self.rotulo.config(text="\u26a0 " + erro.mensagem, fg=self._cor_erro)
            return
        self.rotulo.config(text="CVSS " + formatar(nota), fg=self._fg)

    def obter(self):
        nota, vetor = interpretar_entrada(self.variavel.get())
        return {"cvss": nota, "vetor_cvss": vetor}

    def definir(self, vulnerabilidade):
        vetor = vulnerabilidade.get("vetor_cvss") or ""
        if vetor:
            self.variavel.set(vetor)
        elif vulnerabilidade.get("cvss") is not None:
            self.variavel.set(str(vulnerabilidade["cvss"]))
        else:
            self.variavel.set("")

    def limpar(self):
        self.variavel.set("")

    def abrir_calculadora(self):
        JanelaCalculadoraCVSS(self, ao_confirmar=self.variavel.set, vetor_inicial=self.variavel.get())


class JanelaCalculadoraCVSS(tk.Toplevel):
    def __init__(self, master, ao_confirmar, vetor_inicial=""):
        super().__init__(master)
        self.title("Calculadora CVSS 3.1")
        self.resizable(False, False)
        self._ao_confirmar = ao_confirmar
        self._caixas = {}

        iniciais = dict(PADRAO)
        if str(vetor_inicial).strip().upper().startswith("CVSS:"):
            try:
                iniciais.update(interpretar_vetor(vetor_inicial)[1])
            except ErroValidacao:
                pass

        for linha, metrica in enumerate(ORDEM_METRICAS):
            tk.Label(self, text=NOMES_METRICAS[metrica], anchor="w").grid(row=linha, column=0, sticky="w", padx=8, pady=3)
            valores = [f"{codigo} - {OPCOES[metrica][codigo]}" for codigo in PESOS[metrica]]
            caixa = ttk.Combobox(self, values=valores, state="readonly", width=24)
            caixa.set(f"{iniciais[metrica]} - {OPCOES[metrica][iniciais[metrica]]}")
            caixa.grid(row=linha, column=1, padx=8, pady=3)
            caixa.bind("<<ComboboxSelected>>", lambda _e: self._recalcular())
            self._caixas[metrica] = caixa

        fim = len(ORDEM_METRICAS)
        self.resultado = tk.Label(self, text="", font=("Arial", 11, "bold"))
        self.resultado.grid(row=fim, column=0, columnspan=2, pady=(8, 2))
        self.vetor = tk.Label(self, text="")
        self.vetor.grid(row=fim + 1, column=0, columnspan=2, padx=8)
        tk.Button(self, text="Usar este vetor", command=self._confirmar).grid(
            row=fim + 2, column=0, columnspan=2, pady=8)

        self.transient(master)
        self.grab_set()
        self._recalcular()

    def _metricas(self):
        return {m: caixa.get().split(" - ")[0] for m, caixa in self._caixas.items()}

    def _recalcular(self):
        resultado = calcular_cvss(montar_vetor(self._metricas()))
        self.resultado.config(text=f"CVSS {formatar(resultado.nota)}  |  impacto {resultado.impacto}  "
                                   f"|  explorabilidade {resultado.explorabilidade}")
        self.vetor.config(text=resultado.vetor)
        self._vetor_atual = resultado.vetor

    def _confirmar(self):
        self._ao_confirmar(self._vetor_atual)
        self.destroy()
