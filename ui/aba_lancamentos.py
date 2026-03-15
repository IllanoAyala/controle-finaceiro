import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date

from constants import CATEGORIAS_DESPESA, CATEGORIAS_RECEITA, MESES
from database import (
    carregar_dados_com_id, adicionar_lancamento,
    apagar_lancamento_db, editar_lancamento_db,
    carregar_cartoes, salvar_cartoes,
)
from ui.widgets import fmt, entry_widget, btn


class AbaLancamentos:
    """Mixin — métodos da aba de Lançamentos."""

    def _construir_aba_lancamentos(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=2)
        parent.rowconfigure(1, weight=1)
        resumo = ttk.Frame(parent, style="TFrame")
        resumo.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self._criar_cards_resumo(resumo)
        form = ttk.Frame(parent, style="Card.TFrame", padding=20)
        form.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self._criar_formulario(form)
        tabela = ttk.Frame(parent, style="Card.TFrame", padding=(12, 12))
        tabela.grid(row=1, column=1, sticky="nsew")
        self._criar_tabela(tabela)
        self._atualizar_tabela()

    def _criar_cards_resumo(self, parent):
        for i in range(4):
            parent.columnconfigure(i, weight=1)
        dados = [
            ("↑  Total Receitas", "receitas",   "Receita.TLabel"),
            ("↓  Total Despesas", "despesas",   "Despesa.TLabel"),
            ("=  Saldo",          "saldo",       "CardVal.TLabel"),
            ("#  Lançamentos",    "lancamentos", "CardVal.TLabel"),
        ]
        self.card_labels = {}
        for i, (titulo, key, estilo) in enumerate(dados):
            c = ttk.Frame(parent, style="Card.TFrame", padding=(16, 12))
            c.grid(row=0, column=i, sticky="ew", padx=(0, 8) if i < 3 else 0)
            ttk.Label(c, text=titulo, style="CardTitle.TLabel").pack(anchor="w")
            lbl = ttk.Label(c, text="R$ 0,00", style=estilo)
            lbl.pack(anchor="w", pady=(4, 0))
            self.card_labels[key] = lbl

    def _criar_formulario(self, parent):
        ttk.Label(parent, text="NOVO LANÇAMENTO", style="CardTitle.TLabel",
                  font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2,
                  sticky="w", pady=(0, 14))
        def lbl(row, txt):
            ttk.Label(parent, text=txt, style="Card.TLabel").grid(
                row=row, column=0, sticky="w", pady=4)
        lbl(1, "Data")
        self.entry_data = entry_widget(parent, self, row=1, col=1)
        self.entry_data.insert(0, date.today().strftime("%d/%m/%Y"))
        lbl(2, "Descrição")
        self.entry_desc = entry_widget(parent, self, row=2, col=1)
        lbl(3, "Tipo")
        self.var_tipo = tk.StringVar(value="Despesa")
        ft = ttk.Frame(parent, style="Card.TFrame")
        ft.grid(row=3, column=1, sticky="ew", pady=4)
        for t in ["Despesa", "Receita"]:
            tk.Radiobutton(ft, text=t, variable=self.var_tipo, value=t,
                          command=self._atualizar_categorias,
                          bg=self.CARD, fg=self.FG, selectcolor=self.BORDA,
                          activebackground=self.CARD, activeforeground=self.FG,
                          font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))
        lbl(4, "Categoria")
        self.combo_cat = ttk.Combobox(parent, state="readonly", font=("Segoe UI", 10))
        self.combo_cat.grid(row=4, column=1, sticky="ew", pady=4)
        self._atualizar_categorias()
        lbl(5, "Valor (R$)")
        self.entry_valor = entry_widget(parent, self, row=5, col=1)
        parent.columnconfigure(1, weight=1)
        self.lbl_cartao_lanc = ttk.Label(parent, text="Cartão", style="Card.TLabel")
        self.combo_cartao_lanc = ttk.Combobox(parent, state="readonly", font=("Segoe UI", 10))
        self.combo_cat.bind("<<ComboboxSelected>>", self._toggle_cartao_selector)
        ttk.Separator(parent, orient="horizontal").grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=14)
        btn(parent, self, "＋  Adicionar Lançamento", self._salvar).grid(
            row=8, column=0, columnspan=2, sticky="ew")
        btn(parent, self, "🗑  Apagar Lançamento Selecionado", self._apagar_lancamento,
                 bg=self.BORDA, fg=self.FG2).grid(
            row=9, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        btn(parent, self, "✏  Editar Selecionado", self._editar_lancamento,
                 bg=self.BORDA, fg=self.FG2).grid(
            row=10, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def _atualizar_categorias(self, *_):
        tipo = self.var_tipo.get()
        cats = CATEGORIAS_RECEITA if tipo == "Receita" else CATEGORIAS_DESPESA
        self.combo_cat["values"] = cats
        self.combo_cat.current(0)
        self._toggle_cartao_selector()

    def _toggle_cartao_selector(self, *_):
        if not hasattr(self, "lbl_cartao_lanc"):
            return
        if self.combo_cat.get() == "(D) Cartão de Crédito":
            cartoes = carregar_cartoes()
            nomes = [c["nome"] for c in cartoes]
            self.combo_cartao_lanc["values"] = nomes
            if nomes and not self.combo_cartao_lanc.get():
                self.combo_cartao_lanc.current(0)
            self.lbl_cartao_lanc.grid(row=6, column=0, sticky="w", pady=4)
            self.combo_cartao_lanc.grid(row=6, column=1, sticky="ew", pady=4, ipady=4)
        else:
            self.lbl_cartao_lanc.grid_remove()
            self.combo_cartao_lanc.grid_remove()

    def _criar_tabela(self, parent):
        ttk.Label(parent, text="ÚLTIMOS LANÇAMENTOS", style="CardTitle.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))
        ff = ttk.Frame(parent, style="Card.TFrame")
        ff.pack(fill="x", pady=(0, 8))
        ttk.Label(ff, text="Filtrar mês:", style="Card.TLabel").pack(side="left", padx=(0, 6))
        self.combo_mes = ttk.Combobox(ff, values=["Todos"] + list(MESES.values()),
                                      state="readonly", width=8)
        self.combo_mes.set("Todos")
        self.combo_mes.pack(side="left")
        self.combo_mes.bind("<<ComboboxSelected>>", lambda e: self._atualizar_tabela())
        cols = ("Data", "Descrição", "Tipo", "Categoria", "Valor")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=16)
        for col, w in zip(cols, [80, 130, 70, 160, 90]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w,
                anchor="center" if col not in ("Descrição", "Categoria") else "w")
        sc = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
        self.tree.tag_configure("receita",        foreground=self.FG)
        self.tree.tag_configure("despesa",        foreground=self.FG2)
        self.tree.tag_configure("despesa_cartao", foreground="#555555")

    def _atualizar_tabela(self):
        try:
            todos = carregar_dados_com_id()
        except Exception:
            return
        mes_filtro = self.combo_mes.get()
        dados = [r for r in todos if r["Mês"] == mes_filtro] if mes_filtro != "Todos" else todos
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in dados:
            ds = r["Data"].strftime("%d/%m/%Y") if hasattr(r["Data"], "strftime") else str(r["Data"])
            tipo = r["Tipo"]
            valor = r["Receita"] if tipo == "Receita" else r["Despesa"]
            sinal = "+" if tipo == "Receita" else "-"
            tag = "receita" if tipo == "Receita" else ("despesa_cartao" if tipo == "Despesa Cartão" else "despesa")
            self.tree.insert("", "end", iid=str(r["id"]), values=(
                ds, r["Descrição"], tipo, r["Categoria"],
                (sinal + " R$ " + "{:,.2f}".format(valor)).replace(",","X").replace(".",",").replace("X",".")
            ), tags=(tag,))
        tr = sum(r["Receita"] for r in todos)
        td = sum(r["Despesa"] for r in todos if r["Tipo"] != "Despesa Cartão")
        saldo = tr - td
        def fmt(v): return ("R$ " + "{:,.2f}".format(v)).replace(",","X").replace(".",",").replace("X",".")
        self.card_labels["receitas"].config(text=fmt(tr))
        self.card_labels["despesas"].config(text=fmt(td))
        self.card_labels["saldo"].config(text=fmt(saldo),
            foreground=self.FG if saldo >= 0 else self.FG2)
        self.card_labels["lancamentos"].config(text=str(len(todos)))

    def _salvar(self):
        data_str = self.entry_data.get().strip()
        descricao = self.entry_desc.get().strip()
        tipo = self.var_tipo.get()
        categoria = self.combo_cat.get()
        valor_str = self.entry_valor.get().strip().replace(",", ".")
        if not data_str or not descricao or not valor_str:
            messagebox.showwarning("Campos vazios", "Preencha todos os campos!")
            return
        try:
            data = datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Data inválida", "Use o formato DD/MM/AAAA")
            return
        try:
            valor = float(valor_str)
            if valor <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Valor inválido", "Digite um valor numérico positivo.")
            return
        try:
            if categoria == "(D) Cartão de Crédito":
                nome_cartao = self.combo_cartao_lanc.get() if hasattr(self, "combo_cartao_lanc") else ""
                if not nome_cartao:
                    messagebox.showwarning("Atenção", "Selecione um cartão.")
                    return
                cartoes = carregar_cartoes()
                for c in cartoes:
                    if c["nome"] == nome_cartao:
                        c["fatura"] = c.get("fatura", 0) + valor
                        if "gastos" not in c:
                            c["gastos"] = []
                        c["gastos"].append({"desc": descricao, "valor": valor,
                                            "data": data.strftime("%d/%m/%Y")})
                        break
                salvar_cartoes(cartoes)
                adicionar_lancamento(data, "[" + nome_cartao + "] " + descricao, "Despesa Cartão", categoria, valor)
            else:
                adicionar_lancamento(data, descricao, tipo, categoria, valor)
            self.entry_desc.delete(0, "end")
            self.entry_valor.delete(0, "end")
            self._atualizar_tabela()
            if hasattr(self, "frame_cards_cartoes"):
                self._atualizar_cartoes()
            messagebox.showinfo("Sucesso", "Lançamento \"" + descricao + "\" adicionado!")
        except Exception as e:
            messagebox.showerror("Erro", "Não foi possível salvar:\n" + str(e))

    def _apagar_lancamento(self):
        import re
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um lançamento na tabela para apagar.")
            return
        lanc_id = int(sel[0])
        valores = self.tree.item(sel[0])["values"]
        desc = str(valores[1])
        tipo = str(valores[2])
        if not messagebox.askyesno("Confirmar", "Apagar o lançamento \"" + desc + "\"?"):
            return
        try:
            if tipo == "Despesa Cartão":
                v = re.sub(r"[^0-9,]", "", str(valores[4]))
                if "," in v:
                    partes = v.rsplit(",", 1)
                    v = partes[0].replace(",","") + "." + partes[1]
                try:
                    valor = float(v)
                except:
                    valor = 0.0
                match = re.match(r'^\[(.+?)\]\s*(.*)', desc)
                if match and valor > 0:
                    nome_cartao = match.group(1).strip()
                    desc_sem = match.group(2).strip()
                    cartoes = carregar_cartoes()
                    for c in cartoes:
                        if c["nome"] == nome_cartao:
                            c["fatura"] = max(0.0, round(c.get("fatura", 0) - valor, 2))
                            novos = []
                            removido = False
                            for g in c.get("gastos", []):
                                if not removido and g["desc"] == desc_sem and abs(g["valor"] - valor) < 0.02:
                                    removido = True
                                else:
                                    novos.append(g)
                            c["gastos"] = novos
                            break
                    salvar_cartoes(cartoes)
            apagar_lancamento_db(lanc_id)
            self._atualizar_tabela()
            if hasattr(self, "frame_cards_cartoes"):
                self._atualizar_cartoes()
        except Exception as e:
            messagebox.showerror("Erro", "Não foi possível apagar:\n" + str(e))

    def _editar_lancamento(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um lançamento para editar.")
            return
        lanc_id = int(sel[0])
        valores = self.tree.item(sel[0])["values"]
        data_str  = valores[0]
        desc      = valores[1]
        tipo      = valores[2]
        categoria = valores[3]
        valor_str = str(valores[4]).replace("+","").replace("-","").strip()
        valor_str = valor_str.replace("R$","").replace(".","").replace(",",".").strip()
        win = tk.Toplevel(self)
        win.title("Editar Lançamento")
        win.configure(bg=self.CARD)
        win.resizable(False, False)
        win.grab_set()
        win.geometry("360x380")
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 360) // 2
        y = self.winfo_y() + (self.winfo_height() - 380) // 2
        win.geometry("360x380+" + str(x) + "+" + str(y))
        pad = tk.Frame(win, bg=self.CARD, padx=20, pady=16)
        pad.pack(fill="both", expand=True)
        pad.columnconfigure(1, weight=1)
        tk.Label(pad, text="EDITAR LANÇAMENTO", bg=self.CARD, fg=self.FG2,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,12))
        def lbl(r, txt):
            tk.Label(pad, text=txt, bg=self.CARD, fg=self.FG,
                     font=("Segoe UI", 10)).grid(row=r, column=0, sticky="w", pady=4)
        lbl(1, "Data")
        e_data = tk.Entry(pad, bg=self.ENTRY_BG, fg=self.FG, insertbackground=self.FG,
                         font=("Segoe UI",10), relief="flat", bd=4)
        e_data.grid(row=1, column=1, sticky="ew", pady=4, ipady=4)
        e_data.insert(0, data_str)
        lbl(2, "Descrição")
        e_desc = tk.Entry(pad, bg=self.ENTRY_BG, fg=self.FG, insertbackground=self.FG,
                         font=("Segoe UI",10), relief="flat", bd=4)
        e_desc.grid(row=2, column=1, sticky="ew", pady=4, ipady=4)
        e_desc.insert(0, desc)
        lbl(3, "Tipo")
        var_tipo = tk.StringVar(value=tipo if tipo in ("Despesa","Receita") else "Despesa")
        ft = tk.Frame(pad, bg=self.CARD)
        ft.grid(row=3, column=1, sticky="w", pady=4)
        for t in ["Despesa", "Receita"]:
            tk.Radiobutton(ft, text=t, variable=var_tipo, value=t,
                          bg=self.CARD, fg=self.FG, selectcolor=self.BORDA,
                          activebackground=self.CARD, activeforeground=self.FG,
                          highlightthickness=0, font=("Segoe UI",10)).pack(side="left", padx=(0,10))
        lbl(4, "Categoria")
        combo_cat = ttk.Combobox(pad, state="readonly", font=("Segoe UI",10))
        all_cats = CATEGORIAS_DESPESA + CATEGORIAS_RECEITA
        combo_cat["values"] = all_cats
        combo_cat.grid(row=4, column=1, sticky="ew", pady=4)
        if categoria in all_cats:
            combo_cat.current(all_cats.index(categoria))
        else:
            combo_cat.current(0)
        lbl(5, "Valor (R$)")
        e_valor = tk.Entry(pad, bg=self.ENTRY_BG, fg=self.FG, insertbackground=self.FG,
                          font=("Segoe UI",10), relief="flat", bd=4)
        e_valor.grid(row=5, column=1, sticky="ew", pady=4, ipady=4)
        e_valor.insert(0, valor_str)
        ttk.Separator(pad, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", pady=12)
        def salvar_edicao():
            try:
                nova_data = datetime.strptime(e_data.get().strip(), "%d/%m/%Y").date()
            except ValueError:
                messagebox.showerror("Erro", "Data inválida. Use DD/MM/AAAA", parent=win)
                return
            novo_desc = e_desc.get().strip()
            novo_tipo = var_tipo.get()
            nova_cat  = combo_cat.get()
            try:
                novo_valor = float(e_valor.get().strip().replace(",","."))
                if novo_valor <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Erro", "Valor inválido.", parent=win)
                return
            try:
                editar_lancamento_db(lanc_id, nova_data, novo_desc, novo_tipo, nova_cat, novo_valor)
                self._atualizar_tabela()
                win.destroy()
            except Exception as e:
                messagebox.showerror("Erro", "Não foi possível salvar:\n" + str(e), parent=win)
        tk.Button(pad, text="💾  Salvar Alterações", command=salvar_edicao,
                 bg=self.FG, fg=self.BG, font=("Segoe UI",10,"bold"),
                 relief="flat", cursor="hand2", padx=12, pady=6,
                 activebackground=self.FG, activeforeground=self.BG).grid(
            row=7, column=0, columnspan=2, sticky="ew")

    # ══════════════════════════════════════════════════════════════════════════
    # ABA CARTÕES DE CRÉDITO
    # ══════════════════════════════════════════════════════════════════════════
