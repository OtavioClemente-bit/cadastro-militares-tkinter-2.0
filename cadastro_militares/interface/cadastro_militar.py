import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import unicodedata
import os

from database.db import (
    inserir_militar,
    garantir_catalogos, listar_postos, listar_bancos,
    inserir_posto, inserir_banco
)

# defaults
postos_default = [
    "Capitão", "1º Tenente", "2º Tenente", "Subtenente",
    "1º Sargento", "2º Sargento", "3º Sargento",
    "Cabo Efetivo Profissional", "Soldado Efetivo Profissional", "Soldado Efetivo Variável"
]
bancos_default = [
    "001 - Banco do Brasil S.A", "341 - Itaú Unibanco S.A",
    "033 - Banco Santander (Brasil) S.A", "237 - Banco Bradesco S.A",
    "104 - Caixa Econômica Federal"
]

# ---------- helpers ----------
def ordenar_postos(seq):
    def key(s):
        s = str(s)
        return (0, postos_default.index(s)) if s in postos_default else (1, s.lower())
    return sorted(seq, key=key)

def ordenar_bancos(seq):
    return sorted(seq, key=lambda s: str(s).lower())

def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# ---------- estilos ----------
BG_APP = "#f2f6fb"
CARD_BG = "#ffffff"
BORDER = "#dfe7f3"
TIT = "#103d8f"
ACCENT = "#1565c0"
LBL = "#455a64"

LABEL_MINWIDTH = 220

def abrir_cadastro():
    try:
        garantir_catalogos(postos_default, bancos_default)
    except Exception as e:
        messagebox.showwarning("Aviso", f"Não foi possível garantir catálogos:\n{e}")

    janela = tk.Toplevel()
    janela.title("Cadastro de Militar")
    janela.configure(bg=BG_APP)
    janela.resizable(False, False)

    # centralizar
    w, h = 1000, 720
    janela.update_idletasks()
    sw, sh = janela.winfo_screenwidth(), janela.winfo_screenheight()
    x, y = (sw - w)//2, (sh - h)//2
    janela.geometry(f"{w}x{h}+{x}+{y}")
    janela.grab_set()

    # =========================
    #   CONTAINER COM SCROLL
    # =========================
    container = tk.Frame(janela, bg=BG_APP); container.pack(fill="both", expand=True)
    canvas = tk.Canvas(container, bg=BG_APP, highlightthickness=0)
    sb = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    host = tk.Frame(canvas, bg=BG_APP)
    host.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=host, anchor="nw")
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def _on_mousewheel(event):
        if getattr(event, "num", None) == 4: canvas.yview_scroll(-3, "units"); return
        if getattr(event, "num", None) == 5: canvas.yview_scroll(+3, "units"); return
        if getattr(event, "delta", 0): canvas.yview_scroll(int(-event.delta/40), "units")
    canvas.bind("<Enter>", lambda e: canvas.focus_set())
    canvas.bind("<MouseWheel>", _on_mousewheel); canvas.bind("<Button-4>", _on_mousewheel); canvas.bind("<Button-5>", _on_mousewheel)

    # margem externa
    pad = tk.Frame(host, bg=BG_APP); pad.pack(padx=28, pady=28, fill="both", expand=True)
    # card
    card = tk.Frame(pad, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
    card.pack(fill="both", expand=True, padx=6, pady=6)
    inner = tk.Frame(card, bg=CARD_BG); inner.pack(fill="both", expand=True, padx=26, pady=26)

    # -------- grid MASTER 4 colunas --------
    # [0]=label A (minsize) | [1]=campo A (expande) | [2]=label B (minsize) | [3]=campo B (expande)
    inner.grid_columnconfigure(0, minsize=LABEL_MINWIDTH)
    inner.grid_columnconfigure(1, weight=1)
    inner.grid_columnconfigure(2, minsize=LABEL_MINWIDTH)
    inner.grid_columnconfigure(3, weight=1)

    # =========================
    #   HELPERS DE LAYOUT
    # =========================
    def section_title(row, text):
        bar = tk.Frame(inner, bg=ACCENT, height=22, width=6)
        bar.grid(row=row, column=0, sticky="w", pady=(8, 10))
        tk.Label(inner, text=text, bg=CARD_BG, fg=TIT, font=("Segoe UI", 14, "bold"))\
            .grid(row=row, column=1, columnspan=3, sticky="w", pady=(8, 10), padx=(10,0))
        tk.Frame(inner, bg=BORDER, height=1).grid(row=row+1, column=0, columnspan=4, sticky="we", pady=(0, 10))

    def row_simple_full(row, label, widget=None):
        """label (col0) + campo ocupando 3 colunas (col1..3)"""
        lbl = tk.Label(inner, text=label, bg=CARD_BG, fg=LBL, anchor="e", font=("Segoe UI", 11, "bold"))
        if widget is None: widget = tk.Entry(inner, font=("Segoe UI", 11))
        lbl.grid(row=row, column=0, sticky="e", padx=(0,12), pady=(4,2))
        widget.grid(row=row, column=1, columnspan=3, sticky="we", pady=(4,2))
        return widget

    def row_double(row, labelL, labelR, widgetL=None, widgetR=None):
        """dupla: [lblL col0][entL col1]  [lblR col2][entR col3]"""
        if widgetL is None: widgetL = tk.Entry(inner, font=("Segoe UI", 11))
        if widgetR is None: widgetR = tk.Entry(inner, font=("Segoe UI", 11))
        tk.Label(inner, text=labelL, bg=CARD_BG, fg=LBL, anchor="e",
                 font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="e", padx=(0,12), pady=(4,2))
        widgetL.grid(row=row, column=1, sticky="we", pady=(4,2))
        tk.Label(inner, text=labelR, bg=CARD_BG, fg=LBL, anchor="e",
                 font=("Segoe UI", 11, "bold")).grid(row=row, column=2, sticky="e", padx=(0,12), pady=(4,2))
        widgetR.grid(row=row, column=3, sticky="we", pady=(4,2))
        return widgetL, widgetR

    def row_combo_plus(row, label, values, on_add):
        """label + combobox (col1) + botão + (col2)"""
        tk.Label(inner, text=label, bg=CARD_BG, fg=LBL, anchor="e",
                 font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="e", padx=(0,12), pady=(4,2))
        cb = ttk.Combobox(inner, values=values, state="readonly", font=("Segoe UI", 11))
        cb.grid(row=row, column=1, sticky="we", pady=(4,2))
        tk.Button(inner, text="+", command=on_add, bg=ACCENT, fg="white",
                  bd=0, cursor="hand2", width=3, height=1,
                  font=("Segoe UI", 11, "bold"), activebackground="#1e88e5")\
            .grid(row=row, column=2, sticky="w", pady=(4,2))
        return cb

    # =========================
    #   TÍTULO
    # =========================
    r = 0
    tk.Label(inner, text="Cadastro de Militar", font=("Segoe UI", 20, "bold"),
             bg=CARD_BG, fg=TIT).grid(row=r, column=0, columnspan=4, sticky="w", pady=(0, 6)); r += 1
    tk.Label(inner, text="Preencha os dados abaixo. Campos com * são obrigatórios.",
             font=("Segoe UI", 10), bg=CARD_BG, fg="#607d8b")\
        .grid(row=r, column=0, columnspan=4, sticky="w", pady=(0, 16)); r += 1

    # =========================
    #   IDENTIFICAÇÃO
    # =========================
    section_title(r, "Identificação"); r += 2

    try:
        postos_opcoes = listar_postos() or postos_default[:]
    except Exception:
        postos_opcoes = postos_default[:]
    postos_opcoes = ordenar_postos(postos_opcoes)

    def _add_posto():
        nome = simpledialog.askstring("Novo Posto/Graduação", "Digite o nome do posto/graduação:", parent=janela)
        if not nome: return
        nome = nome.strip()
        if len(nome) < 2:
            messagebox.showwarning("Atenção", "Informe um nome válido.", parent=janela); return
        try:
            ok = inserir_posto(nome)
            if not ok: messagebox.showinfo("Info", "Este posto já existe.", parent=janela)
            novas = ordenar_postos(listar_postos())
            cb_posto['values'] = novas
            if nome in novas: cb_posto.set(nome)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao inserir posto:\n{e}", parent=janela)

    cb_posto = row_combo_plus(r, "Posto e Graduação *", postos_opcoes, _add_posto); r += 1
    nome_cadastro = row_simple_full(r, "Nome completo *"); r += 1
    nome_de_guerra = row_simple_full(r, "Nome de guerra *"); r += 1
    cpf_entrada, prec_entrada = row_double(r, "CPF (11 dígitos) *", "PREC-CP (9 dígitos) *"); r += 1
    idt_entrada = row_simple_full(r, "IDT Militar (10 dígitos) *"); r += 1

    # =========================
    #   DADOS BANCÁRIOS
    # =========================
    section_title(r, "Dados Bancários"); r += 2

    try:
        bancos_opcoes = listar_bancos() or bancos_default[:]
    except Exception:
        bancos_opcoes = bancos_default[:]
    bancos_opcoes = ordenar_bancos(bancos_opcoes)

    def _add_banco():
        nome = simpledialog.askstring("Novo Banco", "Digite o nome do banco:", parent=janela)
        if not nome: return
        nome = nome.strip()
        if len(nome) < 2:
            messagebox.showwarning("Atenção", "Informe um nome válido.", parent=janela); return
        try:
            ok = inserir_banco(nome)
            if not ok: messagebox.showinfo("Info", "Este banco já existe.", parent=janela)
            novas = ordenar_bancos(listar_bancos())
            cb_banco['values'] = novas
            if nome in novas: cb_banco.set(nome)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao inserir banco:\n{e}", parent=janela)

    cb_banco = row_combo_plus(r, "Banco", bancos_opcoes, _add_banco); r += 1
    agencia_entrada, conta_entrada = row_double(r, "Agência (opcional)", "Conta (opcional)"); r += 1

    # =========================
    #   INFORMAÇÕES PESSOAIS
    # =========================
    section_title(r, "Informações Pessoais"); r += 2

    ano_entrada, data_nasc_entrada = row_double(r, "Ano de Formação", "Data de Nascimento (dd/mm/aaaa)"); r += 1
    data_praca_entrada = row_simple_full(r, "Data de Praça (dd/mm/aaaa)"); r += 1
    endereco_entrada = row_simple_full(r, "Endereço Completo"); r += 1
    cep_entrada = row_simple_full(r, "CEP"); r += 1

    # =========================
    #   BENEFÍCIOS
    # =========================
    section_title(r, "Benefícios"); r += 2

    recebe_pre_escolar_var = tk.StringVar(value="Não")
    pre_combo = ttk.Combobox(inner, textvariable=recebe_pre_escolar_var,
                             values=["Sim", "Não"], state="readonly", width=16, font=("Segoe UI", 11))
    valor_pre_entrada = tk.Entry(inner, font=("Segoe UI", 11))
    row_double(r, "Recebe Pré-Escolar?", "Valor Pré-Escolar", widgetL=pre_combo, widgetR=valor_pre_entrada); r += 1

    recebe_aux_transporte_var = tk.StringVar(value="Não")
    aux_combo = ttk.Combobox(inner, textvariable=recebe_aux_transporte_var,
                             values=["Sim", "Não"], state="readonly", width=16, font=("Segoe UI", 11))
    valor_aux_entrada = tk.Entry(inner, font=("Segoe UI", 11))
    row_double(r, "Recebe Auxílio Transporte?", "Valor Auxílio Transporte", widgetL=aux_combo, widgetR=valor_aux_entrada); r += 1

    pnr_var = tk.StringVar(value="Não")
    pnr_combo = ttk.Combobox(inner, textvariable=pnr_var, values=["Sim", "Não"],
                             state="readonly", width=16, font=("Segoe UI", 11))
    row_simple_full(r, "Possui PNR?", widget=pnr_combo); r += 1

    # =========================
    #   FOTO
    # =========================
    section_title(r, "Foto"); r += 2

    foto_path = tk.StringVar()
    label_foto_nome = tk.Label(inner, text="", bg=CARD_BG, fg="#8796a5", font=("Segoe UI", 10))
    label_foto_nome.grid(row=r, column=0, columnspan=3, sticky="w", pady=(0, 4))

    def carregar_imagem_preview(caminho):
        if caminho and os.path.exists(caminho):
            try:
                img = Image.open(caminho); img.thumbnail((280, 280))
                img_tk = ImageTk.PhotoImage(img)
                label_foto_preview.config(image=img_tk); label_foto_preview.image = img_tk
                label_foto_nome.config(text=os.path.basename(caminho), fg="#8796a5")
            except Exception:
                label_foto_nome.config(text="Erro ao carregar imagem", fg="#d32f2f")
                label_foto_preview.config(image=""); label_foto_preview.image = None
        else:
            label_foto_preview.config(image=""); label_foto_preview.image = None
            label_foto_nome.config(text="", fg="#8796a5")

    def selecionar_foto():
        caminho = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.png *.jpeg *.bmp *.gif")])
        if caminho:
            foto_path.set(caminho); carregar_imagem_preview(caminho)
        else:
            foto_path.set(""); carregar_imagem_preview("")

    tk.Button(inner, text="Selecionar Foto", command=selecionar_foto,
              bg=ACCENT, fg="white", font=("Segoe UI", 11, "bold"),
              bd=0, cursor="hand2", width=18, height=1, activebackground="#1e88e5")\
        .grid(row=r, column=3, sticky="e")
    r += 1

    # preview ocupa a linha inteira
    prev_card = tk.Frame(inner, bg="#fafafa", highlightbackground=BORDER, highlightthickness=1)
    prev_card.grid(row=r, column=0, columnspan=4, sticky="w", pady=(0, 10))
    label_foto_preview = tk.Label(prev_card, bg="#fafafa"); label_foto_preview.pack(padx=10, pady=10)
    r += 1

    # =========================
    #   SALVAR
    # =========================
    tk.Frame(inner, bg=BORDER, height=1).grid(row=r, column=0, columnspan=4, sticky="we", pady=(6, 14)); r += 1

    def salvar():
        try:
            posto = cb_posto.get()
            nome = nome_cadastro.get().strip().title()
            guerra = nome_de_guerra.get().strip().capitalize()
            cpf = cpf_entrada.get().strip()
            prec = prec_entrada.get().strip()
            idt = idt_entrada.get().strip()
            banco = cb_banco.get()
            agencia = agencia_entrada.get().strip()
            conta = conta_entrada.get().strip()
            foto = foto_path.get()
            ano = ano_entrada.get().strip()
            data_nascimento = data_nasc_entrada.get().strip()
            data_praca = data_praca_entrada.get().strip()
            endereco = endereco_entrada.get().strip()
            cep = cep_entrada.get().strip()
            recebe_pre_escolar = recebe_pre_escolar_var.get()
            valor_pre_escolar = valor_pre_entrada.get().strip()
            recebe_aux_transporte = recebe_aux_transporte_var.get()
            valor_aux_transporte = valor_aux_entrada.get().strip()
            pnr = pnr_var.get()

            if not nome: return messagebox.showerror("Erro", "Preencha o nome completo.", parent=janela)
            if not guerra: return messagebox.showerror("Erro", "Preencha o nome de guerra.", parent=janela)
            if remover_acentos(guerra) not in remover_acentos(nome):
                return messagebox.showerror("Erro", "O nome de guerra deve estar contido no nome completo.", parent=janela)
            if not cpf.isdigit() or len(cpf) != 11:
                return messagebox.showerror("Erro", "CPF deve conter exatamente 11 dígitos.", parent=janela)
            if not prec.isdigit() or len(prec) != 9:
                return messagebox.showerror("Erro", "PREC-CP deve conter 9 dígitos numéricos.", parent=janela)
            if not idt.isdigit() or len(idt) != 10:
                return messagebox.showerror("Erro", "IDT deve conter 10 dígitos numéricos.", parent=janela)

            dados = (
                posto, nome, guerra, cpf, prec, idt, banco, agencia, conta, foto,
                ano, data_nascimento, data_praca, endereco, cep,
                recebe_pre_escolar, valor_pre_escolar, recebe_aux_transporte, valor_aux_transporte, pnr
            )
            inserir_militar(dados)
            messagebox.showinfo("Sucesso", "Militar cadastrado com sucesso!", parent=janela)
            janela.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}", parent=janela)

    tk.Button(inner, text="Salvar", command=salvar,
              bg="#2e7d32", fg="white", font=("Segoe UI", 12, "bold"),
              width=20, height=2, bd=0, cursor="hand2", activebackground="#388e3c")\
        .grid(row=r, column=0, columnspan=4, pady=(0, 6))

    # inicia preview vazio
    carregar_imagem_preview("")
