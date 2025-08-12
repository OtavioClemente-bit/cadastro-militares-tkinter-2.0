import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database.db import buscar_todos
import json
import os
import time

ARQUIVO_BOLETINS = "boletins.json"

BOLETINS_PADRAO = {
    "Férias - Ordem de Saque": (
        "Seja sacado o adicional de férias, relativo ao ano de 2024, "
        "de acordo com o que prescreve a alínea “d” do inciso II do art. 2º da MP nº 2.215-10, "
        "de 31 AGO 01, em favor dos militares abaixo relacionados, em virtude de estar previsto para gozar férias "
        "(30 dias) no mês de SET 25, no 7º período (15 SE25 a 12 AGO 25), conforme publicado no BI Nr 219, "
        "de 14 NOV 2024, da 4ª Cia PE."
    ),
}

# ------------------- Estilo / Tema -------------------
BG_APP = "#f4f7fb"
FG_TIT = "#0d47a1"
CARD_BG = "white"
ACCENT = "#1976d2"
ACCENT_HOVER = "#1565c0"
WARN = "#e53935"

# ------------------- Tooltip simples -------------------
class _Tooltip:
    def __init__(self, widget, text, delay=350):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwin = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, _=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        if self.tipwin or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") if self.widget.winfo_ismapped() else (0,0,0,0)
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tipwin = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        frm = tk.Frame(tw, bg="#111", bd=1)
        frm.pack()
        lbl = tk.Label(frm, text=self.text, bg="#111", fg="white",
                       font=("Segoe UI", 10), padx=8, pady=4, justify="left")
        lbl.pack()
        tw.wm_geometry(f"+{x}+{y}")

    def _hide(self, _=None):
        self._cancel()
        if self.tipwin:
            self.tipwin.destroy()
            self.tipwin = None

class SistemaBoletim:
    def __init__(self):
        self.janela = tk.Toplevel()
        self.janela.title("Gerar Boletim")
        # janelas menores ainda preservam a barra de botões
        self.janela.geometry("1120x720")
        self.janela.minsize(980, 620)
        self.janela.configure(bg=BG_APP)
        self.janela.grab_set()

        # fontes (com suporte a zoom)
        self.font_size_base = 12
        self.font_size_header = 18
        self._make_fonts()

        # ttk theme
        style = ttk.Style(self.janela)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Frames
        style.configure("Card.TFrame", background=CARD_BG)

        # Labels
        style.configure("Header.TLabel", background=BG_APP, foreground=FG_TIT, font=self.FONT_H1)
        style.configure("Strong.TLabel", background=CARD_BG, foreground=FG_TIT, font=self.FONT_BOLD)
        style.configure("TLabel", background=CARD_BG, font=self.FONT_BASE)

        # Botões
        style.configure("Accent.TButton", font=self.FONT_BOLD, padding=8)
        style.map("Accent.TButton",
                  background=[("active", ACCENT_HOVER), ("!disabled", ACCENT)],
                  foreground=[("!disabled", "white")])

        style.configure("Soft.TButton", font=self.FONT_BOLD, padding=6)
        style.map("Soft.TButton",
                  background=[("active", "#d6eaff"), ("!disabled", "#eaf3ff")],
                  foreground=[("!disabled", "#0d47a1")])

        style.configure("Danger.TButton", font=self.FONT_BOLD, padding=6)
        style.map("Danger.TButton",
                  background=[("active", "#c62828"), ("!disabled", WARN)],
                  foreground=[("!disabled", "white")])

        # Treeview estilos
        style.configure("Treeview",
                        font=self.FONT_BASE,
                        rowheight=int(self.font_size_base*2.2),
                        background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=self.FONT_BOLD, foreground=FG_TIT)

        # Dados
        self.militares = buscar_todos()
        self.militares_selecionados = []
        self.militares_filtrados = []

        self.ordem_postos = {
            "Capitão": 1,
            "1º Tenente": 2,
            "2º Tenente": 3,
            "Subtenente": 4,
            "1º Sargento": 5,
            "2º Sargento": 6,
            "3º Sargento": 7,
            "Cabo Efetivo Profissional": 8,
            "Soldado Efetivo Profissional": 9,
            "Soldado Efetivo Variável": 10
        }

        self.abreviacoes_postos = {
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

        self.textos_boletins = {}
        self.carregar_boletins()
        self.tipos_boletim = list(self.textos_boletins.keys())

        self._montar_ui()
        self._popular_tipos()
        self.atualizar_lista_militares()

    # ------------------- Fonts / Zoom -------------------
    def _make_fonts(self):
        self.FONT_BASE = ("Segoe UI", self.font_size_base)
        self.FONT_BOLD = ("Segoe UI", max(self.font_size_base, 11), "bold")
        self.FONT_H1 = ("Segoe UI", self.font_size_header, "bold")

    def _apply_zoom(self):
        style = ttk.Style()
        style.configure("Header.TLabel", font=self.FONT_H1)
        style.configure("Strong.TLabel", font=self.FONT_BOLD)
        style.configure("TLabel", font=self.FONT_BASE)
        style.configure("Accent.TButton", font=self.FONT_BOLD)
        style.configure("Soft.TButton", font=self.FONT_BOLD)
        style.configure("Danger.TButton", font=self.FONT_BOLD)
        style.configure("Treeview",
                        font=self.FONT_BASE,
                        rowheight=int(self.font_size_base*2.2))
        style.configure("Treeview.Heading", font=self.FONT_BOLD)

    def _zoom_in(self):
        self.font_size_base = min(self.font_size_base + 1, 18)
        self.font_size_header = min(self.font_size_header + 1, 26)
        self._make_fonts()
        self._apply_zoom()

    def _zoom_out(self):
        self.font_size_base = max(self.font_size_base - 1, 10)
        self.font_size_header = max(self.font_size_header - 1, 16)
        self._make_fonts()
        self._apply_zoom()

    # ------------------- Persistência -------------------
    def carregar_boletins(self):
        if os.path.exists(ARQUIVO_BOLETINS):
            try:
                with open(ARQUIVO_BOLETINS, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.textos_boletins = {**BOLETINS_PADRAO, **dados}
            except Exception:
                self.textos_boletins = BOLETINS_PADRAO.copy()
        else:
            self.textos_boletins = BOLETINS_PADRAO.copy()

    def salvar_boletins(self):
        para_salvar = {k: v for k, v in self.textos_boletins.items() if k not in BOLETINS_PADRAO}
        try:
            with open(ARQUIVO_BOLETINS, "w", encoding="utf-8") as f:
                json.dump(para_salvar, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar boletins: {e}", parent=self.janela)

    # ------------------- UI -------------------
    def _montar_ui(self):
        # Título + zoom
        header_bar = tk.Frame(self.janela, bg=BG_APP)
        header_bar.pack(fill="x", padx=16, pady=(14, 6))
        ttk.Label(header_bar, text="Gerar Boletim", style="Header.TLabel").pack(side="left")
        zoom_box = tk.Frame(header_bar, bg=BG_APP)
        zoom_box.pack(side="right")
        ttk.Button(zoom_box, text="A−", style="Soft.TButton", command=self._zoom_out).pack(side="left", padx=4)
        ttk.Button(zoom_box, text="A+", style="Soft.TButton", command=self._zoom_in).pack(side="left", padx=4)

        # Container principal com 3 colunas (Modelos | Disponíveis / Botões / Selecionados)
        main = tk.Frame(self.janela, bg=BG_APP)
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # pesos + largura mínima pra coluna dos botões ficar SEMPRE visível
        main.grid_columnconfigure(0, weight=1, uniform="col")         # modelos
        main.grid_columnconfigure(1, weight=2, uniform="col")         # disponíveis
        main.grid_columnconfigure(2, weight=0, minsize=160)           # botões (fixo mínimo)
        main.grid_columnconfigure(3, weight=2, uniform="col")         # selecionados
        main.grid_rowconfigure(0, weight=1)

        # ===== Coluna 0: Modelos (com grid interno) =====
        col0 = ttk.Frame(main, style="Card.TFrame")
        col0.grid(row=0, column=0, sticky="nsew", padx=(0,10), pady=(0,10))

        # grade interna: 0=título, 1=lista (expande), 2=botões
        col0.grid_columnconfigure(0, weight=1)
        col0.grid_rowconfigure(1, weight=1)  # só a lista cresce

        ttk.Label(col0, text="Modelos de Boletim", style="Strong.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=12, pady=(12,6))

        # lista + scrollbar
        lista_wrap = tk.Frame(col0, bg=CARD_BG)
        lista_wrap.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0,8))
        lista_wrap.grid_columnconfigure(0, weight=1)
        lista_wrap.grid_rowconfigure(0, weight=1)

        self.listbox_tipos = tk.Listbox(
            lista_wrap, height=12, font=self.FONT_BASE, bd=1, relief="solid", activestyle="dotbox"
        )
        self.listbox_tipos.grid(row=0, column=0, sticky="nsew")
        sb_tipos = ttk.Scrollbar(lista_wrap, orient="vertical", command=self.listbox_tipos.yview)
        sb_tipos.grid(row=0, column=1, sticky="ns")
        self.listbox_tipos.configure(yscrollcommand=sb_tipos.set)
        self.listbox_tipos.bind("<<ListboxSelect>>", lambda e: None)

        # barra de botões (ícones grandes com tooltip)
        bar_tipos = tk.Frame(col0, bg=CARD_BG)
        bar_tipos.grid(row=2, column=0, sticky="ew", padx=12, pady=(0,12))
        bar_tipos.grid_columnconfigure((0,1,2), weight=1)

        # estilo visual dos botões de ícone
        icon_font = ("Segoe UI Emoji", 16)  # um pouco maior p/ “desenho” aparecer
        btn_pad = {"ipadx": 8, "ipady": 6, "padx": 4, "pady": 2}

        btn_novo = ttk.Button(bar_tipos, text="＋", style="Soft.TButton",
                              command=self.adicionar_tipo_boletim)
        btn_novo.grid(row=0, column=0, sticky="ew")
        btn_novo.configure(width=3)
        btn_novo.bind("<Map>", lambda e: btn_novo.configure(style="Soft.TButton"))
        btn_novo_lbl = tk.Label(btn_novo, text="＋", font=icon_font, bg="#eaf3ff", fg="#0d47a1")
        btn_novo_lbl.place(relx=0.5, rely=0.5, anchor="center")
        _Tooltip(btn_novo, "Novo modelo")

        btn_edit = ttk.Button(bar_tipos, text="✏️", style="Soft.TButton",
                              command=self.editar_tipo_boletim)
        btn_edit.grid(row=0, column=1, sticky="ew")
        btn_edit.configure(width=3)
        btn_edit.bind("<Map>", lambda e: btn_edit.configure(style="Soft.TButton"))
        btn_edit_lbl = tk.Label(btn_edit, text="✏️", font=icon_font, bg="#eaf3ff", fg="#0d47a1")
        btn_edit_lbl.place(relx=0.5, rely=0.5, anchor="center")
        _Tooltip(btn_edit, "Editar modelo")

        btn_del = ttk.Button(bar_tipos, text="🗑", style="Danger.TButton",
                             command=self.remover_tipo_boletim)
        btn_del.grid(row=0, column=2, sticky="ew")
        btn_del.configure(width=3)
        btn_del.bind("<Map>", lambda e: btn_del.configure(style="Danger.TButton"))
        # fundo do Danger é vermelho – ajuste o label para combinar
        btn_del_lbl = tk.Label(btn_del, text="🗑", font=icon_font, bg=BTN_BG(btn_del), fg="white")
        btn_del_lbl.place(relx=0.5, rely=0.5, anchor="center")
        _Tooltip(btn_del, "Excluir modelo")

        # ===== Coluna 1: Disponíveis =====
        col1 = ttk.Frame(main, style="Card.TFrame")
        col1.grid(row=0, column=1, sticky="nsew", padx=(10,8), pady=(0,10))
        col1.grid_columnconfigure(0, weight=1)
        col1.grid_rowconfigure(2, weight=1)

        ttk.Label(col1, text="Disponíveis", style="Strong.TLabel").grid(row=0, column=0, sticky="w", padx=12, pady=(12,4))

        # Busca
        busca_wrap = tk.Frame(col1, bg=CARD_BG)
        busca_wrap.grid(row=1, column=0, sticky="ew", padx=12, pady=(0,8))
        tk.Label(busca_wrap, text="Pesquisar (Nome/Apelido):", font=self.FONT_BASE, bg=CARD_BG).pack(side="left")
        self.entrada_busca = ttk.Entry(busca_wrap)
        self.entrada_busca.pack(side="left", fill="x", expand=True, padx=(8,0))
        self.entrada_busca.bind("<KeyRelease>", lambda e: self.atualizar_lista_militares())

        # Treeview (só Posto/Graduação + Nome)
        left_wrap = tk.Frame(col1, bg=CARD_BG)
        left_wrap.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0,12))
        left_wrap.grid_columnconfigure(0, weight=1)
        left_wrap.grid_rowconfigure(0, weight=1)

        self.tree_disp = self._make_tree(left_wrap)
        self.tree_disp.grid(row=0, column=0, sticky="nsew")
        self._attach_scrollbars(left_wrap, self.tree_disp)

        # ===== Coluna 2: Botões (largura mínima garantida) =====
        col2 = ttk.Frame(main, style="Card.TFrame")
        col2.grid(row=0, column=2, sticky="ns", padx=(0,8), pady=(0,10))
        col2.grid_propagate(False)   # respeita minsize da coluna 2

        inner = tk.Frame(col2, bg=CARD_BG)
        inner.pack(expand=True)

        ttk.Button(inner, text="▶ Adicionar", style="Accent.TButton",
                   command=self.adicionar_militares, width=16).pack(pady=(10,6))
        ttk.Button(inner, text="◀ Remover", style="Danger.TButton",
                   command=self.remover_militares, width=16).pack(pady=(0,10))
        tk.Label(inner, text="Dicas:\n• Duplo-clique move\n• Clique no cabeçalho para ordenar",
                 bg=CARD_BG, justify="center", font=("Segoe UI", max(self.font_size_base-2, 10))).pack(padx=8)

        # ===== Coluna 3: Selecionados =====
        col3 = ttk.Frame(main, style="Card.TFrame")
        col3.grid(row=0, column=3, sticky="nsew", padx=(8,0), pady=(0,10))
        col3.grid_columnconfigure(0, weight=1)
        col3.grid_rowconfigure(1, weight=1)

        self.label_sel = ttk.Label(col3, text="Selecionados (0)", style="Strong.TLabel")
        self.label_sel.grid(row=0, column=0, sticky="w", padx=12, pady=(12,4))

        right_wrap = tk.Frame(col3, bg=CARD_BG)
        right_wrap.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0,12))
        right_wrap.grid_columnconfigure(0, weight=1)
        right_wrap.grid_rowconfigure(0, weight=1)

        self.tree_sel = self._make_tree(right_wrap)
        self.tree_sel.grid(row=0, column=0, sticky="nsew")
        self._attach_scrollbars(right_wrap, self.tree_sel)

        # binds de duplo clique
        self.tree_disp.bind("<Double-1>", lambda e: self.adicionar_militares())
        self.tree_sel.bind("<Double-1>", lambda e: self.remover_militares())

        # Barra de ações (Gerar abre uma nova janela)
        actions = tk.Frame(self.janela, bg=BG_APP)
        actions.pack(fill="x", padx=16, pady=(0,10))
        ttk.Button(actions, text="🧾 Gerar Boletim (abrir prévia)", style="Accent.TButton",
                   command=self.gerar_texto_boletim).pack(side="right")

        # Status
        self.status = tk.Label(self.janela, text="Pronto.", bg=BG_APP, fg="#455a64",
                               font=("Segoe UI", max(self.font_size_base-2, 9)), anchor="w")
        self.status.pack(fill="x", side="bottom", padx=16, pady=(0,8))

    # Tree com colunas e sort (APENAS Posto e Nome)
    def _make_tree(self, parent):
        cols = ("posto", "nome")
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="extended")
        tree.heading("posto", text="Posto/Graduação", command=lambda: self._sort_by(tree, "posto", False))
        tree.heading("nome", text="Nome", command=lambda: self._sort_by(tree, "nome", False))
        tree.column("posto", width=180, anchor="center", stretch=True)
        tree.column("nome", width=360, anchor="w", stretch=True)
        return tree

    def _attach_scrollbars(self, parent, tree):
        sb_y = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        sb_x.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

    def _sort_by(self, tree, col, desc):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        data.sort(key=lambda t: t[0].upper() if isinstance(t[0], str) else t[0], reverse=desc)
        for idx, (_, k) in enumerate(data):
            tree.move(k, "", idx)
        tree.heading(col, command=lambda: self._sort_by(tree, col, not desc))

    # ------------------- Utilidades -------------------
    def _tipo_atual(self):
        try:
            idx = self.listbox_tipos.curselection()
            if not idx:
                return None
            return self.listbox_tipos.get(idx[0])
        except Exception:
            return None

    # ------------------- Fluxo Militares -------------------
    def atualizar_lista_militares(self, event=None):
        termo = (self.entrada_busca.get() or "").strip().upper()
        filtrados = [
            m for m in self.militares
            if termo in (m[2] or "").upper() or termo in (m[3] or "").upper()
        ]
        filtrados.sort(key=lambda x: self.ordem_postos.get(x[1], 999))
        self.militares_filtrados = filtrados

        # repopula disponíveis
        for i in self.tree_disp.get_children():
            self.tree_disp.delete(i)
        for m in filtrados:
            posto = m[1] or ""
            nome = (m[2] or "").upper()
            iid = f"disp_{m[0]}"
            self.tree_disp.insert("", "end", iid=iid, values=(posto, nome))

        self._set_status(f"{len(filtrados)} militar(es) encontrado(s).")
        self.label_sel.config(text=f"Selecionados ({len(self.militares_selecionados)})")

    def _sel_ids_from_tree(self, tree):
        iids = tree.selection()
        ids = []
        for iid in iids:
            try:
                ident = int(iid.split("_", 1)[1])
                ids.append(ident)
            except Exception:
                pass
        return ids

    def _find_militar_by_id(self, mid):
        for m in self.militares:
            if m[0] == mid:
                return m
        return None

    def adicionar_militares(self):
        ids = self._sel_ids_from_tree(self.tree_disp)
        count = 0
        for mid in ids:
            mil = self._find_militar_by_id(mid)
            if mil and (mil not in self.militares_selecionados):
                self.militares_selecionados.append(mil)
                count += 1
        self.militares_selecionados.sort(key=lambda x: (self.ordem_postos.get(x[1], 999), (x[2] or "").upper()))
        self._rebuild_tree_selected()
        self._set_status(f"{count} adicionado(s). Total: {len(self.militares_selecionados)}.")

    def remover_militares(self):
        ids = self._sel_ids_from_tree(self.tree_sel)
        before = len(self.militares_selecionados)
        self.militares_selecionados = [m for m in self.militares_selecionados if m[0] not in ids]
        self._rebuild_tree_selected()
        removed = before - len(self.militares_selecionados)
        self._set_status(f"{removed} removido(s). Total: {len(self.militares_selecionados)}.")

    def _rebuild_tree_selected(self):
        for i in self.tree_sel.get_children():
            self.tree_sel.delete(i)
        for m in self.militares_selecionados:
            posto = m[1] or ""
            nome = (m[2] or "").upper()
            iid = f"sel_{m[0]}"
            self.tree_sel.insert("", "end", iid=iid, values=(posto, nome))
        self.label_sel.config(text=f"Selecionados ({len(self.militares_selecionados)})")

    # ------------------- CRUD Modelos -------------------
    def adicionar_tipo_boletim(self):
        self._abrir_janela_editar_novo()

    def editar_tipo_boletim(self):
        tipo = self._tipo_atual()
        if not tipo:
            messagebox.showwarning("Aviso", "Selecione um modelo para editar.", parent=self.janela)
            return
        texto = self.textos_boletins.get(tipo, "")
        self._abrir_janela_editar_novo(nome_existente=tipo, texto_existente=texto)

    def _abrir_janela_editar_novo(self, nome_existente=None, texto_existente=""):
        dlg = tk.Toplevel(self.janela)
        dlg.title("Novo Modelo de Boletim" if not nome_existente else "Editar Modelo de Boletim")
        dlg.geometry("820x560")
        dlg.configure(bg=BG_APP)
        dlg.grab_set()

        frame = ttk.Frame(dlg, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frame, text="Nome do modelo de boletim:", style="Strong.TLabel").pack(anchor="w", padx=12, pady=(12,6))
        entrada_nome = ttk.Entry(frame, font=self.FONT_BASE)
        entrada_nome.pack(fill="x", padx=12)
        if nome_existente:
            entrada_nome.insert(0, nome_existente)

        ttk.Label(frame, text="Texto padrão do boletim:", style="Strong.TLabel").pack(anchor="w", padx=12, pady=(12,6))
        txt = tk.Text(frame, font=self.FONT_BASE, height=16, bd=1, relief="solid", wrap="word")
        txt.pack(fill="both", expand=True, padx=12, pady=(0,12))
        if texto_existente:
            txt.insert("1.0", texto_existente)

        bar = tk.Frame(frame, bg=CARD_BG)
        bar.pack(fill="x", padx=12, pady=(0,12))
        ttk.Button(bar, text="💾 Salvar Modelo", style="Accent.TButton",
                   command=lambda: salvar()).pack(side="left")
        ttk.Button(bar, text="Cancelar", style="Soft.TButton",
                   command=dlg.destroy).pack(side="left", padx=8)

        def salvar():
            nome = entrada_nome.get().strip()
            texto = txt.get("1.0", tk.END).strip()
            if not nome:
                messagebox.showerror("Erro", "Digite o nome do modelo.", parent=dlg)
                return
            if nome != nome_existente and nome in self.tipos_boletim:
                messagebox.showwarning("Aviso", "Já existe um modelo com esse nome.", parent=dlg)
                return

            if nome_existente and nome_existente in self.tipos_boletim:
                idx = self.tipos_boletim.index(nome_existente)
                self.tipos_boletim[idx] = nome
                del self.textos_boletins[nome_existente]
            else:
                self.tipos_boletim.append(nome)

            self.textos_boletins[nome] = texto if texto else ""
            self._popular_tipos()
            try:
                idx_novo = self.tipos_boletim.index(nome)
                self.listbox_tipos.selection_clear(0, tk.END)
                self.listbox_tipos.selection_set(idx_novo)
            except Exception:
                pass
            self.salvar_boletins()
            dlg.destroy()

    def remover_tipo_boletim(self):
        tipo = self._tipo_atual()
        if not tipo:
            messagebox.showwarning("Aviso", "Selecione um modelo para remover.", parent=self.janela)
            return
        if tipo in BOLETINS_PADRAO:
            messagebox.showerror("Erro", "Não é possível remover modelos padrão.", parent=self.janela)
            return
        confirmar = messagebox.askyesno("Confirmar Exclusão", f"Deseja realmente excluir o modelo '{tipo}'?", parent=self.janela)
        if confirmar:
            self.tipos_boletim.remove(tipo)
            del self.textos_boletins[tipo]
            self._popular_tipos()
            self.salvar_boletins()
            self._set_status(f"Modelo '{tipo}' removido.")

    def _popular_tipos(self):
        self.listbox_tipos.delete(0, tk.END)
        for tipo in self.tipos_boletim:
            self.listbox_tipos.insert(tk.END, tipo)
        if self.tipos_boletim:
            self.listbox_tipos.select_set(0)

    # ------------------- Geração / Prévia em NOVA JANELA -------------------
    def gerar_texto_boletim(self):
        if not self.militares_selecionados:
            messagebox.showwarning("Atenção", "Selecione ao menos um militar para gerar o boletim.", parent=self.janela)
            return
        tipo = self._tipo_atual()
        if not tipo:
            messagebox.showwarning("Atenção", "Selecione um tipo de boletim.", parent=self.janela)
            return

        texto = self.textos_boletins.get(tipo, f"Modelo de boletim '{tipo}' não definido.\n\n")
        texto += "\n\n"

        for m in self.militares_selecionados:
            abreviacao = self.abreviacoes_postos.get(m[1], m[1])
            nome = (m[2] or "").upper()
            texto += f"{abreviacao} {nome}\n\n"

        self._abrir_preview(titulo=f"Prévia do Boletim — {tipo}", conteudo=texto)
        self._set_status(f"Boletim gerado ({len(self.militares_selecionados)} militar(es)).")

    def _abrir_preview(self, titulo: str, conteudo: str):
        dlg = tk.Toplevel(self.janela)
        dlg.title(titulo)
        dlg.geometry("980x720")
        dlg.minsize(720, 520)  # garante espaço mínimo pros botões
        dlg.configure(bg=BG_APP)
        dlg.transient(self.janela)
        dlg.grab_set()

        # Cabeçalho
        head = tk.Frame(dlg, bg=BG_APP)
        head.pack(fill="x", padx=14, pady=(14, 6))
        ttk.Label(head, text=titulo, style="Header.TLabel").pack(side="left")

        # Área do texto
        wrap = ttk.Frame(dlg, style="Card.TFrame")
        wrap.pack(fill="both", expand=True, padx=14, pady=10)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        txt = tk.Text(wrap, font=("Segoe UI", 12), wrap="word", bd=1, relief="solid")
        txt.grid(row=0, column=0, sticky="nsew")
        sb_y = ttk.Scrollbar(wrap, orient="vertical", command=txt.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        txt.configure(yscrollcommand=sb_y.set)
        txt.insert("1.0", conteudo)

        # Barra de ações (altura fixa para não colapsar)
        bar = tk.Frame(dlg, bg=BG_APP, height=60)
        bar.pack(fill="x", padx=14, pady=(0,12))
        bar.pack_propagate(False)

        def copiar():
            dlg.clipboard_clear()
            dlg.clipboard_append(txt.get("1.0", "end-1c"))
            messagebox.showinfo("OK", "Texto copiado para a área de transferência.", parent=dlg)

        def salvar_txt():
            try:
                path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Texto", "*.txt")],
                    parent=dlg
                )
                if not path:
                    return
                with open(path, "w", encoding="utf-8") as f:
                    f.write(txt.get("1.0", "end-1c"))
                messagebox.showinfo("OK", f"Arquivo salvo em:\n{path}", parent=dlg)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar arquivo:\n{e}", parent=dlg)

        ttk.Button(bar, text="📋 Copiar", style="Soft.TButton", command=copiar).pack(side="left")
        ttk.Button(bar, text="💾 Salvar .txt", style="Soft.TButton", command=salvar_txt).pack(side="left", padx=8)
        ttk.Button(bar, text="Fechar", style="Danger.TButton", command=dlg.destroy).pack(side="right")

    # ------------------- Status -------------------
    def _set_status(self, msg):
        self.status.config(text=msg)

def BTN_BG(btn):
    # tenta capturar a cor atual do estilo do botão
    try:
        style = ttk.Style()
        return style.lookup(btn.cget("style"), "background", default="#e53935") or "#e53935"
    except Exception:
        return "#e53935"

def abrir_boletim():
    SistemaBoletim()
