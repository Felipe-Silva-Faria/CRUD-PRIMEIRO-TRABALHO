from tkinter import messagebox
from persistencia import estado
from api.servicos_api import deletar_ativo_api_ou_txt
from ativos.tabela_ativos import atualizar_tabela


# Acao do Botao DELETAR
def deletar_ativo_selecionado():
    selecionado = estado.tabela.selection()
    if not selecionado:
        messagebox.showerror("Erro", "Selecione um ativo na tabela para deletar!")
        return

    ativo = estado.ativos_salvos[selecionado[0]]
    resposta = messagebox.askyesno("Confirmar", f"Tem certeza que deseja deletar o ativo '{ativo['nome']}'?")

    if resposta:
        if deletar_ativo_api_ou_txt(ativo["id"]):
            messagebox.showinfo("Sucesso", "Ativo deletado com sucesso!")
            atualizar_tabela()
        else:
            messagebox.showerror("Erro", "Nao foi possivel deletar o ativo.")
