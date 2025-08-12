# interface/soldos.py
import tkinter as tk
from tkinter import ttk, messagebox
from database.db import listar_postos, obter_soldos_dict, atualizar_soldo_posto

BG_APP = "#e3f2fd"
FG_TIT = "#0d47a1"
BTN_BG = "#1976d2"
BTN_BG_ACTIVE = "#1565c0"
BTN_FG = "white"

ESTILO_BOTAO = {
    "font": ("Segoe UI", 12),
    "bg": BTN_BG,
    "fg": BTN_FG,
    "activebackground": BTN_BG_ACTIVE,
    "activeforeground": BTN_FG,
    "width": 18,
    "height": 1,
    "bd": 0,
    "cursor": "hand2"
}

def abrir_soldos(master):

    win = tk.Toplevel(master)
    win.title("Soldos")
    win.geometry("700x520")
    win.configure(bg=BG_APP)
    win.resizable(False, False)
    win.grab_set()

    tk.Label(win, text="SOLDOS POR POSTO/GRADUAÇÃO",
             font=("Segoe UI", 18, "bold"), bg=BG_APP, fg=FG_TIT).pack(pady=(24, 6))

    topo = tk.Frame(win, bg=BG_APP); topo.pack(pady=6)
    tk.Label(topo, text="Posto:", bg=BG_APP, font=("Segoe UI", 11)).grid(row=0, column=0, sticky="e", padx=6)
    tk.Label(topo, text="Soldo (R$):", bg=BG_APP, font=("Segoe UI", 11)).grid(row=0, column=2, sticky="e", padx=6)

    # lista de postos na ORDEM DO BANCO (id ASC)
    postos = listar_postos()
    posto_var = tk.StringVar(value=postos[0] if postos else "")
    soldo_var = tk.StringVar(value="0,00")

    cb = ttk.Combobox(topo, values=postos, textvariable=posto_var, state="readonly", width=35)
    cb.grid(row=0, column=1, sticky="w", padx=4)
    if postos:
        cb.current(0)

    ent = tk.Entry(topo, textvariable=soldo_var, width=14, font=("Segoe UI", 11))
    ent.grid(row=0, column=3, sticky="w", padx=4)

    def _format_in(v):
        s = str(v).strip().replace("R$", "").replace(" ", "")
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return f"{float(s):.2f}"
        except Exception:
            return "0.00"

    def _carregar_soldo_evt(_=None):
        d = obter_soldos_dict()
        val = d.get(posto_var.get(), 0.0)
        soldo_var.set(f"{val:.2f}".replace(".", ","))

    cb.bind("<<ComboboxSelected>>", _carregar_soldo_evt)
    _carregar_soldo_evt()

    def _salvar():
        if not posto_var.get():
            messagebox.showwarning("Atenção", "Selecione um posto.", parent=win)
            return
        try:
            ok = atualizar_soldo_posto(posto_var.get(), float(_format_in(soldo_var.get())))
            if ok:
                _popular()           # recarrega tabela mantendo ORDEM DO BANCO
                _carregar_soldo_evt()
                messagebox.showinfo("OK", "Soldo atualizado.", parent=win)
            else:
                messagebox.showwarning("Atenção", "Não foi possível atualizar o soldo.", parent=win)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}", parent=win)

    tk.Button(topo, text="Salvar", command=_salvar, **ESTILO_BOTAO).grid(row=0, column=4, padx=8)

    tree = ttk.Treeview(win, columns=("posto", "soldo"), show="headings", height=16)
    tree.heading("posto", text="POSTO/GRADUAÇÃO")
    tree.heading("soldo", text="SOLDO (R$)")
    tree.column("posto", width=420, anchor="w")
    tree.column("soldo", width=160, anchor="center")
    tree.pack(fill="both", expand=True, padx=12, pady=12)

    def _popular():
        tree.delete(*tree.get_children())
        # sempre usa a ordem do catálogo
        postos_ordenados = listar_postos()
        d = obter_soldos_dict()
        for p in postos_ordenados:
            val = d.get(p, 0.0)
            tree.insert("", "end", values=(p, f"{val:.2f}".replace(".", ",")))

        # também atualiza o combobox para refletir eventual inclusão de novos postos
        cb['values'] = postos_ordenados
        if posto_var.get() not in postos_ordenados and postos_ordenados:
            posto_var.set(postos_ordenados[0])
            cb.current(0)
            _carregar_soldo_evt()

    _popular()
