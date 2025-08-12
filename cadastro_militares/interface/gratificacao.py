import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

# DB
from database.db import buscar_todos, obter_soldo_por_posto

# ---------- tema/estilo ----------
BG_APP = "#e3f2fd"
FG_TIT = "#0d47a1"
BORDER = "#dfe7f3"
CARD_BG = "#ffffff"
PRIMARY = "#1976d2"
PRIMARY_HOVER = "#1565c0"

# ---------- abreviações P/G (MAIÚSCULO) ----------
ABREV_PG = {
    "Capitão": "CAP",
    "1º Tenente": "1º TEN",
    "2º Tenente": "2º TEN",
    "Subtenente": "ST",
    "1º Sargento": "1º SGT",
    "2º Sargento": "2º SGT",
    "3º Sargento": "3º SGT",
    "Aspirante": "ASP",
    "Cabo Efetivo Profissional": "CB EF PROFL",
    "Soldado Efetivo Profissional": "SD EF PROFL",
    "Soldado Efetivo Variável": "SD EF VRV",
}

# ---------- hierarquia (ordem) ----------
ORDEM_HIERARQUIA = [
    "Capitão", "1º Tenente", "2º Tenente", "Subtenente",
    "1º Sargento", "2º Sargento", "3º Sargento",
    "Aspirante",
    "Cabo Efetivo Profissional", "Soldado Efetivo Profissional", "Soldado Efetivo Variável",
]
ORD_IDX = {p: i for i, p in enumerate(ORDEM_HIERARQUIA)}

# ---------- helpers ----------
def money(v) -> str:
    try:
        x = float(v)
    except Exception:
        x = 0.0
    s = f"{x:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

def digitos(s: str) -> str:
    return "".join(ch for ch in str(s) if ch.isdigit())

def formatar_cpf(cpf: str) -> str:
    s = digitos(cpf)
    return f"{s[0:3]}.{s[3:6]}.{s[6:9]}-{s[9:11]}" if len(s) == 11 else cpf

MESES_ABR = ["JAN","FEV","MAR","ABR","MAI","JUN","JUL","AGO","SET","OUT","NOV","DEZ"]
def fmt_data_abrev(dt: datetime) -> str:
    return f"{dt.day:02d} {MESES_ABR[dt.month-1]} {str(dt.year)[-2:]}"

def dias_periodo(d1: str, d2: str) -> int:
    """Datas em dd/mm/aaaa. Conta inclusivo (ex.: 05 a 13 -> 9)."""
    try:
        a = datetime.strptime(d1.strip(), "%d/%m/%Y")
        b = datetime.strptime(d2.strip(), "%d/%m/%Y")
        if b < a:
            a, b = b, a
        return (b - a).days + 1
    except Exception:
        return 0

# ----- número por extenso (pt-BR) p/ dinheiro (simples) -----
_UN = ["zero","um","dois","três","quatro","cinco","seis","sete","oito","nove"]
_DEZ = ["dez","onze","doze","treze","catorze","quinze","dezesseis","dezessete","dezoito","dezenove"]
_DZ = ["", "", "vinte","trinta","quarenta","cinquenta","sessenta","setenta","oitenta","noventa"]
_CN = ["","cento","duzentos","trezentos","quatrocentos","quinhentos","seiscentos","setecentos","oitocentos","novecentos"]

def _centena_por_extenso(n):
    n = int(n)
    if n == 0: return ""
    if n == 100: return "cem"
    c = n // 100
    r = n % 100
    partes = []
    if c: partes.append(_CN[c])
    if r:
        if r < 10: partes.append(_UN[r])
        elif 10 <= r < 20: partes.append(_DEZ[r-10])
        else:
            d = r // 10
            u = r % 10
            if u: partes.append(f"{_DZ[d]} e {_UN[u]}")
            else: partes.append(_DZ[d])
    return " e ".join(p for p in partes if p)

def _milhares(n):
    if n == 0: return ""
    if n == 1: return "mil"
    return f"{_centena_por_extenso(n)} mil"

def numero_em_reais_extenso(valor: float) -> str:
    valor = round(float(valor) + 1e-9, 2)
    inteiro = int(valor)
    cent = int(round((valor - inteiro) * 100))

    partes = []
    milhoes = inteiro // 1_000_000
    resto = inteiro % 1_000_000
    milhares = resto // 1000
    centenas = resto % 1000

    if milhoes:
        partes.append("um milhão" if milhoes == 1 else f"{_centena_por_extenso(milhoes)} milhões")
    if milhares:
        partes.append(_milhares(milhares))
    if centenas:
        partes.append(_centena_por_extenso(centenas))
    if not (milhoes or milhares or centenas):
        partes.append("zero")

    reais = "real" if inteiro == 1 else "reais"
    frase = " ".join(partes) + f" {reais}"

    if cent:
        centavos = "centavo" if cent == 1 else "centavos"
        frase += f" e {_centena_por_extenso(cent)} {centavos}"
    return frase

# ---------- dados base ----------
def _carregar_militares():
    regs = []
    try:
        lista = buscar_todos()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar militares:\n{e}")
        return regs
    for it in lista:
        # (id, posto, nome, nome_guerra, cpf, prec, idt, banco, ag, conta, foto, ...)
        regs.append({
            "ID": it[0],
            "Posto": it[1],
            "Nome": it[2],
            "CPF": it[4],
            "PREC": it[5],
        })
    # ordena por hierarquia + nome
    regs.sort(key=lambda d: (ORD_IDX.get(d["Posto"], 999), str(d["Nome"] or "").lower()))
    return regs

# =========================
#   Janela Gratificação 2%
# =========================
def abrir_gratificacao_representacao(master):
    win = tk.Toplevel(master)
    win.title("Gratificação de Representação (2%)")
    win.geometry("1200x760")
    win.configure(bg=BG_APP)
    win.resizable(True, True)
    try:
        win.state("zoomed")
    except Exception:
        pass
    win.grab_set()

    # --------- ttk theme / styles ---------
    style = ttk.Style(win)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground=FG_TIT, background=BG_APP)
    style.configure("Sub.TLabel", font=("Segoe UI", 11, "bold"), background=BG_APP, foreground="#37474f")
    style.configure("Card.TFrame", background=CARD_BG, relief="flat")
    style.configure("TSeparator", background=BORDER)

    style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"),
                    padding=(14, 8), foreground="white", background=PRIMARY, borderwidth=0)
    style.map("Primary.TButton", background=[("active", PRIMARY_HOVER), ("pressed", PRIMARY_HOVER)])
    style.configure("Ghost.TButton", font=("Segoe UI", 11, "bold"),
                    padding=(12, 6), foreground=PRIMARY, background="#eaf3ff", borderwidth=0)
    style.map("Ghost.TButton",
              foreground=[("active", "white"), ("pressed", "white")],
              background=[("active", PRIMARY), ("pressed", PRIMARY)])

    # força cores legíveis no Treeview
    style.configure("Treeview", rowheight=28, font=("Segoe UI", 11),
                    foreground="#111", background="white", fieldbackground="white")
    style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#e8f0fe")
    style.map("Treeview",
              background=[("selected", "#cfe8ff")],
              foreground=[("selected", "#000")])

    # --------- Título ----------
    ttk.Label(win, text="GRATIFICAÇÃO DE REPRESENTAÇÃO (2%)", style="Title.TLabel").pack(pady=(16, 8))

    # -------------- Card: Config do Boletim --------------
    card_cfg = ttk.Frame(win, style="Card.TFrame", padding=(12, 10))
    card_cfg.pack(fill="x", padx=14, pady=(0, 10))

    def mk_lbl(parent, txt): return ttk.Label(parent, text=txt, style="Sub.TLabel")

    mk_lbl(card_cfg, "Local do deslocamento:").grid(row=0, column=0, sticky="e", padx=(0, 8), pady=4)
    ent_local = ttk.Entry(card_cfg, width=40)
    ent_local.insert(0, "Guarnição do Rio de Janeiro")
    ent_local.grid(row=0, column=1, sticky="w", pady=4)

    mk_lbl(card_cfg, "Finalidade:").grid(row=0, column=2, sticky="e", padx=(18, 8), pady=4)
    ent_finalidade = ttk.Entry(card_cfg, width=52)
    ent_finalidade.insert(0, "competir nas Olimpíadas Militares do CML")
    ent_finalidade.grid(row=0, column=3, sticky="w", pady=4)

    mk_lbl(card_cfg, "Saída (dd/mm/aaaa):").grid(row=1, column=0, sticky="e", padx=(0, 8), pady=4)
    ent_saida = ttk.Entry(card_cfg, width=18)
    ent_saida.insert(0, "05/06/2025")
    ent_saida.grid(row=1, column=1, sticky="w", pady=4)

    mk_lbl(card_cfg, "Retorno (dd/mm/aaaa):").grid(row=1, column=2, sticky="e", padx=(18, 8), pady=4)
    ent_retorno = ttk.Entry(card_cfg, width=18)
    ent_retorno.insert(0, "13/06/2025")
    ent_retorno.grid(row=1, column=3, sticky="w", pady=4)

    mk_lbl(card_cfg, "BI nº / data:").grid(row=2, column=0, sticky="e", padx=(0, 8), pady=4)
    ent_bi = ttk.Entry(card_cfg, width=40)
    ent_bi.insert(0, "BI Nr 113, de 23 JUN 25 da 4ª Cia PE")
    ent_bi.grid(row=2, column=1, sticky="w", pady=4)

    # ---- Resumo de período (dias comuns) ----
    dias_top_var = tk.IntVar(value=dias_periodo(ent_saida.get(), ent_retorno.get()))
    resumo_var = tk.StringVar(value="")

    mk_lbl(card_cfg, "Resumo:").grid(row=3, column=0, sticky="e", padx=(0, 8), pady=(8,4))
    lbl_resumo = ttk.Label(card_cfg, textvariable=resumo_var)
    lbl_resumo.grid(row=3, column=1, columnspan=3, sticky="w", pady=(8,4))

    for c in range(4):
        card_cfg.grid_columnconfigure(c, weight=1 if c in (1, 3) else 0)

    ttk.Separator(win).pack(fill="x", padx=12, pady=(6, 10))

    # -------------- Split: esquerda (lista) / direita (selecionados) --------------
    split = tk.Frame(win, bg=BG_APP)
    split.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    left = ttk.Frame(split, style="Card.TFrame", padding=(10, 10))
    left.pack(side="left", fill="both", expand=True, padx=(0, 6))

    right = ttk.Frame(split, style="Card.TFrame", padding=(10, 10))
    right.pack(side="left", fill="both", expand=True, padx=(6, 0))

    # ---- esquerda: filtro + tree de todos ----
    top_l = ttk.Frame(left, style="Card.TFrame")
    top_l.pack(fill="x", pady=(0, 8))

    ttk.Label(top_l, text="Buscar:", style="Sub.TLabel").pack(side="left")
    busca_var = tk.StringVar()
    ent_busca = ttk.Entry(top_l, textvariable=busca_var, width=36)
    ent_busca.pack(side="left", padx=8)

    wrap_btns = ttk.Frame(top_l, style="Card.TFrame")
    wrap_btns.pack(side="right")

    btn_add_all = ttk.Button(wrap_btns, text="Adicionar TODOS ➜", style="Ghost.TButton")
    btn_add_all.pack(side="right", padx=(6,0))

    btn_reload = ttk.Button(wrap_btns, text="Recarregar", style="Ghost.TButton")
    btn_reload.pack(side="right", padx=(6,0))

    btn_add = ttk.Button(wrap_btns, text="Adicionar Selecionados ➜", style="Primary.TButton")
    btn_add.pack(side="right", padx=(6,0))

    cols = ("nome","posto","soldo","val_dia")
    tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="extended")
    ysb = ttk.Scrollbar(left, orient="vertical", command=tree.yview)
    xsb = ttk.Scrollbar(left, orient="horizontal", command=tree.xview)
    tree.configure(yscroll=ysb.set, xscroll=xsb.set)

    tree.heading("nome", text="NOME")
    tree.heading("posto", text="POSTO")
    tree.heading("soldo", text="SOLDO")
    tree.heading("val_dia", text="2%/DIA")

    tree.column("nome", width=380, anchor="w")
    tree.column("posto", width=170, anchor="center")
    tree.column("soldo", width=130, anchor="center")
    tree.column("val_dia", width=130, anchor="center")

    tree.pack(fill="both", expand=True)
    ysb.pack(side="right", fill="y")
    xsb.pack(fill="x")

    tree.tag_configure("odd", background="#f8fbff")
    tree.tag_configure("even", background="#ffffff")

    # carrega base + popular
    base_regs = _carregar_militares()

    def _popular_lista():
        tree.delete(*tree.get_children())
        q = (busca_var.get() or "").strip().lower()
        count = 0
        for i, d in enumerate(base_regs):
            if q and q not in str(d["Nome"]).lower():
                continue
            soldo = float(obter_soldo_por_posto(d["Posto"]) or 0.0)
            vdia = soldo * 0.02
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end",
                        values=(d["Nome"], d["Posto"], money(soldo), money(vdia)),
                        iid=str(d["ID"]), tags=(tag,))
            count += 1
        if count == 0:
            tree.insert("", "end",
                        values=("— Nenhum militar encontrado —", "", "", ""),
                        iid="__vazio__", tags=("odd",))

    _popular_lista()
    busca_var.trace_add("write", lambda *_: _popular_lista())
    tree.bind("<Double-1>", lambda e: btn_add.invoke())

    def _iids_todos():
        return [iid for iid in tree.get_children("") if iid != "__vazio__"]

    def _recarregar():
        nonlocal base_regs
        base_regs = _carregar_militares()
        _popular_lista()

    btn_reload.config(command=_recarregar)

    # ---- direita: selecionados (usam DIAS COMUNS do topo) ----
    top_r = ttk.Frame(right, style="Card.TFrame")
    top_r.pack(fill="x")
    ttk.Label(top_r, text="Selecionados", style="Sub.TLabel").pack(side="left")

    btn_boletim = ttk.Button(top_r, text="Gerar Boletim", style="Primary.TButton")
    btn_boletim.pack(side="right", padx=6)
    btn_rm = ttk.Button(top_r, text="Remover Selecionados", style="Ghost.TButton")
    btn_rm.pack(side="right", padx=6)

    wrap = ttk.Frame(right, style="Card.TFrame")
    wrap.pack(fill="both", expand=True, pady=(8, 0))

    canvas = tk.Canvas(wrap, bg=BG_APP, highlightthickness=0)
    sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas, style="Card.TFrame")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    # header dos selecionados
    hdr = ttk.Frame(inner, style="Card.TFrame")
    hdr.pack(fill="x", pady=(0, 6))
    heads = [("NOME", 34), ("P/G", 8), ("2%/dia", 14), ("Dias (comuns)", 16), ("TOTAL", 14)]
    for i, (t, _w) in enumerate(heads):
        ttk.Label(hdr, text=t, style="Sub.TLabel").grid(row=0, column=i, padx=6, sticky="w")

    # dados vivos dos selecionados
    linhas = {}  # id -> dict(row widgets + dados)

    def _recalc_all_totais():
        """Recalcula TODAS as linhas quando muda o período comum (topo)."""
        dd = dias_top_var.get()
        for iid, dline in list(linhas.items()):
            dline["lbl_dias"]["text"] = dd
            total = dline["val_dia"] * dd
            dline["lbl_total"]["text"] = money(total)
            dline["total"] = total
            dline["dias"] = dd

    def _atualiza_resumo():
        d = dias_periodo(ent_saida.get(), ent_retorno.get())
        dias_top_var.set(d)
        resumo_var.set(f"Período comum: {ent_saida.get()} a {ent_retorno.get()}  •  Dias (inclusivo): {d}")
        _recalc_all_totais()

    def _add_rows(ids):
        dd = dias_top_var.get()
        for iid in ids:
            if iid in linhas:
                continue
            d = next((x for x in base_regs if str(x["ID"]) == iid), None)
            if not d:
                continue
            soldo = float(obter_soldo_por_posto(d["Posto"]) or 0.0)
            vdia = soldo * 0.02

            row = ttk.Frame(inner, style="Card.TFrame")
            row.pack(fill="x", pady=4)
            row_inner = tk.Frame(row, bg="#fafafa", highlightbackground=BORDER, highlightthickness=1)
            row_inner.pack(fill="x", padx=2, pady=2)

            tk.Label(row_inner, text=str(d["Nome"]).upper(), bg="#fafafa",
                     font=("Segoe UI", 10, "bold"), width=34, anchor="w").grid(row=0, column=0, padx=6, pady=6, sticky="w")
            tk.Label(row_inner, text=ABREV_PG.get(d["Posto"], d["Posto"].upper()),
                     bg="#fafafa", width=8, font=("Segoe UI", 10)).grid(row=0, column=1, padx=6, pady=6, sticky="w")

            ttk.Label(row_inner, text=money(vdia), width=14).grid(row=0, column=2, padx=6, pady=6, sticky="w")
            lbl_dias = ttk.Label(row_inner, text=str(dd), width=16)
            lbl_dias.grid(row=0, column=3, padx=6, pady=6, sticky="w")
            lbl_total = ttk.Label(row_inner, text=money(vdia * dd))
            lbl_total.grid(row=0, column=4, padx=6, pady=6, sticky="w")
            lbl_total.configure(font=("Segoe UI", 10, "bold"))

            linhas[iid] = {
                "row": row, "dados": d,
                "lbl_dias": lbl_dias, "lbl_total": lbl_total,
                "val_dia": vdia, "total": vdia * dd, "dias": dd
            }

    def _remove_selected_rows():
        sel_left = [iid for iid in tree.selection()]
        if not sel_left:
            if not linhas:
                return
            if not messagebox.askyesno("Remover", "Remover TODOS os selecionados?", parent=win):
                return
            sel_left = list(linhas.keys())
        for iid in sel_left:
            if iid in linhas:
                try:
                    linhas[iid]["row"].destroy()
                except Exception:
                    pass
                linhas.pop(iid, None)

    btn_add.config(command=lambda: _add_rows(tree.selection() or _iids_todos()))
    btn_add_all.config(command=lambda: _add_rows(_iids_todos()))
    btn_rm.config(command=_remove_selected_rows)

    # recalcular ao mudar as datas do cabeçalho
    ent_saida.bind("<FocusOut>", lambda e: _atualiza_resumo())
    ent_retorno.bind("<FocusOut>", lambda e: _atualiza_resumo())
    ent_saida.bind("<KeyRelease>", lambda e: _atualiza_resumo())
    ent_retorno.bind("<KeyRelease>", lambda e: _atualiza_resumo())

    # inicializa resumo agora que as funções existem
    _atualiza_resumo()

    # -------------- Gerar Boletim --------------
    def _gerar_boletim():
        if not linhas:
            messagebox.showinfo("Info", "Nenhum militar selecionado.", parent=win)
            return
        try:
            dt_saida = datetime.strptime(ent_saida.get().strip(), "%d/%m/%Y")
            dt_retorno = datetime.strptime(ent_retorno.get().strip(), "%d/%m/%Y")
        except Exception:
            messagebox.showerror("Erro", "Datas do cabeçalho inválidas. Use dd/mm/aaaa.", parent=win)
            return

        local = ent_local.get().strip()
        finalidade = ent_finalidade.get().strip()
        bi = ent_bi.get().strip()
        dias_comuns = dias_top_var.get()

        header = (
            f"Seja sacada a gratificação de representação normal (2%), dos seguintes militares abaixo relacionados, "
            f"referente ao deslocamento a serviço, para a {local}, em {fmt_data_abrev(dt_saida)}, "
            f"com a finalidade de {finalidade}, tendo retornado em {fmt_data_abrev(dt_retorno)}, "
            f"que teve seu deslocamento autorizado pelo {bi}.\n\n"
        )

        corpo = ""
        for iid, dline in linhas.items():
            d = dline["dados"]
            total = dline["val_dia"] * dias_comuns
            total_ext = numero_em_reais_extenso(total)
            abrev = ABREV_PG.get(d["Posto"], d["Posto"].upper())
            nome_up = str(d["Nome"] or "").upper()
            prec = str(d["PREC"] or "")
            cpf_fmt = formatar_cpf(d["CPF"])
            dias_ext = numero_em_reais_extenso(dias_comuns).replace(" reais","").replace(" real","")

            corpo += f"{abrev} {nome_up}\n"
            corpo += f"Prec-CP {prec} CPF {cpf_fmt}\n"
            corpo += f"Valor solicitado: {money(total)} ({total_ext});\n"
            corpo += f"Período: {fmt_data_abrev(dt_saida)} a {fmt_data_abrev(dt_retorno)};\n"
            corpo += f"Quantidade de dias: {dias_comuns} ({dias_ext}) dias\n\n"

        texto = header + corpo

        # diálogo de prévia (com botões sempre visíveis)
        dlg = tk.Toplevel(win)
        dlg.title("Boletim - Gratificação de Representação (2%)")
        dlg.geometry("860x600")
        dlg.configure(bg=BG_APP)
        dlg.grab_set()

        dlg.grid_rowconfigure(1, weight=1)
        dlg.grid_columnconfigure(0, weight=1)

        ttk.Label(dlg, text="Prévia do Boletim", style="Title.TLabel").grid(row=0, column=0, pady=(12, 6), sticky="w", padx=12)

        frame_txt = ttk.Frame(dlg, style="Card.TFrame", padding=6)
        frame_txt.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        txt = tk.Text(frame_txt, wrap="word", font=("Segoe UI", 11))
        txt.grid(row=0, column=0, sticky="nsew")
        ysb2 = ttk.Scrollbar(frame_txt, orient="vertical", command=txt.yview)
        ysb2.grid(row=0, column=1, sticky="ns")
        txt.configure(yscrollcommand=ysb2.set)
        frame_txt.grid_rowconfigure(0, weight=1)
        frame_txt.grid_columnconfigure(0, weight=1)
        txt.insert("1.0", texto)

        barx = ttk.Frame(dlg, style="Card.TFrame")
        barx.grid(row=2, column=0, pady=8)
        def _copiar():
            dlg.clipboard_clear(); dlg.clipboard_append(txt.get("1.0", "end-1c"))
            messagebox.showinfo("OK", "Texto copiado para a área de transferência.", parent=dlg)
        def _salvar():
            path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Texto", "*.txt")], parent=dlg)
            if not path: return
            with open(path, "w", encoding="utf-8") as f:
                f.write(txt.get("1.0", "end-1c"))
            messagebox.showinfo("OK", f"Arquivo salvo em:\n{path}", parent=dlg)

        ttk.Button(barx, text="Copiar", style="Primary.TButton", command=_copiar).pack(side="left", padx=6)
        ttk.Button(barx, text="Salvar .txt", style="Ghost.TButton", command=_salvar).pack(side="left", padx=6)

    btn_boletim.config(command=_gerar_boletim)
