import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from database.db import buscar_todos, excluir_militar, atualizar_militar
from impor_export import exportar_para_excel, importar_de_excel
import os
import re

# ---- colunas completas (do banco) ----
COLS_FULL = [
    "ID", "Posto", "Nome", "Nome de Guerra", "CPF", "PREC-CP", "IDT", "Banco",
    "Agência", "Conta", "Foto", "Ano de Formação", "Data de Nascimento", "Data de Praça",
    "Endereço", "CEP", "Recebe Pré Escolar", "Valor Pré Escolar",
    "Recebe Auxílio Transporte", "Valor Auxílio Transporte", "Possui PNR"
]

# ---- colunas visíveis na lista ----
COLS_VIEW = ["Posto", "Ano", "Nome", "Nome de Guerra", "CPF", "PREC-CP", "IDT Militar"]

# mapeamento (índices do registro completo -> ordem das colunas visíveis)
IDX_ID    = 0
IDX_POSTO = 1
IDX_NOME  = 2
IDX_NG    = 3
IDX_CPF   = 4
IDX_PREC  = 5
IDX_IDT   = 6
IDX_FOTO  = 10
IDX_ANO   = 11

postos = [
    "Capitão", "1º Tenente", "2º Tenente", "Subtenente",
    "1º Sargento", "2º Sargento", "3º Sargento",
    "Cabo Efetivo Profissional", "Soldado Efetivo Profissional", "Soldado Efetivo Variável"
]
ordem_postos = {posto: i+1 for i, posto in enumerate(postos)}

cores_postos = {
    "Capitão": "#A5D6A7",
    "1º Tenente": "#C5E1A5",
    "2º Tenente": "#E6EE9C",
    "Subtenente": "#FFF59D",
    "1º Sargento": "#FFE082",
    "2º Sargento": "#FFCC80",
    "3º Sargento": "#FFAB91",
    "Cabo Efetivo Profissional": "#CE93D8",
    "Soldado Efetivo Profissional": "#9FA8DA",
    "Soldado Efetivo Variável": "#80DEEA"
}

bancos = [
    "001 - Banco do Brasil S.A", "341 - Itaú Unibanco S.A",
    "033 - Banco Santander (Brasil) S.A", "237 - Banco Bradesco S.A",
    "104 - Caixa Econômica Federal"
]


def abrir_listagem():
    janela = tk.Toplevel()
    janela.title("Lista de Militares")
    janela.configure(bg="#e3f2fd")
    janela.minsize(1100, 600)
    janela.resizable(True, True)
    try:
        janela.state("zoomed")
    except Exception:
        pass

    # ---------- Header ----------
    header = tk.Frame(janela, bg="#1565c0")
    header.pack(fill="x")
    tk.Label(header, text="📋 Lista de Militares", bg="#1565c0", fg="white",
             font=("Segoe UI", 20, "bold")).pack(side="left", padx=18, pady=12)

    # ---------- Toolbar ----------
    toolbar = tk.Frame(janela, bg="#e3f2fd")
    toolbar.pack(fill="x", padx=16, pady=(10, 6))

    tk.Label(toolbar, text="Buscar Nome/Nome de Guerra:", bg="#e3f2fd",
             font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
    entrada_busca = tk.Entry(toolbar, width=38, font=("Segoe UI", 11))
    entrada_busca.grid(row=0, column=1, padx=(8, 12), sticky="w")

    btn_limpar = tk.Button(toolbar, text="✖ Limpar", font=("Segoe UI", 10, "bold"),
                           bg="#90a4ae", fg="white", bd=0, cursor="hand2",
                           padx=10, pady=6)
    btn_limpar.grid(row=0, column=2, padx=(0, 16))

    tk.Label(toolbar, text="Filtrar por Posto:", bg="#e3f2fd",
             font=("Segoe UI", 11, "bold")).grid(row=0, column=3, sticky="w")
    combo_postos = ttk.Combobox(toolbar, values=["Todos"] + postos, font=("Segoe UI", 11),
                                state="readonly", width=33)
    combo_postos.set("Todos")
    combo_postos.grid(row=0, column=4, padx=(8, 12), sticky="w")

    right_btns = tk.Frame(toolbar, bg="#e3f2fd")
    right_btns.grid(row=0, column=5, sticky="e")
    for i in range(6):
        toolbar.grid_columnconfigure(i, weight=1)

    def mkbtn(parent, text, bg, fg="white", cmd=None):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                         font=("Segoe UI", 10, "bold"), bd=0, cursor="hand2",
                         padx=14, pady=8, activebackground=bg)

    btn_exportar = mkbtn(right_btns, "📤 Exportar Excel", "#2e7d32")
    btn_importar = mkbtn(right_btns, "📥 Importar Excel", "#1976d2")
    btn_editar   = mkbtn(right_btns, "✏️ Editar", "#ffc107", fg="black")
    btn_excluir  = mkbtn(right_btns, "❌ Excluir", "#f44336")
    btn_qtd      = mkbtn(right_btns, "📊 Quantidade por Posto", "#673ab7")
    btn_carteira = mkbtn(right_btns, "👤 Carteira", "#0288d1")
    for i, b in enumerate((btn_exportar, btn_importar, btn_editar, btn_excluir, btn_qtd, btn_carteira)):
        b.grid(row=0, column=i, padx=5)

    # ---------- Treeview ----------
    estilo = ttk.Style(janela)
    try:
        estilo.theme_use("clam")
    except Exception:
        pass
    estilo.configure("Treeview", font=("Segoe UI", 11), rowheight=28)
    estilo.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#e8f0fe")
    estilo.map("Treeview", background=[("selected", "#b3e5fc")])

    center = tk.Frame(janela, bg="#e3f2fd")
    center.pack(fill="both", expand=True, padx=16, pady=(0, 12))
    frame_tree = tk.Frame(center, bg="#e3f2fd")
    frame_tree.pack(expand=True, fill="both")

    tree = ttk.Treeview(frame_tree, columns=COLS_VIEW, show="headings", selectmode="browse")
    vsb = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame_tree, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    frame_tree.grid_columnconfigure(0, weight=1)
    frame_tree.grid_rowconfigure(0, weight=1)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    # ---- larguras mínimas + máximas + crescimento proporcional ----
    MINW = {
        "Posto": 120,
        "Ano": 60,
        "Nome": 180,
        "Nome de Guerra": 150,
        "CPF": 170,
        "PREC-CP": 160,
        "IDT Militar": 160
    }
    MAXW = {"Nome": 320, "Nome de Guerra": 240}
    GROW_COLS = ("Nome", "Nome de Guerra", "CPF", "PREC-CP", "IDT Militar")
    GROW_WEIGHTS = {"Nome": 2, "Nome de Guerra": 1, "CPF": 1, "PREC-CP": 1, "IDT Militar": 1}

    def auto_resize(_=None):
        tree.update_idletasks()
        total = tree.winfo_width()
        base = sum(MINW[c] for c in COLS_VIEW)
        extra = max(0, total - base - 20)
        widths = dict(MINW)
        if extra > 0:
            total_w = sum(GROW_WEIGHTS.get(c, 0) for c in GROW_COLS) or 1
            distrib, usado = {}, 0
            for c in GROW_COLS:
                add = int(extra * (GROW_WEIGHTS.get(c, 0) / total_w))
                distrib[c] = add; usado += add
            sobra = extra - usado
            if sobra > 0 and "Nome" in distrib:
                distrib["Nome"] += sobra
            for c, add in distrib.items():
                widths[c] = widths.get(c, 0) + add
            for c, cap in MAXW.items():
                if widths.get(c, 0) > cap:
                    widths[c] = cap
        for col in COLS_VIEW:
            anchor = "center" if col in ("Ano", "CPF", "PREC-CP", "IDT Militar") else "w"
            stretch = col in GROW_COLS
            tree.heading(col, text=col, command=lambda _c=col: ordenar_coluna(_c))
            tree.column(col, anchor=anchor, width=widths[col], stretch=stretch)

    frame_tree.bind("<Configure>", auto_resize)

    # ---------- Status ----------
    status_var = tk.StringVar(value="")
    tk.Label(janela, textvariable=status_var, anchor="w",
             font=("Segoe UI", 9), bg="#eaf3ff", fg="#37474f").pack(fill="x", side="bottom")

    # ---------- Dados e estado ----------
    dados_completos = []   # lista com as linhas do banco (completas)
    item_full = {}         # iid -> linha completa

    def formatar_cpf(cpf):
        cpf = str(cpf or "")
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 and cpf.isdigit() else cpf

    def cpf_sem_pontuacao(cpf):
        return re.sub(r"\D+", "", str(cpf or ""))

    def atualizar_status(lista):
        status_var.set(f"Mostrando {len(lista)} de {len(dados_completos)} registros.")

    def carregar_militares():
        nonlocal dados_completos
        dados_completos = sorted(
            buscar_todos(),
            key=lambda m: (ordem_postos.get(m[IDX_POSTO], 999), str(m[IDX_NOME] or "").lower())
        )
        aplicar_filtro()
        auto_resize()

    def montar_linha_visivel(full_row):
        return (
            full_row[IDX_POSTO],
            full_row[IDX_ANO],
            (full_row[IDX_NOME] or "").upper(),
            (full_row[IDX_NG] or "").upper(),
            formatar_cpf(full_row[IDX_CPF]),
            full_row[IDX_PREC],
            full_row[IDX_IDT],
        )

    def atualizar_treeview(lista_full):
        tree.delete(*tree.get_children())
        item_full.clear()
        for full in lista_full:
            vis = montar_linha_visivel(full)
            cor = cores_postos.get(full[IDX_POSTO], "#FFFFFF")
            iid = tree.insert("", "end", values=vis, tags=(cor,))
            tree.tag_configure(cor, background=cor)
            item_full[iid] = full
        atualizar_status(lista_full)

    def aplicar_filtro(_event=None):
        termo = entrada_busca.get().strip().lower()
        filtro_posto = combo_postos.get()
        filtrado = dados_completos
        if termo:
            filtrado = [m for m in filtrado
                        if termo in (str(m[IDX_NOME] or "").lower())
                        or termo in (str(m[IDX_NG] or "").lower())]
        if filtro_posto != "Todos":
            filtrado = [m for m in filtrado if m[IDX_POSTO] == filtro_posto]
        atualizar_treeview(filtrado)

    def limpar_filtros():
        entrada_busca.delete(0, "end")
        combo_postos.set("Todos")
        aplicar_filtro()

    entrada_busca.bind("<KeyRelease>", aplicar_filtro)
    combo_postos.bind("<<ComboboxSelected>>", aplicar_filtro)
    btn_limpar.config(command=limpar_filtros)

    # ---------- Ordenação ----------
    def ordenar_coluna(col, reverso=False):
        dados = [(tree.set(k, col), k) for k in tree.get_children("")]
        if col == "Posto":
            dados.sort(key=lambda x: ordem_postos.get(x[0], 999), reverse=reverso)
        elif col == "Ano":
            def ano_key(v):
                try:
                    return int(v[0])
                except Exception:
                    return 99999
            dados.sort(key=ano_key, reverse=reverso)
        else:
            dados.sort(key=lambda x: str(x[0]).lower(), reverse=reverso)
        for i, (_, k) in enumerate(dados):
            tree.move(k, "", i)
        tree.heading(col, command=lambda: ordenar_coluna(col, not reverso))

    # ---------- Preview da foto ----------
    preview = tk.Toplevel(janela)
    preview.withdraw()
    preview.overrideredirect(True)
    label_preview = tk.Label(preview, bg="white", relief="solid", borderwidth=1)
    label_preview.pack()

    def mostrar_preview(event):
        iid = tree.identify_row(event.y)
        if not iid or iid not in item_full:
            preview.withdraw()
            return
        full = item_full[iid]
        caminho_foto = full[IDX_FOTO]
        if caminho_foto and os.path.exists(caminho_foto):
            try:
                img = Image.open(caminho_foto)
                img.thumbnail((260, 260), Image.LANCZOS)
                foto_tk = ImageTk.PhotoImage(img)
                label_preview.configure(image=foto_tk)
                label_preview.image = foto_tk
                preview.geometry(f"+{event.x_root+20}+{event.y_root}")
                preview.deiconify()
            except Exception:
                preview.withdraw()
        else:
            preview.withdraw()

    tree.bind("<Motion>", mostrar_preview)
    tree.bind("<Leave>", lambda e: preview.withdraw())

    # ---------- Seleção de célula p/ cópia ----------
    last_click = {"iid": None, "col": None}  # col = nome da coluna visível (ex.: "CPF")

    def on_click(event):
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        iid = tree.identify_row(event.y)
        colid = tree.identify_column(event.x)   # '#1'..'#N'
        try:
            col_index = int(colid.replace("#", "")) - 1
            col_name = COLS_VIEW[col_index]
        except Exception:
            col_name = None
        if iid:
            tree.selection_set(iid)
            last_click["iid"] = iid
            last_click["col"] = col_name

    tree.bind("<Button-1>", on_click, add="+")  # mantém seleção + guarda coluna

    # ---------- Cópia para área de transferência ----------
    SEP = "\t"  # separados por TAB (bom para colar no Excel)

    def copiar_valor_celula():
        iid = last_click["iid"] or (tree.selection()[0] if tree.selection() else None)
        col = last_click["col"]
        if not iid or not col:
            return
        val = tree.set(iid, col)
        janela.clipboard_clear()
        janela.clipboard_append(str(val))
        status_var.set(f"Copiado: {col}")

    def copiar_linha_visivel():
        iid = last_click["iid"] or (tree.selection()[0] if tree.selection() else None)
        if not iid:
            return
        vals = tree.item(iid)["values"]
        txt = SEP.join(str(v) for v in vals)
        janela.clipboard_clear()
        janela.clipboard_append(txt)
        status_var.set("Copiada linha (colunas visíveis).")

    def cpf_sem_pontuacao_local(cpf):
        return re.sub(r"\D+", "", str(cpf or ""))

    def copiar_cpf_sem_pontos():
        iid = last_click["iid"] or (tree.selection()[0] if tree.selection() else None)
        if not iid:
            return
        full = item_full.get(iid)
        if not full:
            return
        janela.clipboard_clear()
        janela.clipboard_append(cpf_sem_pontuacao_local(full[IDX_CPF]))
        status_var.set("CPF (sem pontuação) copiado.")

    def copiar_prec():
        iid = last_click["iid"] or (tree.selection()[0] if tree.selection() else None)
        if not iid:
            return
        full = item_full.get(iid)
        if not full:
            return
        janela.clipboard_clear()
        janela.clipboard_append(str(full[IDX_PREC] or ""))
        status_var.set("PREC-CP copiado.")

    def copiar_idt():
        iid = last_click["iid"] or (tree.selection()[0] if tree.selection() else None)
        if not iid:
            return
        full = item_full.get(iid)
        if not full:
            return
        janela.clipboard_clear()
        janela.clipboard_append(str(full[IDX_IDT] or ""))
        status_var.set("IDT copiado.")

    # atalhos
    janela.bind("<Control-c>", lambda e: copiar_valor_celula())
    janela.bind("<Control-C>", lambda e: copiar_valor_celula())
    janela.bind("<Control-Shift-c>", lambda e: copiar_linha_visivel())
    janela.bind("<Control-Shift-C>", lambda e: copiar_linha_visivel())

    # ---------- Ações ----------
    def _get_full_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um militar.", parent=janela)
            return None
        iid = sel[0]
        return item_full.get(iid)

    def excluir():
        full = _get_full_selected()
        if not full:
            return
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir o militar selecionado?", parent=janela):
            excluir_militar(full[IDX_ID])
            carregar_militares()

    def mostrar_quantidade():
        contagem = {posto: 0 for posto in postos}
        for m in dados_completos:
            if m[IDX_POSTO] in contagem:
                contagem[m[IDX_POSTO]] += 1
        total = sum(contagem.values())

        winq = tk.Toplevel(janela)
        winq.title("Quantidade de Militares por Posto")
        winq.geometry("420x520")
        winq.configure(bg="#f5f5f5")
        winq.transient(janela)
        winq.grab_set()

        tk.Label(winq, text="Quantidade de Militares por Posto",
                 font=("Segoe UI", 14, "bold"), bg="#f5f5f5").pack(pady=15)

        tree_qtd = ttk.Treeview(winq, columns=("Posto", "Quantidade"), show="headings", height=15)
        tree_qtd.heading("Posto", text="Posto")
        tree_qtd.heading("Quantidade", text="Quantidade")
        tree_qtd.column("Posto", anchor="w", width=260)
        tree_qtd.column("Quantidade", anchor="center", width=110)
        tree_qtd.pack(padx=15, pady=10, fill="both", expand=True)

        for posto, qtd in contagem.items():
            tree_qtd.insert("", "end", values=(posto, qtd))
        tree_qtd.insert("", "end", values=("TOTAL", total))

    # ======== CARTEIRA ========
    def mostrar_carteira():
        full = _get_full_selected()
        if not full:
            return
        dados = full

        # ------- janela -------
        win = tk.Toplevel(janela)
        win.title(f"Carteira – {dados[IDX_NOME] or ''}")
        win.geometry("1200x900")
        win.configure(bg="#e3f2fd")
        win.transient(janela)
        win.grab_set()

        # estilos
        style = ttk.Style(win)
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#0d47a1", background="#e3f2fd")
        style.configure("Card.TFrame", background="white")
        style.configure("Sub.TLabel", font=("Segoe UI", 11, "bold"), background="white", foreground="#37474f")
        style.configure("Value.TEntry", fieldbackground="white", foreground="#222")
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"),
                        padding=(12, 6), foreground="white", background="#1976d2", borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#1565c0"), ("pressed", "#1565c0")])
        style.configure("Ghost.TButton", font=("Segoe UI", 10),
                        padding=(8, 4), foreground="#1976d2", background="#eaf3ff", borderwidth=0)
        style.map("Ghost.TButton",
                  foreground=[("active", "white"), ("pressed", "white")],
                  background=[("active", "#1976d2"), ("pressed", "#1976d2")])

        status_var = tk.StringVar(value="Dica: selecione e use Ctrl+C, dê duplo-clique ou clique direito para copiar.")
        def set_status(msg): status_var.set(msg)

        def copy_text(txt, rotulo="Valor"):
            try:
                win.clipboard_clear()
                win.clipboard_append(str(txt if txt is not None else ""))
                set_status(f"Copiado: {rotulo}")
            except Exception:
                messagebox.showinfo("Copiar", "Não foi possível copiar para a área de transferência.", parent=win)

        # menu de contexto (Copiar)
        menu_ctx = tk.Menu(win, tearoff=0)
        def copy_selection_or_all():
            w = win.focus_get()
            sel = None
            # tenta pegar seleção de Entry/Text
            try:
                if isinstance(w, (tk.Entry, ttk.Entry, tk.Text)):
                    sel = w.selection_get()
            except Exception:
                sel = None
            # se não houver seleção, copia inteiro (Entry)
            if not sel:
                try:
                    if isinstance(w, (tk.Entry, ttk.Entry)):
                        sel = w.get()
                except Exception:
                    pass
            if sel:
                copy_text(sel, "Seleção")
        menu_ctx.add_command(label="Copiar", command=copy_selection_or_all)

        ttk.Label(win, text="Carteira do Militar", style="Title.TLabel").pack(pady=(16, 8))

        # container com scroll
        outer = ttk.Frame(win, style="Card.TFrame")
        outer.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)

        canvas = tk.Canvas(outer, bg="#e3f2fd", highlightthickness=0)
        ysb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, style="Card.TFrame")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=ysb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")

        # ---------- helpers ----------
        selectables = []  # entradas p/ habilitar Ctrl+C e menu
        def make_line(parent, r, rotulo, valor, copy_btn=False):
            ttk.Label(parent, text=rotulo, style="Sub.TLabel").grid(row=r, column=0, sticky="e", padx=(8,10), pady=6)
            wrap = ttk.Frame(parent, style="Card.TFrame"); wrap.grid(row=r, column=1, sticky="w", padx=(0,8), pady=6)

            var = tk.StringVar(value=("—" if (valor is None or valor == "") else str(valor)))
            ent = ttk.Entry(wrap, textvariable=var, width=60, state="readonly", style="Value.TEntry")
            ent.pack(side="left")
            selectables.append(ent)

            # eventos: duplo-clique / clique direito
            def _copy(_=None): copy_text(var.get(), rotulo.strip(":"))
            ent.bind("<Double-Button-1>", _copy)
            ent.bind("<Button-3>", lambda e: (ent.focus_set(), menu_ctx.tk_popup(e.x_root, e.y_root)))

            if copy_btn:
                ttk.Button(wrap, text="📋", style="Ghost.TButton", width=3, command=_copy).pack(side="left", padx=(8,0))
            return f"{rotulo} {var.get()}"

        # ---------- topo: foto + identificação ----------
        top = ttk.Frame(inner, style="Card.TFrame")
        top.pack(fill="x", padx=8, pady=8)

        foto_card = ttk.Frame(top, style="Card.TFrame")
        foto_card.pack(side="left", padx=(0, 10), pady=4)
        foto_wrap = tk.Frame(foto_card, bg="#f1f5fb", highlightthickness=1, highlightbackground="#dfe7f3")
        foto_wrap.pack(padx=8, pady=8)
        lbl_foto = tk.Label(foto_wrap, bg="#f1f5fb"); lbl_foto.pack(padx=10, pady=10)

        caminho_foto = dados[IDX_FOTO]
        def _load_photo(path):
            if path and os.path.exists(path):
                try:
                    img = Image.open(path)
                    img.thumbnail((320, 320), Image.LANCZOS)
                    ph = ImageTk.PhotoImage(img)
                    lbl_foto.configure(image=ph, text="")
                    lbl_foto.image = ph
                    return
                except Exception:
                    pass
            lbl_foto.configure(image="", text="Sem foto", font=("Segoe UI", 12, "bold"))
            lbl_foto.image = None
        _load_photo(caminho_foto)

        # card dados básicos
        id_card = ttk.Frame(top, style="Card.TFrame"); id_card.pack(side="left", fill="both", expand=True, pady=4)
        id_card.grid_columnconfigure(0, weight=0); id_card.grid_columnconfigure(1, weight=1)

        coletor = []
        coletor.append(make_line(id_card, 0, "Posto/Graduação:", dados[IDX_POSTO]))
        coletor.append(make_line(id_card, 1, "Ano de Formação:", dados[IDX_ANO]))
        coletor.append(make_line(id_card, 2, "Nome:", dados[IDX_NOME], copy_btn=True))
        coletor.append(make_line(id_card, 3, "Nome de Guerra:", dados[IDX_NG], copy_btn=True))
        coletor.append(make_line(id_card, 4, "CPF:", dados[IDX_CPF], copy_btn=True))
        coletor.append(make_line(id_card, 5, "PREC-CP:", dados[IDX_PREC], copy_btn=True))
        coletor.append(make_line(id_card, 6, "IDT Militar:", dados[IDX_IDT], copy_btn=True))

        ttk.Separator(inner).pack(fill="x", padx=8, pady=8)

        # ---------- cards secundários ----------
        grid = ttk.Frame(inner, style="Card.TFrame")
        grid.pack(fill="x", padx=8, pady=(0, 8))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        card1 = ttk.Frame(grid, style="Card.TFrame"); card1.grid(row=0, column=0, sticky="nsew", padx=(0,6))
        ttk.Label(card1, text="Dados Bancários e Endereço", style="Sub.TLabel").pack(anchor="w", padx=10, pady=(10,0))
        wrap1 = ttk.Frame(card1, style="Card.TFrame"); wrap1.pack(fill="x", padx=8, pady=8)
        coletor.append(make_line(wrap1, 0, "Banco:", dados[7]))
        coletor.append(make_line(wrap1, 1, "Agência:", dados[8]))
        coletor.append(make_line(wrap1, 2, "Conta:", dados[9]))
        coletor.append(make_line(wrap1, 3, "Endereço:", dados[14], copy_btn=True))
        coletor.append(make_line(wrap1, 4, "CEP:", dados[15], copy_btn=True))

        card2 = ttk.Frame(grid, style="Card.TFrame"); card2.grid(row=0, column=1, sticky="nsew", padx=(6,0))
        ttk.Label(card2, text="Benefícios", style="Sub.TLabel").pack(anchor="w", padx=10, pady=(10,0))
        wrap2 = ttk.Frame(card2, style="Card.TFrame"); wrap2.pack(fill="x", padx=8, pady=8)
        coletor.append(make_line(wrap2, 0, "Recebe Pré-Escolar:", dados[16]))
        coletor.append(make_line(wrap2, 1, "Valor Pré-Escolar:", dados[17]))
        coletor.append(make_line(wrap2, 2, "Recebe Auxílio Transp.:", dados[18]))
        coletor.append(make_line(wrap2, 3, "Valor Auxílio Transp.:", dados[19]))
        coletor.append(make_line(wrap2, 4, "Possui PNR:", dados[20]))

        card3 = ttk.Frame(inner, style="Card.TFrame"); card3.pack(fill="x", padx=8, pady=(0,8))
        ttk.Label(card3, text="Datas", style="Sub.TLabel").pack(anchor="w", padx=10, pady=(10,0))
        wrap3 = ttk.Frame(card3, style="Card.TFrame"); wrap3.pack(fill="x", padx=8, pady=8)
        coletor.append(make_line(wrap3, 0, "Data de Nascimento:", dados[12]))
        coletor.append(make_line(wrap3, 1, "Data de Praça:", dados[13]))

        # rodapé
        footer = ttk.Frame(win, style="Card.TFrame"); footer.pack(fill="x", padx=16, pady=(0,8))
        ttk.Button(footer, text="Copiar CPF", style="Ghost.TButton",
                   command=lambda: copy_text(dados[IDX_CPF], "CPF")).pack(side="left", padx=(0,6))
        ttk.Button(footer, text="Copiar PREC-CP", style="Ghost.TButton",
                   command=lambda: copy_text(dados[IDX_PREC], "PREC-CP")).pack(side="left", padx=6)
        ttk.Button(footer, text="Copiar IDT", style="Ghost.TButton",
                   command=lambda: copy_text(dados[IDX_IDT], "IDT")).pack(side="left", padx=6)

        def copiar_tudo():
            txt = "\n".join(coletor)
            copy_text(txt, "Todos os dados")
        ttk.Button(footer, text="Copiar tudo", style="Primary.TButton", command=copiar_tudo).pack(side="right")
        ttk.Button(footer, text="Fechar", style="Primary.TButton", command=win.destroy).pack(side="right", padx=(0,8))

        # barra de status
        ttk.Label(win, textvariable=status_var, background="#e3f2fd", foreground="#37474f").pack(fill="x", padx=16, pady=(0,12))

        # habilita Ctrl+C nas entradas e menu de contexto com clique direito
        def bind_copy_shortcuts(widget):
            widget.bind("<Control-c>", lambda e: copy_selection_or_all())
            widget.bind("<Control-C>", lambda e: copy_selection_or_all())
            widget.bind("<Button-3>", lambda e: (widget.focus_set(), menu_ctx.tk_popup(e.x_root, e.y_root)))
        for w in selectables:
            bind_copy_shortcuts(w)

    # ======== FIM CARTEIRA ========

    def editar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um militar para editar.", parent=janela)
            return
        iid = sel[0]
        full = item_full.get(iid)
        if not full:
            return
        id_militar = full[IDX_ID]
        caminho_foto_atual = full[IDX_FOTO] if (full[IDX_FOTO] and os.path.exists(full[IDX_FOTO])) else ""

        # ------- janela -------
        win = tk.Toplevel(janela)
        win.title("Editar Militar")
        win.geometry("1080x780")
        win.configure(bg="#e3f2fd")
        win.transient(janela)
        win.grab_set()

        style = ttk.Style(win)
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#0d47a1", background="#e3f2fd")
        style.configure("Card.TFrame", background="white")
        style.configure("Field.TLabel", background="white", foreground="#37474f", font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"),
                        padding=(14, 8), foreground="white", background="#1976d2", borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#1565c0"), ("pressed", "#1565c0")])
        style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"),
                        padding=(10, 6), foreground="white", background="#d32f2f", borderwidth=0)
        style.map("Danger.TButton", background=[("active", "#b71c1c"), ("pressed", "#b71c1c")])

        ttk.Label(win, text="Editar dados do militar", style="Title.TLabel").pack(pady=(16, 8))

        # container com scroll
        outer = ttk.Frame(win, style="Card.TFrame"); outer.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        outer.grid_columnconfigure(0, weight=1); outer.grid_rowconfigure(0, weight=1)

        canvas = tk.Canvas(outer, bg="#e3f2fd", highlightthickness=0)
        ysb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, style="Card.TFrame")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=ysb.set)
        canvas.grid(row=0, column=0, sticky="nsew"); ysb.grid(row=0, column=1, sticky="ns")

        # ---------- coluna esquerda: foto ----------
        left = ttk.Frame(inner, style="Card.TFrame")
        left.pack(side="left", padx=(8, 10), pady=8, fill="y")

        foto_box = tk.Frame(left, bg="#f1f5fb", highlightthickness=1, highlightbackground="#dfe7f3")
        foto_box.pack(padx=8, pady=8)
        lbl_foto = tk.Label(foto_box, bg="#f1f5fb"); lbl_foto.pack(padx=12, pady=12)

        def carregar_preview_foto(caminho):
            if caminho and os.path.exists(caminho):
                try:
                    img = Image.open(caminho); img.thumbnail((340, 340), Image.LANCZOS)
                    ph = ImageTk.PhotoImage(img)
                    lbl_foto.configure(image=ph, text=""); lbl_foto.image = ph
                    return
                except Exception:
                    pass
            lbl_foto.configure(image="", text="Sem foto", font=("Segoe UI", 11, "bold")); lbl_foto.image = None

        carregar_preview_foto(caminho_foto_atual)
        nova_foto = {"caminho": caminho_foto_atual}

        btns_foto = ttk.Frame(left, style="Card.TFrame"); btns_foto.pack(pady=(4, 0))
        def _selecionar_foto():
            path = filedialog.askopenfilename(
                title="Selecione a foto",
                filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
            )
            if path:
                nova_foto["caminho"] = path
                carregar_preview_foto(path)

        ttk.Button(btns_foto, text="Selecionar Foto", style="Primary.TButton",
                command=_selecionar_foto).pack(fill="x", padx=4, pady=2)
        ttk.Button(btns_foto, text="Remover Foto", style="Danger.TButton",
                command=lambda: (nova_foto.update({"caminho": ""}), carregar_preview_foto(""))).pack(fill="x", padx=4, pady=2)

        # ---------- coluna direita: formulário em 2 colunas ----------
        right = ttk.Frame(inner, style="Card.TFrame")
        right.pack(side="left", fill="both", expand=True, padx=(10, 8), pady=8)

        form = ttk.Frame(right, style="Card.TFrame")
        form.pack(fill="both", expand=True, padx=8, pady=8)
        for c in (0,1,2,3): form.grid_columnconfigure(c, weight=1)

        campos = {}
        labels_campos = [
            "Posto", "Nome", "Nome de Guerra", "CPF", "PREC-CP", "IDT",
            "Banco", "Agência", "Conta", "Foto",
            "Ano de Formação", "Data de Nascimento", "Data de Praça",
            "Endereço", "CEP", "Recebe Pré Escolar", "Valor Pré Escolar",
            "Recebe Auxílio Transporte", "Valor Auxílio Transporte", "Possui PNR"
        ]
        dados_antigos = full

        def add_input(r, c, titulo, valor, tipo="entry"):
            ttk.Label(form, text=titulo, style="Field.TLabel").grid(row=r, column=c*2, sticky="e", padx=(6,8), pady=(8,2))
            if tipo == "combo":
                cb = ttk.Combobox(form, state="readonly")
                cb.grid(row=r, column=c*2+1, sticky="ew", padx=(0,8), pady=(6,2))
                cb.set(valor or "")
                return cb
            elif tipo == "label":
                lab = ttk.Label(form, text=valor or "—")
                lab.grid(row=r, column=c*2+1, sticky="ew", padx=(0,8), pady=(6,2))
                return lab
            else:
                ent = ttk.Entry(form)
                ent.grid(row=r, column=c*2+1, sticky="ew", padx=(0,8), pady=(6,2))
                ent.insert(0, valor or "")
                return ent

        # linha 0
        campos["Posto"] = add_input(0, 0, "Posto", dados_antigos[IDX_POSTO], "combo")
        campos["Nome"] = add_input(0, 1, "Nome", dados_antigos[IDX_NOME])
        campos["Posto"]["values"] = postos
        # linha 1
        campos["Nome de Guerra"] = add_input(1, 0, "Nome de Guerra", dados_antigos[IDX_NG])
        campos["CPF"] = add_input(1, 1, "CPF", dados_antigos[IDX_CPF])
        # linha 2
        campos["PREC-CP"] = add_input(2, 0, "PREC-CP", dados_antigos[IDX_PREC])
        campos["IDT"] = add_input(2, 1, "IDT", dados_antigos[IDX_IDT])
        # linha 3
        campos["Banco"] = add_input(3, 0, "Banco", dados_antigos[7], "combo")
        campos["Agência"] = add_input(3, 1, "Agência", dados_antigos[8])
        campos["Banco"]["values"] = bancos
        # linha 4
        campos["Conta"] = add_input(4, 0, "Conta", dados_antigos[9])
        campos["Foto"] = add_input(4, 1, "Foto", dados_antigos[IDX_FOTO], "label")
        # linha 5
        campos["Ano de Formação"] = add_input(5, 0, "Ano de Formação", dados_antigos[IDX_ANO])
        campos["Data de Nascimento"] = add_input(5, 1, "Data de Nascimento", dados_antigos[12])
        # linha 6
        campos["Data de Praça"] = add_input(6, 0, "Data de Praça", dados_antigos[13])
        campos["Endereço"] = add_input(6, 1, "Endereço", dados_antigos[14])
        # linha 7
        campos["CEP"] = add_input(7, 0, "CEP", dados_antigos[15])
        campos["Recebe Pré Escolar"] = add_input(7, 1, "Recebe Pré Escolar", dados_antigos[16], "combo")
        campos["Recebe Pré Escolar"]["values"] = ["Sim", "Não"]
        # linha 8
        campos["Valor Pré Escolar"] = add_input(8, 0, "Valor Pré Escolar", dados_antigos[17])
        campos["Recebe Auxílio Transporte"] = add_input(8, 1, "Recebe Auxílio Transporte", dados_antigos[18], "combo")
        campos["Recebe Auxílio Transporte"]["values"] = ["Sim", "Não"]
        # linha 9
        campos["Valor Auxílio Transporte"] = add_input(9, 0, "Valor Auxílio Transporte", dados_antigos[19])
        campos["Possui PNR"] = add_input(9, 1, "Possui PNR", dados_antigos[20], "combo")
        campos["Possui PNR"]["values"] = ["Sim", "Não"]

        # rodapé fixo
        footer = ttk.Frame(win, style="Card.TFrame")
        footer.pack(fill="x", padx=16, pady=10)

        def salvar_edicao():
            valores = []
            for campo in labels_campos:
                widget = campos[campo]
                if campo == "Foto":
                    valores.append(nova_foto["caminho"])
                else:
                    valores.append(widget.get() if hasattr(widget, "get") else widget.cget("text"))
            atualizar_militar(id_militar, tuple(valores))
            messagebox.showinfo("Sucesso", "Militar atualizado com sucesso.", parent=win)
            win.destroy()
            carregar_militares()

        ttk.Button(footer, text="💾 Salvar Alterações", style="Primary.TButton",
                command=salvar_edicao).pack(side="right", padx=6)
        ttk.Button(footer, text="Cancelar", command=win.destroy).pack(side="right", padx=6)

    # botões
    btn_exportar.config(command=lambda: exportar_para_excel(janela))
    btn_importar.config(command=lambda: importar_de_excel(janela, carregar_militares))
    btn_editar.config(command=editar)
    btn_excluir.config(command=excluir)
    btn_qtd.config(command=mostrar_quantidade)
    btn_carteira.config(command=mostrar_carteira)

    # ---------- menu de contexto ----------
    menu = tk.Menu(janela, tearoff=0)
    menu.add_command(label="📋 Copiar valor", command=copiar_valor_celula)
    menu.add_command(label="📋 Copiar linha (TAB)", command=copiar_linha_visivel)
    menu.add_separator()
    menu.add_command(label="📋 Copiar CPF (sem pontuação)", command=copiar_cpf_sem_pontos)
    menu.add_command(label="📋 Copiar PREC-CP", command=copiar_prec)
    menu.add_command(label="📋 Copiar IDT", command=copiar_idt)
    menu.add_separator()
    menu.add_command(label="✏️ Editar", command=editar)
    menu.add_command(label="👤 Carteira", command=mostrar_carteira)
    menu.add_separator()
    menu.add_command(label="❌ Excluir", command=excluir)

    def abrir_menu(evt):
        iid = tree.identify_row(evt.y)
        if iid:
            tree.selection_set(iid)
            colid = tree.identify_column(evt.x)
            try:
                col_index = int(colid.replace("#", "")) - 1
                last_click["col"] = COLS_VIEW[col_index]
            except Exception:
                pass
            last_click["iid"] = iid
            menu.tk_popup(evt.x_root, evt.y_root)

    tree.bind("<Button-3>", abrir_menu)

    # atalhos extras
    janela.bind("<Delete>", lambda e: excluir())
    janela.bind("<Return>", lambda e: mostrar_carteira())
    janela.bind("<Control-e>", lambda e: editar())
    janela.bind("<Control-E>", lambda e: editar())
    janela.bind("<Control-f>", lambda e: (entrada_busca.focus_set(), entrada_busca.select_range(0, "end")))
    janela.bind("<Control-F>", lambda e: (entrada_busca.focus_set(), entrada_busca.select_range(0, "end")))
    # F11 fullscreen
    is_full = {"v": False}
    def toggle_full(_=None):
        is_full["v"] = not is_full["v"]
        janela.attributes("-fullscreen", is_full["v"])
    janela.bind("<F11>", toggle_full)
    janela.bind("<Escape>", lambda e: (janela.attributes("-fullscreen", False), is_full.update(v=False)))

    # start
    carregar_militares()
