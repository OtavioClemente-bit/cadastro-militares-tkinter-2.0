import tkinter as tk
from tkinter import ttk, messagebox, filedialog


from database.db import buscar_todos, atualizar_aux_transporte, obter_soldo_por_posto

# --------- tema/estilo ----------
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
    "width": 16,
    "height": 1,
    "bd": 0,
    "cursor": "hand2"
}
ESTILO_BOTAO_SM = {**ESTILO_BOTAO, "width": 10}
ESTILO_BOTAO_TINY = {**ESTILO_BOTAO, "width": 2}

ABREV_POSTOS = {
    "Capitão": "Cap.",
    "1º Tenente": "1º Ten.",
    "2º Tenente": "2º Ten.",
    "Subtenente": "Sub Ten.",
    "1º Sargento": "1º Sgt",
    "2º Sargento": "2º Sgt",
    "3º Sargento": "3º Sgt",
    "Cabo Efetivo Profissional": "Cb EP",
    "Soldado Efetivo Profissional": "Sd EP",
    "Soldado Efetivo Variável": "Sd EV",
}

# ORDEM HIERÁRQUICA 
ORDER_POSTOS = [
    "Capitão",
    "1º Tenente",
    "2º Tenente",
    "Subtenente",
    "1º Sargento",
    "2º Sargento",
    "3º Sargento",
    "Cabo Efetivo Profissional",
    "Soldado Efetivo Profissional",
    "Soldado Efetivo Variável",
]
RANK_INDEX = {p: i for i, p in enumerate(ORDER_POSTOS)}

def _posto_key(p):
    return RANK_INDEX.get(p, 999)

# --------- helpers de formato ----------
import re as _re
_RE_MONEY = _re.compile(r"^\s*(R\$)?\s*\d{0,9}([.,]\d{0,2})?\s*$")

def _to_float(v, default=0.0):
    try:
        s = str(v).strip().replace("R$", "").replace(" ", "")
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        return float(s) if s else default
    except Exception:
        return default

def money(v) -> str:
    try:
        x = float(v)
    except Exception:
        x = 0.0
    s = f"{x:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

def money_entry(parent, textvariable=None, width=12):
    var = textvariable or tk.StringVar()
    def _vcmd(newval):
        return _RE_MONEY.match(newval) is not None if newval != "" else True
    def _fmt(_evt=None):
        if var.get().strip() == "":
            var.set("R$ 0,00"); return
        var.set(money(_to_float(var.get(), 0.0)))
    vcmd = (parent.register(_vcmd), "%P")
    e = tk.Entry(parent, textvariable=var, width=width, validate="key",
                 validatecommand=vcmd, font=("Segoe UI", 11))
    e.bind("<FocusOut>", _fmt)
    return e, var

# --------- cálculos ----------
def calcular_por_total_mensal(total_mensal, soldo):
    """Recebe TOTAL BRUTO (22d) e soldo; retorna líquido (aux) e cota.
       Só é usada na calculadora quando houver tarifas."""
    total = _to_float(total_mensal, 0.0)
    sd = _to_float(soldo, 0.0)
    cota30 = sd * 0.06
    cota22 = cota30 * (22.0/30.0)
    aux = max(0.0, total - cota22)  # líquido
    return {"total_mes_22": total, "cota22": cota22, "aux": aux}

def calcular_por_tarifas(lista_tarifas, soldo):
    """Usada apenas na calculadora: tarifa x2 = valor do dia (BRUTO)"""
    soma_tarifas = sum(_to_float(x, 0.0) for x in lista_tarifas)
    valor_dia_bruto = soma_tarifas * 2.0
    total_mes_22 = valor_dia_bruto * 22.0
    r = calcular_por_total_mensal(total_mes_22, soldo)  # dá o líquido (aux)
    r.update({"valor_dia": valor_dia_bruto})
    return r

# =========================
#   Janela Auxílio
# =========================
def abrir_auxilio_transporte(master):
    win = tk.Toplevel(master)
    win.title("Auxílio Transporte")
    win.geometry("1050x700")
    win.configure(bg=BG_APP)
    win.resizable(False, False)
    win.grab_set()

    # ---------- estilos ttk mais bonitos ----------
    style = ttk.Style(win)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Blue.TNotebook", background=BG_APP, borderwidth=0, tabmargins=(10, 8, 10, 0))
    style.configure("Blue.TNotebook.Tab",
                    font=("Segoe UI", 12, "bold"),
                    padding=(20, 10),
                    background="#eaf3ff")
    style.map("Blue.TNotebook.Tab",
              background=[("selected", "white")],
              foreground=[("selected", FG_TIT)])
    style.configure("mystyle.Treeview",
                    background="white",
                    fieldbackground="white",
                    rowheight=26,
                    font=("Segoe UI", 10))
    style.configure("mystyle.Treeview.Heading",
                    font=("Segoe UI", 11, "bold"),
                    background="#bbdefb",
                    foreground=FG_TIT)

    tk.Label(win, text="AUXÍLIO TRANSPORTE", font=("Segoe UI", 20, "bold"),
             bg=BG_APP, fg=FG_TIT).pack(pady=(20, 6))

    nb = ttk.Notebook(win, style="Blue.TNotebook")
    nb.pack(fill="both", expand=True, padx=16, pady=10)

    # ---------------- dados base ----------------
    def _carregar_militares():
        try:
            lista = buscar_todos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar militares:\n{e}", parent=win)
            return []
        out = []
        for it in lista:
            out.append({
                "ID": it[0],
                "Posto": it[1],
                "Nome": it[2],
                "CPF": it[4],
                "PREC": it[5],
                "recebe_aux_transporte": it[18] if len(it)>18 else "Não",
                "valor_aux_transporte": it[19] if len(it)>19 else 0.0
            })
        return out

    # ============== ABA 1: RELATÓRIO ==============
    tab_rel = tk.Frame(nb, bg=BG_APP); nb.add(tab_rel, text="Relatório")

    # busca (tempo real)
    top_rel = tk.Frame(tab_rel, bg=BG_APP); top_rel.pack(fill="x", padx=10, pady=(10,0))
    tk.Label(top_rel, text="Buscar:", bg=BG_APP, font=("Segoe UI", 11, "bold")).pack(side="left")
    busca_var = tk.StringVar()
    ent_busca_rel = tk.Entry(top_rel, textvariable=busca_var, width=40, font=("Segoe UI", 11))
    ent_busca_rel.pack(side="left", padx=8)
    def _on_type_rel(_=None): _popular_relatorio()
    ent_busca_rel.bind("<KeyRelease>", _on_type_rel)

    # Só duas colunas de valores:
    cols = ("nome","posto","valor_dia","total_liquido")
    headers = ("NOME","POSTO","VALOR DO DIA (LÍQ./22)","TOTAL (LÍQ.)")
    widths  = (360, 240, 180, 180)

    tree = ttk.Treeview(tab_rel, columns=cols, show="headings", style="mystyle.Treeview")
    for c,h,w in zip(cols, headers, widths):
        tree.heading(c, text=h)
        tree.column(c, width=w, anchor="center")
    tree.pack(fill="both", expand=True, padx=12, pady=12)
    vsb = ttk.Scrollbar(tab_rel, orient="vertical", command=tree.yview)
    tree.configure(yscroll=vsb.set)
    vsb.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne")

    # zebra rows
    tree.tag_configure("odd", background="#f6fbff")
    tree.tag_configure("even", background="#ffffff")

    item_to_info = {}

    bar_rel = tk.Frame(tab_rel, bg=BG_APP); bar_rel.pack(fill="x", padx=12, pady=(0,12))
    btn_atualizar = tk.Button(bar_rel, text="Atualizar", **ESTILO_BOTAO_SM)
    btn_editar    = tk.Button(bar_rel, text="Editar", **ESTILO_BOTAO_SM)
    btn_atualizar.pack(side="left", padx=6)
    btn_editar.pack(side="left", padx=6)

    def _popular_relatorio():
        tree.delete(*tree.get_children())
        item_to_info.clear()
        q = (busca_var.get() or "").strip().lower()
        regs = _carregar_militares()

        linhas = []
        for d in regs:
            if not str(d.get("recebe_aux_transporte","Não")).lower().startswith("s"):
                continue
            nome = str(d["Nome"])
            if q and q not in nome.lower():
                continue
            posto = str(d["Posto"])

            total_liq = _to_float(d.get("valor_aux_transporte", 0.0), 0.0)  # JÁ é líquido
            valor_dia_liq = total_liq / 22.0 if total_liq else 0.0

            linhas.append({
                "ID": int(d["ID"]), "nome": nome, "posto": posto,
                "valor_dia": valor_dia_liq, "total_liquido": total_liq
            })

        # ordena por hierarquia e depois por nome
        linhas.sort(key=lambda x: (_posto_key(x["posto"]), x["nome"].lower()))

        for i, row in enumerate(linhas):
            tag = "odd" if i % 2 else "even"
            item = tree.insert(
                "", "end",
                values=(
                    row["nome"],
                    row["posto"],
                    money(row["valor_dia"]),      
                    money(row["total_liquido"])   
                ),
                tags=(tag,)
            )
            item_to_info[item] = (row["ID"], row["nome"], row["posto"], row["total_liquido"])

    btn_atualizar.config(command=_popular_relatorio)
    _popular_relatorio()

    def _editar_selecionado():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Selecione um militar no relatório.", parent=win)
            return
        item = sel[0]
        pid, nome, posto, total_liquido = item_to_info[item]
        _abrir_dialog_calculadora(win, pid, nome, posto,
                                  total_inicial=total_liquido, on_saved=_popular_relatorio)
    btn_editar.config(command=_editar_selecionado)

    # ============== ABA 2: CALCULADORA ==============
    tab_calc = tk.Frame(nb, bg=BG_APP); nb.add(tab_calc, text="Calculadora")

    topo = tk.Frame(tab_calc, bg=BG_APP); topo.pack(pady=(12, 4))
    tk.Label(topo, text="Posto (para calcular cota quando houver tarifas):",
             bg=BG_APP, font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="e", padx=6)

    postos_usados = sorted({d["Posto"] for d in _carregar_militares()}, key=_posto_key)
    posto_calc = tk.StringVar(value=postos_usados[0] if postos_usados else "")
    cb_calc = ttk.Combobox(topo, values=postos_usados, textvariable=posto_calc, state="readonly", width=36)
    cb_calc.grid(row=0, column=1, sticky="w")

    box = tk.Frame(tab_calc, bg=BG_APP); box.pack(pady=8, anchor="w")
    linhas = []
    def add_linha(valor=""):
        row = tk.Frame(box, bg=BG_APP); row.pack(pady=4, anchor="w")
        idx = len(linhas)+1
        tk.Label(row, text=f"Ônibus {idx}:", bg=BG_APP, font=("Segoe UI", 11)).pack(side="left", padx=(0,6))
        v = tk.StringVar(value=str(valor))
        e, v = money_entry(row, textvariable=v, width=12)
        e.pack(side="left")
        tk.Button(row, text="Remover",
                  command=lambda r=row, var=v: _remover(r, var),
                  **ESTILO_BOTAO_SM).pack(side="left", padx=8)
        linhas.append((row, v))
    def _remover(row, var):
        row.destroy()
        for i,(r,v) in enumerate(list(linhas)):
            if v is var:
                linhas.remove((r,v)); break

    tool = tk.Frame(tab_calc, bg=BG_APP); tool.pack(pady=6)
    tk.Button(tool, text="Adicionar", command=add_linha, **ESTILO_BOTAO_SM).pack(side="left", padx=6)
    tk.Button(tool, text="Calcular", command=lambda: _calcular_calc(), **ESTILO_BOTAO_SM).pack(side="left", padx=6)

    res = tk.Frame(tab_calc, bg=BG_APP); res.pack(pady=8)
    lbl_dia  = tk.Label(res, text="Valor do dia (BRUTO pelas tarifas): —", bg=BG_APP, font=("Segoe UI", 12)); lbl_dia.pack(anchor="w")
    lbl_tot  = tk.Label(res, text="Total mensal (22d): —", bg=BG_APP, font=("Segoe UI", 12)); lbl_tot.pack(anchor="w")
    lbl_cota = tk.Label(res, text="Cota-parte (22d): —", bg=BG_APP, font=("Segoe UI", 12)); lbl_cota.pack(anchor="w")
    lbl_aux  = tk.Label(res, text="Auxílio Transporte (LÍQ. a salvar): —", bg=BG_APP, font=("Segoe UI", 13, "bold")); lbl_aux.pack(anchor="w")

    def _calcular_calc():
        tarifas = [v.get() for _,v in linhas if v.get().strip()!=""]
        soldo = obter_soldo_por_posto(posto_calc.get()) or 0.0
        if not tarifas:
            lbl_dia.config(text="Valor do dia (BRUTO pelas tarifas): —")
            lbl_tot.config(text="Total mensal (22d): —")
            lbl_cota.config(text="Cota-parte (22d): —")
            lbl_aux.config(text="Auxílio Transporte (LÍQ. a salvar): —")
            messagebox.showinfo(
                "Info",
                "Informe as tarifas para calcular BRUTO, cota e novo LÍQUIDO.\n"
                "Sem tarifas, o valor atual já é tratado como LÍQUIDO.",
                parent=win
            )
        else:
            r = calcular_por_tarifas(tarifas, soldo) 
            lbl_dia.config(text=f"Valor do dia (BRUTO pelas tarifas): {money(r.get('valor_dia',0.0))}")
            lbl_tot.config(text=f"Total mensal (22d): {money(r['total_mes_22'])}")
            lbl_cota.config(text=f"Cota-parte (22d): {money(r['cota22'])}")
            lbl_aux.config(text=f"Auxílio Transporte (LÍQ. a salvar): {money(r['aux'])}")

    add_linha("5,75"); add_linha("5,75")

    # ============== ABA 3: DESPESA A ANULAR ==============
    tab_da = tk.Frame(nb, bg=BG_APP); nb.add(tab_da, text="Despesa a Anular")

    tk.Label(tab_da, text="Informe PRETA (−1 dia) e VERMELHA (+1 dia). A diária aqui é (LÍQ./22).",
             bg=BG_APP, font=("Segoe UI", 10)).pack(anchor="w", padx=12, pady=(10, 4))

    top_da = tk.Frame(tab_da, bg=BG_APP); top_da.pack(fill="x", padx=12, pady=6)
    tk.Label(top_da, text="Buscar:", bg=BG_APP, font=("Segoe UI", 11, "bold")).pack(side="left")
    busca_da = tk.StringVar()
    ent_da = tk.Entry(top_da, textvariable=busca_da, width=40, font=("Segoe UI", 11))
    ent_da.pack(side="left", padx=8)
    btn_reload_da = tk.Button(top_da, text="Recarregar", **ESTILO_BOTAO_SM)
    btn_boletim   = tk.Button(top_da, text="Gerar Boletim", **ESTILO_BOTAO_SM)
    btn_reload_da.pack(side="left", padx=6)
    btn_boletim.pack(side="left", padx=6)

    wrap = tk.Frame(tab_da, bg=BG_APP); wrap.pack(fill="both", expand=True, padx=10, pady=(0,10))
    canvas = tk.Canvas(wrap, bg=BG_APP, highlightthickness=0)
    sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG_APP)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    linhas_da = []  # cada item

    def _linha_da(parent, base):
        row_data = {
            **base,
            "preta": 0,
            "vermelha": 0,
            "ajuste": 0.0,
            "novo_liquido": base["liquido_base"]
        }

        row = tk.Frame(parent, bg=BG_APP, bd=0)
        row.pack(fill="x", pady=4)

        tk.Label(row, text=f"{row_data['Nome']}  |  {row_data['Posto']}",
                 bg=BG_APP, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=6, sticky="w")

        tk.Label(row, text=f"Valor dia: {money(row_data['valor_dia'])}", bg=BG_APP)\
            .grid(row=1, column=0, sticky="w", padx=2)
        tk.Label(row, text=f"Total (LÍQ.) base: {money(row_data['liquido_base'])}", bg=BG_APP)\
            .grid(row=1, column=1, sticky="w", padx=(12,2))

        tk.Label(row, text="Preta:", bg=BG_APP).grid(row=1, column=2, sticky="e", padx=(16,2))
        preta_var = tk.IntVar(value=0)
        tk.Button(row, text="−", command=lambda: _dec("preta"), **ESTILO_BOTAO_TINY)\
            .grid(row=1, column=3, sticky="w")
        lbl_preta = tk.Label(row, textvariable=preta_var, bg=BG_APP, width=3, anchor="center")
        lbl_preta.grid(row=1, column=4, padx=2)
        tk.Button(row, text="+", command=lambda: _inc("preta"), **ESTILO_BOTAO_TINY)\
            .grid(row=1, column=5, sticky="w")

        tk.Label(row, text="Vermelha:", bg=BG_APP).grid(row=1, column=6, sticky="e", padx=(16,2))
        verm_var = tk.IntVar(value=0)
        tk.Button(row, text="−", command=lambda: _dec("vermelha"), **ESTILO_BOTAO_TINY)\
            .grid(row=1, column=7, sticky="w")
        lbl_verm = tk.Label(row, textvariable=verm_var, bg=BG_APP, width=3, anchor="center")
        lbl_verm.grid(row=1, column=8, padx=2)
        tk.Button(row, text="+", command=lambda: _inc("vermelha"), **ESTILO_BOTAO_TINY)\
            .grid(row=1, column=9, sticky="w")

        lbl_aj = tk.Label(row, text="Ajuste: R$ 0,00", bg=BG_APP, font=("Segoe UI", 10, "bold"))
        lbl_nv = tk.Label(row, text=f"Novo Total (LÍQ.): {money(row_data['liquido_base'])}",
                          bg=BG_APP, font=("Segoe UI", 10, "bold"))
        lbl_aj.grid(row=1, column=10, sticky="w", padx=(18,2))
        lbl_nv.grid(row=1, column=11, sticky="w", padx=(12,2))

        def _recalc():
            row_data["ajuste"] = (row_data["vermelha"] - row_data["preta"]) * row_data["valor_dia"]
            row_data["novo_liquido"] = max(0.0, row_data["liquido_base"] + row_data["ajuste"])
            lbl_aj.config(text=f"Ajuste: {money(row_data['ajuste'])}")
            lbl_nv.config(text=f"Novo Total (LÍQ.): {money(row_data['novo_liquido'])}")

        def _inc(which):
            row_data[which] += 1
            (preta_var if which == "preta" else verm_var).set(row_data[which])
            _recalc()

        def _dec(which):
            row_data[which] = max(0, row_data[which]-1)
            (preta_var if which == "preta" else verm_var).set(row_data[which])
            _recalc()

        row_data.update({
            "row": row,
            "preta_var": preta_var,
            "verm_var": verm_var,
            "recalc": _recalc
        })
        _recalc()
        linhas_da.append(row_data)

    def _load_da():
        # limpa UI
        for it in list(linhas_da):
            try:
                it["row"].destroy()
            except Exception:
                pass
        linhas_da.clear()

        regs = _carregar_militares()
        linhas_ins = []
        for d in regs:
            if not str(d.get("recebe_aux_transporte","Não")).lower().startswith("s"):
                continue
            posto = d["Posto"]

            total_liq = _to_float(d.get("valor_aux_transporte",0.0), 0.0)  # JÁ é líquido
            valor_dia_liq = total_liq / 22.0 if total_liq else 0.0

            linhas_ins.append({
                "ID": d["ID"], "Nome": d["Nome"], "Posto": posto,
                "CPF": d["CPF"], "PREC": d["PREC"],
                "valor_dia": valor_dia_liq, "liquido_base": total_liq
            })

        # ordena por hierarquia e nome
        linhas_ins.sort(key=lambda x: (_posto_key(x["Posto"]), x["Nome"].lower()))

        for base in linhas_ins:
            _linha_da(inner, base)

    def _filtrar_da(_=None):
        termo = (busca_da.get() or "").strip().lower()
        for it in linhas_da:
            visivel = (termo in str(it["Nome"]).lower()) if termo else True
            it["row"].pack_forget()
            if visivel:
                it["row"].pack(fill="x", pady=4)

    btn_reload_da.config(command=_load_da)
    ent_da.bind("<KeyRelease>", _filtrar_da)  # busca em tempo real
    _load_da()

    def _formatar_cpf(cpf: str) -> str:
        s = "".join(ch for ch in str(cpf) if ch.isdigit())
        if len(s) == 11:
            return f"{s[0:3]}.{s[3:6]}.{s[6:9]}-{s[9:11]}"
        return cpf

    def _gerar_boletim():
        texto = ""
        for it in linhas_da:
            desconto = max(0.0, (it["preta"] - it["vermelha"]) * it["valor_dia"])
            if desconto <= 0:
                continue
            abrev = ABREV_POSTOS.get(it["Posto"], it["Posto"])
            nome_up = str(it["Nome"]).upper()
            prec = it["PREC"]
            cpf_fmt = _formatar_cpf(it["CPF"])
            texto += f"{abrev} {nome_up}\n"
            texto += f"Prec-CP {prec} CPF {cpf_fmt}\n"
            texto += f"Valor: {money(desconto)}\n\n"

        if not texto:
            messagebox.showinfo("Info", "Nenhum desconto a anular encontrado.", parent=win)
            return

        dlg = tk.Toplevel(win)
        dlg.title("Boletim - Despesa a Anular")
        dlg.geometry("720x520")
        dlg.configure(bg=BG_APP)
        dlg.grab_set()

        tk.Label(dlg, text="Prévia do Boletim", bg=BG_APP, fg=FG_TIT,
                 font=("Segoe UI", 14, "bold")).pack(pady=(12,6))

        txt = tk.Text(dlg, wrap="word", font=("Segoe UI", 11))
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", texto)

        barx = tk.Frame(dlg, bg=BG_APP); barx.pack(pady=6)
        def _copiar():
            dlg.clipboard_clear()
            dlg.clipboard_append(txt.get("1.0", "end-1c"))
            messagebox.showinfo("OK", "Texto copiado para a área de transferência.", parent=dlg)
        def _salvar_arquivo():
            try:
                path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                    filetypes=[("Texto", "*.txt")], parent=dlg)
                if not path: return
                with open(path, "w", encoding="utf-8") as f:
                    f.write(txt.get("1.0", "end-1c"))
                messagebox.showinfo("OK", f"Arquivo salvo em:\n{path}", parent=dlg)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar arquivo:\n{e}", parent=dlg)

        tk.Button(barx, text="Copiar", command=_copiar, **ESTILO_BOTAO_SM).pack(side="left", padx=6)
        tk.Button(barx, text="Salvar .txt", command=_salvar_arquivo, **ESTILO_BOTAO_SM).pack(side="left", padx=6)

    btn_boletim.config(command=_gerar_boletim)

# ---------- Dialog para editar e salvar no DB ----------
def _abrir_dialog_calculadora(parent, militar_id, nome, posto, total_inicial=0.0, on_saved=None):
    """total_inicial aqui é LÍQUIDO já salvo/importado."""
    BG_APP = "#e3f2fd"; FG_TIT = "#0d47a1"
    dlg = tk.Toplevel(parent)
    dlg.title(f"Editar Auxílio - {nome}")
    dlg.geometry("600x560")
    dlg.configure(bg=BG_APP)
    dlg.grab_set()

    tk.Label(dlg, text=f"{nome}  |  {posto}", bg=BG_APP, fg=FG_TIT,
             font=("Segoe UI", 14, "bold")).pack(pady=10)

    box = tk.Frame(dlg, bg=BG_APP); box.pack(pady=8, anchor="w")
    linhas = []
    def add_linha(valor=""):
        row = tk.Frame(box, bg=BG_APP); row.pack(pady=4, anchor="w")
        idx = len(linhas)+1
        tk.Label(row, text=f"Ônibus {idx}:", bg=BG_APP, font=("Segoe UI", 11)).pack(side="left", padx=(0,6))
        v = tk.StringVar(value=str(valor))
        e, v = money_entry(row, textvariable=v, width=12)  # ENTRADA MONETÁRIA
        e.pack(side="left")
        btn = tk.Button(row, text="Remover", command=lambda r=row, var=v: _remover(r, var),
                        bg="#e53935", fg="white", bd=0, cursor="hand2", font=("Segoe UI", 11), width=10)
        btn.pack(side="left", padx=8)
        linhas.append((row, v))
    def _remover(row, var):
        row.destroy()
        for i,(r,v) in enumerate(list(linhas)):
            if v is var:
                linhas.remove((r,v)); break

    tk.Button(dlg, text="Adicionar", command=add_linha,
              bg="#1976d2", fg="white", bd=0, cursor="hand2", font=("Segoe UI", 12), width=18).pack(pady=6)

    res = tk.Frame(dlg, bg=BG_APP); res.pack(pady=8, anchor="w")
    lbl_dia  = tk.Label(res, text="Valor do dia (BRUTO pelas tarifas): —", bg=BG_APP, font=("Segoe UI", 12)); lbl_dia.pack(anchor="w")
    lbl_tot  = tk.Label(res, text=f"Total mensal (atual LÍQ.): {money(total_inicial)}", bg=BG_APP, font=("Segoe UI", 12)); lbl_tot.pack(anchor="w")
    lbl_cota = tk.Label(res, text="Cota-parte (22d): —", bg=BG_APP, font=("Segoe UI", 12)); lbl_cota.pack(anchor="w")
    lbl_aux  = tk.Label(res, text="Auxílio Transporte (LÍQ. calculado): —", bg=BG_APP, font=("Segoe UI", 13, "bold")); lbl_aux.pack(anchor="w")

    def _calc_preview():
        tarifas = [v.get() for _,v in linhas if v.get().strip()!=""]
        soldo = obter_soldo_por_posto(posto) or 0.0
        if not tarifas:
            valor_dia_liq = _to_float(total_inicial) / 22.0 if _to_float(total_inicial) else 0.0
            lbl_dia.config(text="Valor do dia (BRUTO pelas tarifas): —")
            lbl_tot.config(text=f"Total mensal (atual LÍQ.): {money(total_inicial)}")
            lbl_cota.config(text="Cota-parte (22d): —")
            lbl_aux.config(text=f"Auxílio Transporte (LÍQ. calculado): {money(total_inicial)}")
            return {"valor_dia": valor_dia_liq, "aux": _to_float(total_inicial, 0.0)}
        else:
            r = calcular_por_tarifas(tarifas, soldo)
            lbl_dia.config(text=f"Valor do dia (BRUTO pelas tarifas): {money(r.get('valor_dia',0.0))}")
            lbl_tot.config(text=f"Total mensal (22d BRUTO): {money(r['total_mes_22'])}")
            lbl_cota.config(text=f"Cota-parte (22d): {money(r['cota22'])}")
            lbl_aux.config(text=f"Auxílio Transporte (LÍQ. calculado): {money(r['aux'])}")
            return r

    btns = tk.Frame(dlg, bg=BG_APP); btns.pack(pady=10)
    tk.Button(btns, text="Calcular prévia", command=_calc_preview,
              bg="#1976d2", fg="white", bd=0, cursor="hand2", font=("Segoe UI", 12), width=16).pack(side="left", padx=6)

    def _salvar():
        r = _calc_preview()
        # GRAVA SEMPRE O LÍQUIDO (coerente com importação)
        total_liquido = _to_float(r.get("aux", total_inicial), 0.0)
        try:
            atualizar_aux_transporte(int(militar_id), float(total_liquido))
            messagebox.showinfo("OK", "Auxílio (LÍQ.) atualizado no banco.", parent=dlg)
            if callable(on_saved): on_saved()
            dlg.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar no banco:\n{e}", parent=dlg)

    tk.Button(btns, text="Salvar no banco", command=_salvar,
              bg="#2e7d32", fg="white", bd=0, cursor="hand2", font=("Segoe UI", 12), width=16).pack(side="left", padx=6)

    add_linha("5,75"); add_linha("5,75")
