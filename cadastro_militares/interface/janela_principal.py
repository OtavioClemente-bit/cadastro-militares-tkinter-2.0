import tkinter as tk
from tkinter import messagebox

from interface.cadastro_militar import abrir_cadastro
from interface.listar_militares import abrir_listagem
from interface.boletim import abrir_boletim
from interface.soldos import abrir_soldos
from interface.auxilio_transporte import abrir_auxilio_transporte
from relatorios.relacao_pessoal import gerar_relacao_pessoal
from interface.gratificacao import abrir_gratificacao_representacao

# ---------- Paleta/estilo ----------
BG_APP = "#e3f2fd"
FG_TIT = "#ffffff"
HEADER_BG = "#1565c0"
CARD_BG = "#ffffff"
BORDER = "#e1e8f5"
BTN_BG = "#1976d2"
BTN_BG_HOVER = "#1e88e5"
BTN_BG_DANGER = "#e53935"
BTN_BG_DANGER_HOVER = "#c62828"
BTN_FG = "white"

def iniciar_sistema():
    janela = tk.Tk()
    janela.title("Sistema de Cadastro de Militares")
    janela.configure(bg=BG_APP)
    janela.resizable(False, False)

    # Centraliza a janela
    w, h = 900, 740
    janela.update_idletasks()
    sw, sh = janela.winfo_screenwidth(), janela.winfo_screenheight()
    x, y = (sw - w) // 2, (sh - h) // 2
    janela.geometry(f"{w}x{h}+{x}+{y}")

    # ---------------- Header ----------------
    header = tk.Frame(janela, bg=HEADER_BG, height=120)
    header.pack(fill="x")
    header.grid_propagate(False)

    icon = tk.Label(header, text="🛡️", bg=HEADER_BG, fg=FG_TIT, font=("Segoe UI Emoji", 42))
    title = tk.Label(header, text="SISTEMA DE CADASTRO MILITAR",
                     font=("Segoe UI", 22, "bold"), bg=HEADER_BG, fg=FG_TIT)
    subtitle = tk.Label(header,
                        text="Gestão de militares • Boletins • Soldos • Auxílio Transporte • Relatórios",
                        font=("Segoe UI", 11), bg=HEADER_BG, fg="#e3f2fd")

    icon.grid(row=0, column=0, rowspan=2, padx=(24, 16), pady=(18, 10), sticky="w")
    title.grid(row=0, column=1, sticky="w", pady=(22, 2))
    subtitle.grid(row=1, column=1, sticky="w")
    header.columnconfigure(1, weight=1)

    # Linha separadora
    tk.Frame(janela, bg="#bbdefb", height=2).pack(fill="x")

    # ---------------- Status var ----------------
    status_var = tk.StringVar(value="Pronto.")

    # ---------------- Card ----------------
    center = tk.Frame(janela, bg=BG_APP)
    center.pack(expand=True, fill="both", padx=26, pady=26)

    card = tk.Frame(center, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
    card.pack(expand=True, fill="both")

    # Conteúdo do card
    tk.Label(card, text="Atalhos rápidos", font=("Segoe UI", 16, "bold"),
             bg=CARD_BG, fg="#0d47a1").pack(pady=(20, 6))
    tk.Label(card, text="Escolha uma ação abaixo ou use os atalhos de teclado.",
             font=("Segoe UI", 10), bg=CARD_BG, fg="#607d8b").pack(pady=(0, 14))

    tk.Frame(card, bg="#e9eef5", height=1).pack(fill="x", padx=24, pady=(0, 16))

    btn_wrap = tk.Frame(card, bg=CARD_BG)
    btn_wrap.pack(padx=20, pady=(0, 8), fill="x")

    # --------------- Helper de botão ---------------
    def make_button(parent, text, emoji, cmd, danger=False, hint=""):
        base_bg = BTN_BG_DANGER if danger else BTN_BG
        hover_bg = BTN_BG_DANGER_HOVER if danger else BTN_BG_HOVER
        btn = tk.Button(
            parent, text=f"{emoji}  {text}", command=cmd,
            font=("Segoe UI", 14), bg=base_bg, fg=BTN_FG,
            activebackground=hover_bg, activeforeground=BTN_FG,
            width=26, height=2, bd=0, cursor="hand2", relief="flat"
        )
        # hover
        btn.bind("<Enter>", lambda _e: (btn.configure(bg=hover_bg), status_var.set(hint or "Pronto.")))
        btn.bind("<Leave>", lambda _e: (btn.configure(bg=base_bg), status_var.set("Pronto.")))
        return btn

    # --------------- Botões ---------------
    botoes = [
        ("Cadastrar Militar", "➕", lambda: abrir_cadastro(), False, "Cadastrar um novo militar (Ctrl+N)"),
        ("Listar Militares", "📋", lambda: abrir_listagem(), False, "Ver/filtrar a lista de militares (Ctrl+L)"),
        ("Boletim", "📄", lambda: abrir_boletim(), False, "Gerar boletim (Ctrl+B)"),
        ("Soldos", "💰", lambda: abrir_soldos(janela), False, "Gerenciar soldos por posto (Ctrl+S)"),
        ("Auxílio Transporte", "🚌", lambda: abrir_auxilio_transporte(janela), False, "Relatório e cálculo do Aux. Transporte (Ctrl+T)"),
        ("Gratificação de Representação", "🏅", lambda: abrir_gratificacao_representacao(janela), False, "2% do soldo por dia + boletim (Ctrl+G)"),
        ("Gerar Relação Pessoal", "🧾", lambda: gerar_relacao_pessoal(janela), False, "Exporta relação no layout do modelo (Ctrl+R)"),
        ("Sair", "❌", janela.destroy, True, "Fechar o sistema (Esc)"),
    ]

    # monta em 2 colunas
    for i, (txt, emj, cmd, danger, hint) in enumerate(botoes):
        r, c = divmod(i, 2)
        make_button(btn_wrap, txt, emj, cmd, danger, hint)\
            .grid(row=r, column=c, padx=12, pady=12, sticky="nsew")

    for c in (0, 1):
        btn_wrap.columnconfigure(c, weight=1)

    # ---------------- Barra de status ----------------
    status = tk.Label(janela, textvariable=status_var, anchor="w",
                      font=("Segoe UI", 9), bg="#eaf3ff", fg="#37474f")
    status.pack(fill="x", side="bottom")

    # ---------------- Menu e Sobre ----------------
    menubar = tk.Menu(janela)

    m_arq = tk.Menu(menubar, tearoff=0)
    m_arq.add_command(label="Cadastrar Militar\t Ctrl+N", command=abrir_cadastro)
    m_arq.add_command(label="Listar Militares\t Ctrl+L", command=abrir_listagem)
    m_arq.add_separator()
    m_arq.add_command(label="Sair\t Esc", command=janela.destroy)
    menubar.add_cascade(label="Arquivo", menu=m_arq)

    m_tools = tk.Menu(menubar, tearoff=0)
    m_tools.add_command(label="Boletim\t Ctrl+B", command=abrir_boletim)
    m_tools.add_command(label="Soldos\t Ctrl+S", command=lambda: abrir_soldos(janela))
    m_tools.add_command(label="Auxílio Transporte\t Ctrl+T", command=lambda: abrir_auxilio_transporte(janela))
    m_tools.add_command(label="Gratificação de Representação\t Ctrl+G", command=lambda: abrir_gratificacao_representacao(janela))
    m_tools.add_command(label="Relação Pessoal\t Ctrl+R", command=lambda: gerar_relacao_pessoal(janela))
    menubar.add_cascade(label="Ferramentas", menu=m_tools)

    def sobre():
        messagebox.showinfo(
            "Sobre",
            "Sistema de Cadastro Militar\n"
            "Versão 1.0\n\n"
            "Atalhos:\n"
            "  Ctrl+N  Cadastrar Militar\n"
            "  Ctrl+L  Listar Militares\n"
            "  Ctrl+B  Boletim\n"
            "  Ctrl+S  Soldos\n"
            "  Ctrl+T  Auxílio Transporte\n"
            "  Ctrl+G  Gratificação de Representação\n"
            "  Ctrl+R  Relação Pessoal\n"
            "  Esc     Sair"
        )
    m_ajuda = tk.Menu(menubar, tearoff=0)
    m_ajuda.add_command(label="Sobre", command=sobre)
    menubar.add_cascade(label="Ajuda", menu=m_ajuda)

    janela.config(menu=menubar)

    # ---------------- Atalhos ----------------
    janela.bind("<Control-n>", lambda e: abrir_cadastro())
    janela.bind("<Control-N>", lambda e: abrir_cadastro())
    janela.bind("<Control-l>", lambda e: abrir_listagem())
    janela.bind("<Control-L>", lambda e: abrir_listagem())
    janela.bind("<Control-b>", lambda e: abrir_boletim())
    janela.bind("<Control-B>", lambda e: abrir_boletim())
    janela.bind("<Control-s>", lambda e: abrir_soldos(janela))
    janela.bind("<Control-S>", lambda e: abrir_soldos(janela))
    janela.bind("<Control-t>", lambda e: abrir_auxilio_transporte(janela))
    janela.bind("<Control-T>", lambda e: abrir_auxilio_transporte(janela))
    janela.bind("<Control-g>", lambda e: abrir_gratificacao_representacao(janela))
    janela.bind("<Control-G>", lambda e: abrir_gratificacao_representacao(janela))
    janela.bind("<Control-r>", lambda e: gerar_relacao_pessoal(janela))
    janela.bind("<Control-R>", lambda e: gerar_relacao_pessoal(janela))
    janela.bind("<Escape>", lambda e: janela.destroy())

    janela.mainloop()
