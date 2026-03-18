import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date

from constants import CORES_GRAFICOS
from database import (
    carregar_cartoes, salvar_cartoes,
    adicionar_cartao_db, remover_cartao_db,
)
from ui.widgets import fmt, entry_widget, btn


class AbaCartoes:
    """Mixin — métodos da aba de Cartões de Crédito."""

    def _construir_aba_cartoes(self, parent):
        parent.columnconfigure(0, minsize=280, weight=0)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)
        esq = tk.Frame(parent, bg=self.CARD)
        esq.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        canvas_esq = tk.Canvas(esq, bg=self.CARD, highlightthickness=0)
        scroll_esq = ttk.Scrollbar(esq, orient="vertical", command=canvas_esq.yview)
        canvas_esq.configure(yscrollcommand=scroll_esq.set)
        scroll_esq.pack(side="right", fill="y")
        canvas_esq.pack(side="left", fill="both", expand=True)
        form = tk.Frame(canvas_esq, bg=self.CARD, padx=20, pady=16)
        form_win = canvas_esq.create_window((0, 0), window=form, anchor="nw")
        def _resize(e):
            canvas_esq.configure(scrollregion=canvas_esq.bbox("all"))
            canvas_esq.itemconfig(form_win, width=e.width)
        canvas_esq.bind("<Configure>", _resize)
        form.bind("<Configure>", lambda e: canvas_esq.configure(scrollregion=canvas_esq.bbox("all")))
        form.columnconfigure(1, weight=1)
        row_idx = [0]
        def sec(txt):
            tk.Label(form, text=txt, bg=self.CARD, fg=self.FG2,
                     font=("Segoe UI", 9, "bold")).grid(
                row=row_idx[0], column=0, columnspan=2, sticky="w", pady=(14, 6))
            row_idx[0] += 1
        def lbl_entry(txt, default=""):
            tk.Label(form, text=txt, bg=self.CARD, fg=self.FG,
                     font=("Segoe UI", 10)).grid(row=row_idx[0], column=0, sticky="w", pady=4)
            e = entry_widget(form, self, row=row_idx[0], col=1)
            if default:
                e.insert(0, default)
            row_idx[0] += 1
            return e
        def sep():
            ttk.Separator(form, orient="horizontal").grid(
                row=row_idx[0], column=0, columnspan=2, sticky="ew", pady=10)
            row_idx[0] += 1
        def add_btn(txt, cmd, bg=None, fg=None):
            btn(form, self, txt, cmd, bg=bg, fg=fg).grid(
                row=row_idx[0], column=0, columnspan=2, sticky="ew", pady=(4, 0))
            row_idx[0] += 1

        sec("NOVO CARTÃO")
        self.c_nome   = lbl_entry("Nome do cartão")

        # Tipo do cartão
        tk.Label(form, text="Tipo", bg=self.CARD, fg=self.FG,
                 font=("Segoe UI", 10)).grid(row=row_idx[0], column=0, sticky="w", pady=4)
        self.var_tipo_cartao = tk.StringVar(value="proprio")
        frame_tc = tk.Frame(form, bg=self.CARD)
        frame_tc.grid(row=row_idx[0], column=1, sticky="w", pady=4)
        row_idx[0] += 1

        # Labels guardados para mostrar/ocultar
        self._lbl_limite = tk.Label(form, text="Limite total (R$)", bg=self.CARD, fg=self.FG, font=("Segoe UI", 10))
        self._lbl_fatura = tk.Label(form, text="Fatura atual (R$)", bg=self.CARD, fg=self.FG, font=("Segoe UI", 10))
        self._lbl_venc   = tk.Label(form, text="Vencimento (dia)",  bg=self.CARD, fg=self.FG, font=("Segoe UI", 10))

        def _toggle_campos_cartao():
            eh_terceiro = self.var_tipo_cartao.get() == "terceiro"
            for lbl, entry in [(self._lbl_limite, self.c_limite),
                               (self._lbl_fatura, self.c_fatura),
                               (self._lbl_venc,   self.c_venc)]:
                if eh_terceiro:
                    lbl.grid_remove()
                    entry.grid_remove()
                else:
                    lbl.grid()
                    entry.grid()

        for val, txt in [("proprio", "Próprio"), ("terceiro", "Terceiro")]:
            tk.Radiobutton(frame_tc, text=txt, variable=self.var_tipo_cartao, value=val,
                          command=_toggle_campos_cartao,
                          bg=self.CARD, fg=self.FG, selectcolor=self.BORDA,
                          activebackground=self.CARD, activeforeground=self.FG,
                          highlightthickness=0, font=("Segoe UI", 10)).pack(side="left", padx=(0,12))

        # Campos próprios — colocados manualmente para ter referência dos labels
        r = row_idx[0]
        self._lbl_limite.grid(row=r,   column=0, sticky="w", pady=4)
        self.c_limite = entry_widget(form, self, row=r, col=1); row_idx[0] += 1
        r = row_idx[0]
        self._lbl_fatura.grid(row=r,   column=0, sticky="w", pady=4)
        self.c_fatura = entry_widget(form, self, row=r, col=1)
        self.c_fatura.insert(0, "0"); row_idx[0] += 1
        r = row_idx[0]
        self._lbl_venc.grid(row=r,     column=0, sticky="w", pady=4)
        self.c_venc   = entry_widget(form, self, row=r, col=1); row_idx[0] += 1
        sep()
        add_btn("＋  Adicionar Cartão", self._adicionar_cartao)

        sep()
        sec("REGISTRAR GASTO NO CARTÃO")
        tk.Label(form, text="Cartão", bg=self.CARD, fg=self.FG,
                 font=("Segoe UI", 10)).grid(row=row_idx[0], column=0, sticky="w", pady=4)
        self.combo_cartao_gasto = ttk.Combobox(form, state="readonly", font=("Segoe UI", 10))
        self.combo_cartao_gasto.grid(row=row_idx[0], column=1, sticky="ew", pady=4)
        row_idx[0] += 1
        self.g_desc  = lbl_entry("Descrição")
        self.g_valor = lbl_entry("Valor total (R$)")
        tk.Label(form, text="Parcelado?", bg=self.CARD, fg=self.FG,
                 font=("Segoe UI", 10)).grid(row=row_idx[0], column=0, sticky="w", pady=4)
        self.var_parcelado = tk.BooleanVar(value=False)
        frame_parc = tk.Frame(form, bg=self.CARD)
        frame_parc.grid(row=row_idx[0], column=1, sticky="w", pady=4)
        tk.Radiobutton(frame_parc, text="Não", variable=self.var_parcelado, value=False,
                      command=self._toggle_parcelas, bg=self.CARD, fg=self.FG, selectcolor=self.BORDA,
                      activebackground=self.CARD, activeforeground=self.FG,
                      highlightthickness=0, font=("Segoe UI", 10)).pack(side="left", padx=(0,10))
        tk.Radiobutton(frame_parc, text="Sim", variable=self.var_parcelado, value=True,
                      command=self._toggle_parcelas, bg=self.CARD, fg=self.FG, selectcolor=self.BORDA,
                      activebackground=self.CARD, activeforeground=self.FG,
                      highlightthickness=0, font=("Segoe UI", 10)).pack(side="left")
        row_idx[0] += 1
        self.lbl_parcelas = tk.Label(form, text="Nº de parcelas", bg=self.CARD, fg=self.FG,
                                     font=("Segoe UI", 10))
        self.entry_parcelas = entry_widget(form, self)
        self.entry_parcelas.insert(0, "2")
        self.lbl_parcela_val = tk.Label(form, text="", bg=self.CARD, fg=self.FG2, font=("Segoe UI", 9))
        self._parc_row = row_idx[0]
        row_idx[0] += 2
        sep()
        add_btn("＋  Adicionar Gasto", self._adicionar_gasto_cartao)

        sep()
        sec("PRÓXIMAS FATURAS")
        tk.Label(form, text="Cartão", bg=self.CARD, fg=self.FG,
                 font=("Segoe UI", 10)).grid(row=row_idx[0], column=0, sticky="w", pady=4)
        self.combo_cartao_fat = ttk.Combobox(form, state="readonly", font=("Segoe UI", 10))
        self.combo_cartao_fat.grid(row=row_idx[0], column=1, sticky="ew", pady=4)
        row_idx[0] += 1
        self.f_desc  = lbl_entry("Descrição")
        self.f_valor = lbl_entry("Valor (R$)")
        tk.Label(form, text="Mês/Ano (MM/AAAA)", bg=self.CARD, fg=self.FG,
                 font=("Segoe UI", 10)).grid(row=row_idx[0], column=0, sticky="w", pady=4)
        self.f_mes = entry_widget(form, self, row=row_idx[0], col=1)
        prox = date.today()
        self.f_mes.insert(0, str(prox.month).zfill(2) + "/" + str(prox.year))
        row_idx[0] += 1
        sep()
        add_btn("＋  Adicionar à Próxima Fatura", self._adicionar_proxima_fatura)

        # Painel direito
        # Painel direito com scroll vertical
        dir_outer = ttk.Frame(parent, style="TFrame")
        dir_outer.grid(row=0, column=1, sticky="nsew")
        dir_outer.columnconfigure(0, weight=1)
        dir_outer.rowconfigure(0, weight=1)

        dir_canvas = tk.Canvas(dir_outer, bg=self.BG, highlightthickness=0)
        dir_scroll = ttk.Scrollbar(dir_outer, orient="vertical", command=dir_canvas.yview)
        dir_canvas.configure(yscrollcommand=dir_scroll.set)
        dir_canvas.grid(row=0, column=0, sticky="nsew")
        dir_scroll.grid(row=0, column=1, sticky="ns")

        dir_frame = tk.Frame(dir_canvas, bg=self.BG)
        dir_win = dir_canvas.create_window((0, 0), window=dir_frame, anchor="nw")

        def _resize_dir(e):
            dir_canvas.configure(scrollregion=dir_canvas.bbox("all"))
            dir_canvas.itemconfig(dir_win, width=e.width)
        dir_canvas.bind("<Configure>", _resize_dir)
        dir_frame.bind("<Configure>", lambda e: dir_canvas.configure(scrollregion=dir_canvas.bbox("all")))
        dir_frame.columnconfigure(0, weight=1)

        # Scroll com mouse
        def _on_mousewheel(e):
            dir_canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        dir_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Cards resumo
        resumo_c = tk.Frame(dir_frame, bg=self.BG)
        resumo_c.pack(fill="x", pady=(0, 10))
        resumo_c.columnconfigure(0, weight=1)
        resumo_c.columnconfigure(1, weight=1)
        self.card_fatura_total = self._mini_card(resumo_c, "Fatura Atual")
        self.card_fatura_total.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        self.card_proximas = self._mini_card(resumo_c, "Próximas Faturas")
        self.card_proximas.grid(row=0, column=1, sticky="ew", pady=(0, 6))
        self.card_limite_total = self._mini_card(resumo_c, "Limite Total")
        self.card_limite_total.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.card_disponivel = self._mini_card(resumo_c, "Disponível")
        self.card_disponivel.grid(row=1, column=1, sticky="ew")
        self.card_terceiros = self._mini_card(resumo_c, "Gastos em Cartões de Terceiros")
        self.card_terceiros.grid(row=2, column=0, sticky="nsew", padx=(0, 6), pady=(6, 0))

        # Meus Cartões — frame de cards dinâmicos
        tc = tk.Frame(dir_frame, bg=self.CARD)
        tc.pack(fill="x", pady=(0, 10))
        tk.Label(tc, text="MEUS CARTÕES", bg=self.CARD, fg=self.FG2,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 8))
        self.frame_cards_cartoes = tk.Frame(tc, bg=self.CARD)
        self.frame_cards_cartoes.pack(fill="x", padx=12, pady=(0, 10))
        # Guarda referência do cartão selecionado
        self._cartao_idx_sel = tk.IntVar(value=-1)

        # Próximas Faturas (cards lado a lado, sem scroll horizontal)
        tf = tk.Frame(dir_frame, bg=self.CARD)
        tf.pack(fill="x")
        tf.columnconfigure(0, weight=1)
        tk.Label(tf, text="PRÓXIMAS FATURAS", bg=self.CARD, fg=self.FG2,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(10,6))

        self.fat_cards_frame = tk.Frame(tf, bg=self.CARD)
        self.fat_cards_frame.pack(fill="x", padx=12, pady=(0,10))

        def _rewrap_fat(e=None):
            f = self.fat_cards_frame
            children = f.winfo_children()
            if not children: return
            f.update_idletasks()
            W = f.winfo_width()
            if W < 2: return
            card_w = 130
            cols = max(1, W // (card_w + 8))
            for w in children:
                w.grid_forget()
            for i, w in enumerate(children):
                w.grid(row=i // cols, column=i % cols, sticky="nsew", padx=(0,8), pady=(0,8))
            for col in range(cols):
                f.columnconfigure(col, weight=1)

        self.fat_cards_frame.bind("<Configure>", lambda e: _rewrap_fat())
        self._rewrap_fat = _rewrap_fat
        self._fat_canvas = None  # não usado mas mantido por compatibilidade

        self._atualizar_cartoes()

    def _mini_card(self, parent, titulo):
        # Wrapper com altura fixa
        outer = tk.Frame(parent, bg=self.CARD, height=160)
        outer.pack_propagate(False)
        f = ttk.Frame(outer, style="Card.TFrame", padding=(14, 10))
        f.pack(fill="both", expand=True)
        tk.Label(f, text=titulo, bg=self.CARD, fg=self.FG2, font=("Segoe UI", 9)).pack(anchor="w")
        lbl = tk.Label(f, text="R$ 0,00", bg=self.CARD, fg=self.FG, font=("Segoe UI", 13, "bold"))
        lbl.pack(anchor="w", pady=(2, 0))
        outer._lbl = lbl
        f._lbl = lbl
        # Frame para composição (linhas por cartão)
        composicao = tk.Frame(f, bg=self.CARD)
        composicao.pack(anchor="w", fill="x")
        f._composicao = composicao
        outer._composicao = composicao
        return outer

    def _adicionar_cartao(self):
        nome = self.c_nome.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Digite o nome do cartão.")
            return
        eh_terceiro = self.var_tipo_cartao.get() == "terceiro"
        if eh_terceiro:
            limite, fatura, venc = 0, 0, 0
        else:
            try:
                limite = float(self.c_limite.get().strip().replace(",", "."))
                fatura = float(self.c_fatura.get().strip().replace(",", "."))
                venc   = int(self.c_venc.get().strip())
            except ValueError:
                messagebox.showerror("Erro", "Preencha todos os campos corretamente.")
                return
        adicionar_cartao_db(nome, limite, fatura, venc, eh_terceiro)
        self.c_nome.delete(0, "end")
        if not eh_terceiro:
            for e in [self.c_limite, self.c_fatura, self.c_venc]:
                e.delete(0, "end")
        self.var_tipo_cartao.set("proprio")
        self._atualizar_cartoes()

    def _toggle_parcelas(self):
        if self.var_parcelado.get():
            self.lbl_parcelas.grid(row=self._parc_row, column=0, sticky="w", pady=4)
            self.entry_parcelas.grid(row=self._parc_row, column=1, sticky="ew", pady=4, ipady=4)
            self.lbl_parcela_val.grid(row=self._parc_row+1, column=0, columnspan=2, sticky="w", pady=(0,4))
            self.entry_parcelas.bind("<KeyRelease>", self._atualizar_valor_parcela)
            self.g_valor.bind("<KeyRelease>", self._atualizar_valor_parcela)
        else:
            self.lbl_parcelas.grid_remove()
            self.entry_parcelas.grid_remove()
            self.lbl_parcela_val.grid_remove()
            self.lbl_parcela_val.config(text="")

    def _atualizar_valor_parcela(self, *_):
        try:
            total = float(self.g_valor.get().strip().replace(",", "."))
            n = int(self.entry_parcelas.get().strip())
            if n > 0:
                parc = total / n
                self.lbl_parcela_val.config(
                    text=("→ " + str(n) + "x de R$ " + "{:,.2f}".format(parc)).replace(",","X").replace(".",",").replace("X","."))
        except:
            self.lbl_parcela_val.config(text="")

    def _adicionar_gasto_cartao(self):
        nome  = self.combo_cartao_gasto.get()
        desc  = self.g_desc.get().strip()
        try:
            valor = float(self.g_valor.get().strip().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido.")
            return
        if not nome or not desc:
            messagebox.showwarning("Atenção", "Preencha todos os campos.")
            return
        parcelado = self.var_parcelado.get()
        cartoes = carregar_cartoes()
        def fmt(v): return ("R$ " + "{:,.2f}".format(v)).replace(",","X").replace(".",",").replace("X",".")
        if parcelado:
            try:
                n = int(self.entry_parcelas.get().strip())
                if n < 2:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Erro", "Informe o número de parcelas (mínimo 2).")
                return
            parcela = valor / n
            hoje = date.today()
            for c in cartoes:
                if c["nome"] == nome:
                    c["fatura"] = c.get("fatura", 0) + parcela
                    if not c.get("mes_fatura"):
                        c["mes_fatura"] = str(hoje.month).zfill(2) + "/" + str(hoje.year)
                    if "gastos" not in c:
                        c["gastos"] = []
                    c["gastos"].append({"desc": desc + " (1/" + str(n) + ")", "valor": parcela,
                                        "data": hoje.strftime("%d/%m/%Y")})
                    if "faturas" not in c:
                        c["faturas"] = []
                    for i in range(2, n + 1):
                        mes_fut = hoje.month - 1 + i
                        ano_fut = hoje.year + (mes_fut - 1) // 12
                        mes_fut = ((mes_fut - 1) % 12) + 1
                        mes_str = str(mes_fut).zfill(2) + "/" + str(ano_fut)
                        nome_mes = ["JAN","FEV","MAR","ABR","MAI","JUN",
                                    "JUL","AGO","SET","OUT","NOV","DEZ"][mes_fut-1]
                        c["faturas"].append({"desc": desc + " (" + str(i) + "/" + str(n) + ")",
                                             "valor": parcela, "mes": mes_str + " " + nome_mes})
                    break
            salvar_cartoes(cartoes)
            msg = (str(n) + "x de " + fmt(parcela) + " — 1ª parcela na fatura atual, restantes nas próximas.")
        else:
            for c in cartoes:
                if c["nome"] == nome:
                    c["fatura"] = c.get("fatura", 0) + valor
                    if not c.get("mes_fatura"):
                        hoje = date.today()
                        c["mes_fatura"] = str(hoje.month).zfill(2) + "/" + str(hoje.year)
                    if "gastos" not in c:
                        c["gastos"] = []
                    c["gastos"].append({"desc": desc, "valor": valor,
                                        "data": date.today().strftime("%d/%m/%Y")})
                    break
            salvar_cartoes(cartoes)
            msg = fmt(valor) + " adicionado à fatura de " + nome + "."
        self.g_desc.delete(0, "end")
        self.g_valor.delete(0, "end")
        self.var_parcelado.set(False)
        self._toggle_parcelas()
        self._atualizar_cartoes()
        messagebox.showinfo("Sucesso", msg)

    def _adicionar_proxima_fatura(self):
        nome  = self.combo_cartao_fat.get()
        desc  = self.f_desc.get().strip()
        mes   = self.f_mes.get().strip()
        try:
            valor = float(self.f_valor.get().strip().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido.")
            return
        if not nome or not desc or not mes:
            messagebox.showwarning("Atenção", "Preencha todos os campos.")
            return
        cartoes = carregar_cartoes()
        for c in cartoes:
            if c["nome"] == nome:
                if "faturas" not in c:
                    c["faturas"] = []
                c["faturas"].append({"desc": desc, "valor": valor, "mes": mes})
                break
        salvar_cartoes(cartoes)
        self.f_desc.delete(0, "end")
        self.f_valor.delete(0, "end")
        self._atualizar_cartoes()

    def _pagar_fatura(self):
        idx = self._cartao_idx_sel.get()
        if idx < 0:
            messagebox.showwarning("Atenção", "Selecione um cartão para pagar a fatura.")
            return
        cartoes = carregar_cartoes()
        c = cartoes[idx]
        nome = c["nome"]
        def fmt(v): return ("R$ " + "{:,.2f}".format(v)).replace(",","X").replace(".",",").replace("X",".")
        fatura_atual = c.get("fatura", 0)
        msg_conf = ("Confirmar pagamento da fatura de " + nome + "?\n\n"
                    "Valor pago: " + fmt(fatura_atual) + "\n\n"
                    "A fatura atual será zerada e a próxima fatura mais próxima se tornará a fatura atual.")
        if not messagebox.askyesno("Confirmar Pagamento", msg_conf):
            return
        c["gastos"] = []
        c["fatura"] = 0.0
        faturas = c.get("faturas", [])
        if faturas:
            def parse_mes(f):
                try:
                    partes = f["mes"].strip().split()
                    m, a = partes[0].split("/")
                    return int(a) * 100 + int(m)
                except:
                    return 999999
            faturas_sorted = sorted(faturas, key=parse_mes)
            proxima = faturas_sorted[0]
            c["fatura"] = proxima["valor"]
            c["mes_fatura"] = proxima["mes"]
            c["gastos"] = [{"desc": proxima["desc"], "valor": proxima["valor"],
                            "data": date.today().strftime("%d/%m/%Y")}]
            c["faturas"] = [f for f in faturas
                            if not (f["mes"] == proxima["mes"] and f["desc"] == proxima["desc"])]
            msg_ok = ("Fatura de " + nome + " paga!\n\n"
                      "Valor pago: " + fmt(fatura_atual) + "\n"
                      "Nova fatura atual: " + fmt(c["fatura"]) + " (" + proxima["mes"] + ")")
        else:
            msg_ok = "Fatura de " + nome + " paga!\n\nSem próximas faturas. Limite totalmente liberado."
        salvar_cartoes(cartoes)
        self._atualizar_cartoes()
        messagebox.showinfo("Fatura Paga!", msg_ok)

    def _editar_cartao(self):
        idx = self._cartao_idx_sel.get()
        if idx < 0:
            messagebox.showwarning("Atenção", "Selecione um cartão para editar.")
            return
        cartoes = carregar_cartoes()
        c = cartoes[idx]
        win = tk.Toplevel(self)
        win.title("Editar Cartão")
        win.configure(bg=self.CARD)
        win.resizable(False, False)
        win.grab_set()
        win.geometry("340x280")
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 340) // 2
        y = self.winfo_y() + (self.winfo_height() - 280) // 2
        win.geometry("340x280+" + str(x) + "+" + str(y))
        pad = tk.Frame(win, bg=self.CARD, padx=20, pady=16)
        pad.pack(fill="both", expand=True)
        pad.columnconfigure(1, weight=1)
        tk.Label(pad, text="EDITAR CARTÃO", bg=self.CARD, fg=self.FG2,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,12))
        campos = [
            (1, "Nome",             "nome",        c.get("nome","")),
            (2, "Limite (R$)",      "limite",      str(c.get("limite",""))),
            (3, "Fatura atual (R$)","fatura",      str(c.get("fatura","0"))),
            (4, "Vencimento (dia)", "vencimento",  str(c.get("vencimento",""))),
        ]
        entries = {}
        for r, lbl_txt, key, val in campos:
            tk.Label(pad, text=lbl_txt, bg=self.CARD, fg=self.FG,
                     font=("Segoe UI",10)).grid(row=r, column=0, sticky="w", pady=4)
            e = tk.Entry(pad, bg=self.ENTRY_BG, fg=self.FG, insertbackground=self.FG,
                        font=("Segoe UI",10), relief="flat", bd=4)
            e.grid(row=r, column=1, sticky="ew", pady=4, ipady=4)
            e.insert(0, val)
            entries[key] = e
        ttk.Separator(pad, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=12)
        def salvar_edicao_cartao():
            try:
                cartoes[idx]["nome"]       = entries["nome"].get().strip()
                cartoes[idx]["limite"]     = float(entries["limite"].get().strip().replace(",","."))
                cartoes[idx]["fatura"]     = float(entries["fatura"].get().strip().replace(",","."))
                cartoes[idx]["vencimento"] = int(entries["vencimento"].get().strip())
            except ValueError:
                messagebox.showerror("Erro", "Preencha todos os campos corretamente.", parent=win)
                return
            salvar_cartoes(cartoes)
            self._atualizar_cartoes()
            win.destroy()
        tk.Button(pad, text="💾  Salvar Alterações", command=salvar_edicao_cartao,
                 bg=self.FG, fg=self.BG, font=("Segoe UI",10,"bold"),
                 relief="flat", cursor="hand2", padx=12, pady=6,
                 activebackground=self.FG, activeforeground=self.BG).grid(
            row=6, column=0, columnspan=2, sticky="ew")

    def _remover_cartao(self):
        idx = self._cartao_idx_sel.get()
        if idx < 0:
            messagebox.showwarning("Atenção", "Selecione um cartão para remover.")
            return
        cartoes = carregar_cartoes()
        nome = cartoes[idx]["nome"]
        if messagebox.askyesno("Confirmar", "Remover o cartão \"" + nome + "\"?"):
            remover_cartao_db(c["id"])
            self._atualizar_cartoes()

    def _abrir_gerenciar_fatura(self, modo):
        cartoes = carregar_cartoes()
        cartoes_com_fat = [c for c in cartoes if c.get("faturas")]
        if not cartoes_com_fat:
            messagebox.showwarning("Atenção", "Nenhuma próxima fatura cadastrada.")
            return

        win = tk.Toplevel(self)
        win.title("Editar Fatura" if modo == "editar" else "Remover Fatura")
        win.configure(bg=self.CARD)
        win.resizable(False, False)
        win.grab_set()
        h = 340 if modo == "editar" else 260
        win.geometry("380x" + str(h))
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 380) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        win.geometry("380x" + str(h) + "+" + str(x) + "+" + str(y))

        pad = tk.Frame(win, bg=self.CARD, padx=20, pady=16)
        pad.pack(fill="both", expand=True)
        pad.columnconfigure(1, weight=1)

        titulo = "EDITAR FATURA" if modo == "editar" else "REMOVER FATURA"
        tk.Label(pad, text=titulo, bg=self.CARD, fg=self.FG2,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,12))

        tk.Label(pad, text="Cartão", bg=self.CARD, fg=self.FG,
                 font=("Segoe UI",10)).grid(row=1, column=0, sticky="w", pady=4)
        combo_c = ttk.Combobox(pad, state="readonly", font=("Segoe UI",10))
        combo_c["values"] = [c["nome"] for c in cartoes_com_fat]
        combo_c.current(0)
        combo_c.grid(row=1, column=1, sticky="ew", pady=4)

        tk.Label(pad, text="Fatura", bg=self.CARD, fg=self.FG,
                 font=("Segoe UI",10)).grid(row=2, column=0, sticky="w", pady=4)
        combo_f = ttk.Combobox(pad, state="readonly", font=("Segoe UI",10))
        combo_f.grid(row=2, column=1, sticky="ew", pady=4)

        def parse_mes(f):
            try:
                partes = f["mes"].strip().split()
                m, a = partes[0].split("/")
                return int(a) * 100 + int(m)
            except:
                return 999999

        def atualizar_faturas(*_):
            nome = combo_c.get()
            c = next((x for x in cartoes if x["nome"] == nome), None)
            if c:
                fats = sorted(c.get("faturas", []), key=parse_mes)
                combo_f["values"] = [
                    f["mes"] + "  —  " + ("R$ " + "{:,.2f}".format(f["valor"])).replace(",","X").replace(".",",").replace("X",".")
                    for f in fats]
                if fats:
                    combo_f.current(0)

        combo_c.bind("<<ComboboxSelected>>", atualizar_faturas)
        atualizar_faturas()
        ttk.Separator(pad, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=12)

        if modo == "remover":
            def confirmar():
                nome = combo_c.get()
                idx_f = combo_f.current()
                if idx_f < 0:
                    return
                c = next((x for x in cartoes if x["nome"] == nome), None)
                if not c:
                    return
                fats = sorted(c.get("faturas", []), key=parse_mes)
                fat = fats[idx_f]
                if messagebox.askyesno("Confirmar", "Remover fatura de " + fat["mes"] + "?", parent=win):
                    c["faturas"] = [f for f in c["faturas"]
                                    if not (f["mes"] == fat["mes"] and f["valor"] == fat["valor"])]
                    salvar_cartoes(cartoes)
                    self._atualizar_cartoes()
                    win.destroy()
            tk.Button(pad, text="🗑  Remover", command=confirmar,
                     bg=self.BORDA, fg="#f87171", font=("Segoe UI",10,"bold"),
                     relief="flat", cursor="hand2", padx=12, pady=6,
                     activebackground=self.BORDA, activeforeground="#f87171").grid(
                row=4, column=0, columnspan=2, sticky="ew")
        else:
            tk.Label(pad, text="Novo Mês/Ano", bg=self.CARD, fg=self.FG,
                     font=("Segoe UI",10)).grid(row=4, column=0, sticky="w", pady=4)
            e_mes = tk.Entry(pad, bg=self.ENTRY_BG, fg=self.FG, insertbackground=self.FG,
                            font=("Segoe UI",10), relief="flat", bd=4)
            e_mes.grid(row=4, column=1, sticky="ew", pady=4, ipady=4)
            tk.Label(pad, text="Novo Valor (R$)", bg=self.CARD, fg=self.FG,
                     font=("Segoe UI",10)).grid(row=5, column=0, sticky="w", pady=4)
            e_val = tk.Entry(pad, bg=self.ENTRY_BG, fg=self.FG, insertbackground=self.FG,
                            font=("Segoe UI",10), relief="flat", bd=4)
            e_val.grid(row=5, column=1, sticky="ew", pady=4, ipady=4)

            def preencher(*_):
                nome = combo_c.get()
                idx_f = combo_f.current()
                if idx_f < 0:
                    return
                c = next((x for x in cartoes if x["nome"] == nome), None)
                if not c:
                    return
                fat = sorted(c.get("faturas", []), key=parse_mes)[idx_f]
                e_mes.delete(0, "end"); e_mes.insert(0, fat["mes"])
                e_val.delete(0, "end"); e_val.insert(0, str(fat["valor"]))

            combo_f.bind("<<ComboboxSelected>>", preencher)
            preencher()

            def salvar():
                nome = combo_c.get()
                idx_f = combo_f.current()
                if idx_f < 0:
                    return
                novo_mes = e_mes.get().strip()
                try:
                    novo_valor = float(e_val.get().strip().replace(",","."))
                except ValueError:
                    messagebox.showerror("Erro", "Valor inválido.", parent=win)
                    return
                c = next((x for x in cartoes if x["nome"] == nome), None)
                if not c:
                    return
                fat = sorted(c.get("faturas", []), key=parse_mes)[idx_f]
                for f in c["faturas"]:
                    if f["mes"] == fat["mes"] and f["valor"] == fat["valor"]:
                        f["mes"] = novo_mes; f["valor"] = novo_valor
                        break
                salvar_cartoes(cartoes)
                self._atualizar_cartoes()
                win.destroy()

            ttk.Separator(pad, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", pady=12)
            tk.Button(pad, text="💾  Salvar", command=salvar,
                     bg=self.FG, fg=self.BG, font=("Segoe UI",10,"bold"),
                     relief="flat", cursor="hand2", padx=12, pady=6,
                     activebackground=self.FG, activeforeground=self.BG).grid(
                row=7, column=0, columnspan=2, sticky="ew")

    def _editar_fatura(self):
        self._abrir_gerenciar_fatura("editar")

    def _remover_fatura(self):
        self._abrir_gerenciar_fatura("remover")

    def _atualizar_cartoes(self):
        CORES = ["#E24B4A", "#1D9E75", "#378ADD", "#BA7517", "#D4537E", "#7F77DD"]
        for w in self.frame_cards_cartoes.winfo_children():
            w.destroy()
        self._cartao_idx_sel.set(-1)
        # Limpa cards de faturas
        for w in self.fat_cards_frame.winfo_children():
            w.destroy()
        cartoes = carregar_cartoes()
        nomes = [c["nome"] for c in cartoes]
        self.combo_cartao_gasto["values"] = nomes
        self.combo_cartao_fat["values"]   = nomes
        if nomes:
            if not self.combo_cartao_gasto.get():
                self.combo_cartao_gasto.current(0)
            if not self.combo_cartao_fat.get():
                self.combo_cartao_fat.current(0)
        total_fatura = total_limite = total_comprometido = total_terceiros = 0.0
        def fmt(v): return ("R$ " + "{:,.2f}".format(v)).replace(",","X").replace(".",",").replace("X",".")
        for c in cartoes:
            fatura   = c.get("fatura", 0)
            limite   = c.get("limite", 0)
            proximas = sum(f["valor"] for f in c.get("faturas", []))
            uso = ((fatura + proximas) / limite * 100) if limite > 0 else 0
            eh_terceiro = c.get("terceiro", False)
            if not eh_terceiro:
                total_limite      += limite
                total_comprometido += fatura + proximas
            if eh_terceiro:
                total_terceiros += fatura
            else:
                # Só soma na fatura atual se for do mês atual ou anterior
                mes_fat = c.get("mes_fatura", "")
                fatura_no_mes = True
                if mes_fat:
                    try:
                        from datetime import date as _date
                        mf, af = mes_fat.strip().split("/")
                        from datetime import date as _d
                        hoje2 = _d.today()
                        fat_ref = int(af) * 100 + int(mf)
                        hoje_ref = hoje2.year * 100 + hoje2.month
                        fatura_no_mes = fat_ref <= hoje_ref
                    except:
                        fatura_no_mes = True
                if fatura_no_mes:
                    total_fatura += fatura
            cor_uso = "#f87171" if (not eh_terceiro and uso >= 80) else ("#fbbf24" if (not eh_terceiro and uso >= 50) else (self.FG2 if eh_terceiro else "#ffffff"))

            # Card do cartão
            cidx = len(self.frame_cards_cartoes.winfo_children())
            card_c = tk.Frame(self.frame_cards_cartoes, bg=self.BORDA, padx=12, pady=10,
                             cursor="hand2")
            card_c.pack(fill="x", pady=(0, 6))

            # Header: nome + badge terceiro + fatura
            h = tk.Frame(card_c, bg=self.BORDA)
            h.pack(fill="x")
            tk.Label(h, text=c["nome"], bg=self.BORDA, fg=cor_uso,
                     font=("Segoe UI", 10, "bold")).pack(side="left")
            if c.get("terceiro"):
                tk.Label(h, text=" TERCEIRO", bg=self.BORDA, fg=self.FG2,
                         font=("Segoe UI", 7, "bold")).pack(side="left", padx=(4,0))
            tk.Label(h, text=fmt(fatura), bg=self.BORDA, fg=cor_uso,
                     font=("Segoe UI", 10, "bold")).pack(side="right")

            # Barra de uso e info (apenas para cartões próprios)
            if not c.get("terceiro"):
                barra_c = tk.Frame(card_c, bg=self.CARD, height=4)
                barra_c.pack(fill="x", pady=(6, 6))
                barra_c.pack_propagate(False)
                def _bc(event, b=barra_c, u=uso, cor=cor_uso):
                    for w in b.winfo_children(): w.destroy()
                    larg = b.winfo_width()
                    if larg < 2: return
                    ws = max(1, int(min(u, 100) / 100 * larg))
                    tk.Frame(b, bg=cor, width=ws, height=4).place(x=0, y=0, width=ws, height=4)
                barra_c.bind("<Configure>", _bc)
                info = tk.Frame(card_c, bg=self.BORDA)
                info.pack(fill="x")
                tk.Label(info, text="Limite: " + fmt(limite), bg=self.BORDA, fg=self.FG2,
                         font=("Segoe UI", 8)).pack(side="left")
                tk.Label(info, text=str(round(uso)) + "% usado", bg=self.BORDA, fg=self.FG2,
                         font=("Segoe UI", 8)).pack(side="left", padx=(10, 0))
                tk.Label(info, text="Venc. dia " + str(c.get("vencimento","")),
                         bg=self.BORDA, fg=self.FG2, font=("Segoe UI", 8)).pack(side="right")
            else:
                tk.Label(card_c, text="Gastos registrados: " + str(len(c.get("gastos", []))),
                         bg=self.BORDA, fg=self.FG2, font=("Segoe UI", 8)).pack(anchor="w", pady=(4,0))

            # Botões ação
            btns = tk.Frame(card_c, bg=self.BORDA)
            btns.pack(fill="x", pady=(8, 0))
            def _sel(i=cidx, f=card_c):
                self._cartao_idx_sel.set(i)
                for w in self.frame_cards_cartoes.winfo_children():
                    w.config(bg="#3a3a3a")
                    for ch in w.winfo_children():
                        try: ch.config(bg="#3a3a3a")
                        except: pass
                f.config(bg=self.BORDA)
            cor_btn = "#3a3a3a" if self._tema_atual == "dark" else "#e5e7eb"
            btn(btns, self, "✏ Editar", lambda i=cidx: (self._cartao_idx_sel.set(i), self._editar_cartao()),
                     bg=cor_btn, fg=self.FG2).pack(side="left")
            btn(btns, self, "✅ Pagar", lambda i=cidx: (self._cartao_idx_sel.set(i), self._pagar_fatura()),
                     bg=cor_btn, fg=self.FG2).pack(side="left", padx=(6, 0))
            btn(btns, self, "🗑 Remover", lambda i=cidx: (self._cartao_idx_sel.set(i), self._remover_cartao()),
                     bg=cor_btn, fg=self.FG2).pack(side="right")
            def parse_mes(f):
                try:
                    partes = f["mes"].strip().split()
                    m, a = partes[0].split("/")
                    return int(a) * 100 + int(m)
                except:
                    return 999999
            faturas_ordenadas = sorted(c.get("faturas", []), key=parse_mes)
            if faturas_ordenadas:
                total_prox = sum(f["valor"] for f in faturas_ordenadas)
                cor_card = "#f87171" if uso >= 80 else ("#fbbf24" if uso >= 50 else "#ffffff")
                # Card do cartão
                card = tk.Frame(self.fat_cards_frame, bg=self.BORDA, padx=12, pady=10)
                # card will be placed by _rewrap_fat
                pass  # placed by rewrap
                tk.Label(card, text=c["nome"].upper(), bg=self.BORDA, fg=cor_card,
                         font=("Segoe UI", 9, "bold")).pack(anchor="w")
                tk.Label(card, text="Total: " + fmt(total_prox), bg=self.BORDA, fg=self.FG2,
                         font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 6))
                for fat in faturas_ordenadas:
                    row_f = tk.Frame(card, bg=self.BORDA)
                    row_f.pack(fill="x", pady=1)
                    tk.Label(row_f, text=fat["mes"], bg=self.BORDA, fg=self.FG2,
                             font=("Segoe UI", 8), width=10, anchor="w").pack(side="left")
                    tk.Label(row_f, text=fmt(fat["valor"]), bg=self.BORDA, fg=self.FG,
                             font=("Segoe UI", 9, "bold")).pack(side="left", padx=(4, 0))
        self.fat_cards_frame.update_idletasks()
        if hasattr(self, "_rewrap_fat"): self._rewrap_fat()
        disponivel = total_limite - total_comprometido
        self.card_fatura_total._lbl.config(text=fmt(total_fatura),
            fg="#f87171" if total_fatura > 0 else "#888888")
        # Composição por cartão — opção 3 (barra proporcional + legenda)
        for w in self.card_fatura_total._composicao.winfo_children():
            w.destroy()
        def _fatura_no_mes_atual(c):
            mes_fat = c.get("mes_fatura", "")
            if not mes_fat:
                return True
            try:
                from datetime import date as _d
                mf, af = mes_fat.strip().split("/")
                hoje_ref = _d.today().year * 100 + _d.today().month
                fat_ref  = int(af) * 100 + int(mf)
                return fat_ref <= hoje_ref
            except:
                return True
        cartoes_fat = [(c, c.get("fatura", 0)) for c in cartoes
                       if c.get("fatura", 0) > 0 and not c.get("terceiro") and _fatura_no_mes_atual(c)]
        if cartoes_fat and total_fatura > 0:
            # Barra proporcional
            barra = tk.Frame(self.card_fatura_total._composicao, bg=self.CARD, height=5)
            barra.pack(fill="x", pady=(6, 6))
            barra.pack_propagate(False)
            barra.update_idletasks()
            def _desenhar_barra(event, cartoes_fat=cartoes_fat, barra=barra):
                for w in barra.winfo_children():
                    w.destroy()
                largura = barra.winfo_width()
                if largura < 2:
                    return
                x = 0
                for i, (c, fat) in enumerate(cartoes_fat):
                    cor = CORES[i % len(CORES)]
                    frac = fat / total_fatura
                    w_seg = max(1, int(frac * largura))
                    seg = tk.Frame(barra, bg=cor, width=w_seg, height=5)
                    seg.place(x=x, y=0, width=w_seg, height=5)
                    x += w_seg
            barra.bind("<Configure>", _desenhar_barra)
            # Legenda
            for i, (c, fat) in enumerate(cartoes_fat):
                cor = CORES[i % len(CORES)]
                row = tk.Frame(self.card_fatura_total._composicao, bg=self.CARD)
                row.pack(fill="x", pady=1)
                dot = tk.Frame(row, bg=cor, width=8, height=8)
                dot.pack(side="left", padx=(0, 5))
                dot.pack_propagate(False)
                tk.Label(row, text=c["nome"], bg=self.CARD, fg=self.FG2,
                         font=("Segoe UI", 8)).pack(side="left")
                tk.Label(row, text=fmt(fat), bg=self.CARD, fg=self.FG,
                         font=("Segoe UI", 8, "bold")).pack(side="right")
        total_proximas = total_comprometido - total_fatura
        self.card_proximas._lbl.config(text=fmt(total_proximas),
            fg="#fbbf24" if total_proximas > 0 else "#888888")

        # Composição Próximas Faturas
        for w in self.card_proximas._composicao.winfo_children():
            w.destroy()
        cartoes_prox = [(c, sum(f["valor"] for f in c.get("faturas", []))) for c in cartoes]
        cartoes_prox = [(c, v) for c, v in cartoes_prox if v > 0]
        if cartoes_prox and total_proximas > 0:
            barra2 = tk.Frame(self.card_proximas._composicao, bg=self.CARD, height=5)
            barra2.pack(fill="x", pady=(6, 6))
            barra2.pack_propagate(False)
            def _barra2(event, cp=cartoes_prox, b=barra2, tot=total_proximas):
                for w in b.winfo_children(): w.destroy()
                larg = b.winfo_width()
                if larg < 2: return
                x = 0
                for i, (c, v) in enumerate(cp):
                    cor = CORES[i % len(CORES)]
                    ws = max(1, int(v / tot * larg))
                    tk.Frame(b, bg=cor, width=ws, height=5).place(x=x, y=0, width=ws, height=5)
                    x += ws
            barra2.bind("<Configure>", _barra2)
            for i, (c, v) in enumerate(cartoes_prox):
                cor = CORES[i % len(CORES)]
                row = tk.Frame(self.card_proximas._composicao, bg=self.CARD)
                row.pack(fill="x", pady=1)
                dot = tk.Frame(row, bg=cor, width=8, height=8)
                dot.pack(side="left", padx=(0, 5))
                dot.pack_propagate(False)
                tk.Label(row, text=c["nome"], bg=self.CARD, fg=self.FG2,
                         font=("Segoe UI", 8)).pack(side="left")
                tk.Label(row, text=fmt(v), bg=self.CARD, fg=self.FG,
                         font=("Segoe UI", 8, "bold")).pack(side="right")

        # Composição Limite Total
        self.card_limite_total._lbl.config(text=fmt(total_limite))
        for w in self.card_limite_total._composicao.winfo_children():
            w.destroy()
        cartoes_proprios = [c for c in cartoes if not c.get("terceiro")]
        if cartoes_proprios and total_limite > 0:
            barra3 = tk.Frame(self.card_limite_total._composicao, bg=self.CARD, height=5)
            barra3.pack(fill="x", pady=(6, 6))
            barra3.pack_propagate(False)
            def _barra3(event, b=barra3):
                for w in b.winfo_children(): w.destroy()
                larg = b.winfo_width()
                if larg < 2: return
                x = 0
                for i, c in enumerate(cartoes_proprios):
                    cor = CORES[i % len(CORES)]
                    ws = max(1, int(c.get("limite", 0) / total_limite * larg))
                    tk.Frame(b, bg=cor, width=ws, height=5).place(x=x, y=0, width=ws, height=5)
                    x += ws
            barra3.bind("<Configure>", _barra3)
            for i, c in enumerate(cartoes_proprios):
                cor = CORES[i % len(CORES)]
                row = tk.Frame(self.card_limite_total._composicao, bg=self.CARD)
                row.pack(fill="x", pady=1)
                dot = tk.Frame(row, bg=cor, width=8, height=8)
                dot.pack(side="left", padx=(0, 5))
                dot.pack_propagate(False)
                tk.Label(row, text=c["nome"], bg=self.CARD, fg=self.FG2,
                         font=("Segoe UI", 8)).pack(side="left")
                tk.Label(row, text=fmt(c.get("limite", 0)), bg=self.CARD, fg=self.FG,
                         font=("Segoe UI", 8, "bold")).pack(side="right")

        # Composição Disponível
        self.card_disponivel._lbl.config(text=fmt(disponivel),
            fg=self.FG if disponivel >= 0 else "#f87171")

        # Card gastos em terceiros
        self.card_terceiros._lbl.config(
            text=fmt(total_terceiros),
            fg="#fbbf24" if total_terceiros > 0 else self.FG2)
        for w in self.card_terceiros._composicao.winfo_children():
            w.destroy()
        cartoes_terc = [(c, c.get("fatura", 0)) for c in cartoes if c.get("terceiro") and c.get("fatura", 0) > 0]
        for c, fat in cartoes_terc:
            row = tk.Frame(self.card_terceiros._composicao, bg=self.CARD)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=c["nome"], bg=self.CARD, fg=self.FG2,
                     font=("Segoe UI", 8)).pack(side="left")
            tk.Label(row, text=fmt(fat), bg=self.CARD, fg=self.FG,
                     font=("Segoe UI", 8, "bold")).pack(side="right")
        for w in self.card_disponivel._composicao.winfo_children():
            w.destroy()
        if cartoes:
            disp_por_cartao = [(c, max(0, c.get("limite", 0) - c.get("fatura", 0) - sum(f["valor"] for f in c.get("faturas", [])))) for c in cartoes if not c.get("terceiro")]
            total_disp = sum(v for _, v in disp_por_cartao)
            if total_disp > 0:
                barra4 = tk.Frame(self.card_disponivel._composicao, bg=self.CARD, height=5)
                barra4.pack(fill="x", pady=(6, 6))
                barra4.pack_propagate(False)
                def _barra4(event, dp=disp_por_cartao, b=barra4, tot=total_disp):
                    for w in b.winfo_children(): w.destroy()
                    larg = b.winfo_width()
                    if larg < 2: return
                    x = 0
                    for i, (c, v) in enumerate(dp):
                        cor = CORES[i % len(CORES)]
                        ws = max(1, int(v / tot * larg))
                        tk.Frame(b, bg=cor, width=ws, height=5).place(x=x, y=0, width=ws, height=5)
                        x += ws
                barra4.bind("<Configure>", _barra4)
                for i, (c, v) in enumerate(disp_por_cartao):
                    cor = CORES[i % len(CORES)]
                    row = tk.Frame(self.card_disponivel._composicao, bg=self.CARD)
                    row.pack(fill="x", pady=1)
                    dot = tk.Frame(row, bg=cor, width=8, height=8)
                    dot.pack(side="left", padx=(0, 5))
                    dot.pack_propagate(False)
                    tk.Label(row, text=c["nome"], bg=self.CARD, fg=self.FG2,
                             font=("Segoe UI", 8)).pack(side="left")
                    tk.Label(row, text=fmt(v), bg=self.CARD, fg=self.FG,
                             font=("Segoe UI", 8, "bold")).pack(side="right")

    def _calcular_simulacao(self):
        try:
            valor = float(self.sim_entries["sim_valor"].get().strip().replace(",", "."))
            n     = int(self.sim_entries["sim_parcelas"].get().strip())
        except ValueError:
            self.lbl_simulacao.config(text="⚠ Preencha os campos corretamente.")
            return
        parcela = valor / n
        def fmt(v): return ("R$ " + "{:,.2f}".format(v)).replace(",","X").replace(".",",").replace("X",".")
        self.lbl_simulacao.config(
            text="Parcela:  " + fmt(parcela) + "\nTotal pago:  " + fmt(valor))