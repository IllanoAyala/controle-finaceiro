import tkinter as tk
from tkinter import ttk
from datetime import date
from collections import defaultdict

from database import carregar_dados_com_id
from ui.widgets import fmt, btn

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

MESES_ORDEM = ["JAN","FEV","MAR","ABR","MAI","JUN","JUL","AGO","SET","OUT","NOV","DEZ"]
MESES_NUM   = {v: i+1 for i, v in enumerate(MESES_ORDEM)}

CORES_CAT = [
    "#E24B4A","#1D9E75","#378ADD","#BA7517","#D4537E","#7F77DD",
    "#EF9F27","#5DCAA5","#F0997B","#85B7EB","#C0DD97","#ED93B1",
]


class AbaAnalises:
    """Mixin — métodos da aba de Análises."""

    def _construir_aba_analises(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # ── Seletor de mês ──────────────────────────────────────────────────
        ctrl = tk.Frame(parent, bg=self.BG)
        ctrl.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        tk.Label(ctrl, text="Mês de referência:", bg=self.BG, fg=self.FG2,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))

        self._analise_mes = tk.StringVar(value=self._mes_atual_str())
        meses_disp = ["Todos"] + [
            f"{str(m).zfill(2)}/{y}"
            for y in range(2024, date.today().year + 2)
            for m in range(1, 13)
        ]
        combo = ttk.Combobox(ctrl, textvariable=self._analise_mes,
                             values=meses_disp, state="readonly",
                             width=10, font=("Segoe UI", 10))
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda e: self._atualizar_analises())

        tk.Button(ctrl, text="↺", command=self._atualizar_analises,
                  bg=self.BORDA, fg=self.FG2,
                  font=("Segoe UI", 10), relief="flat",
                  cursor="hand2", padx=10, pady=4,
                  activebackground=self.BORDA, activeforeground=self.FG
                  ).pack(side="right")

        # ── Canvas com scroll ───────────────────────────────────────────────
        outer = tk.Frame(parent, bg=self.BG)
        outer.grid(row=1, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        canvas_scroll = tk.Canvas(outer, bg=self.BG, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas_scroll.yview)
        canvas_scroll.configure(yscrollcommand=scroll.set)
        canvas_scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        self._analises_frame = tk.Frame(canvas_scroll, bg=self.BG)
        self._analises_win = canvas_scroll.create_window(
            (0, 0), window=self._analises_frame, anchor="nw")

        def _resize(e):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
            canvas_scroll.itemconfig(self._analises_win, width=e.width)

        canvas_scroll.bind("<Configure>", _resize)
        self._analises_frame.bind(
            "<Configure>",
            lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        )
        canvas_scroll.bind_all("<MouseWheel>",
            lambda e: canvas_scroll.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._analises_frame.columnconfigure(0, weight=1)
        self._analises_frame.columnconfigure(1, weight=1)

        self._atualizar_analises()

    def _mes_atual_str(self):
        t = date.today()
        return f"{str(t.month).zfill(2)}/{t.year}"

    def _atualizar_analises(self):
        for w in self._analises_frame.winfo_children():
            w.destroy()
        plt.close("all")

        dados = carregar_dados_com_id()
        mes_sel = self._analise_mes.get()

        # Filtra dados do mês selecionado
        if mes_sel != "Todos":
            m, a = mes_sel.split("/")
            dados_mes = [d for d in dados
                         if d["Data"].month == int(m) and d["Data"].year == int(a)]
        else:
            dados_mes = dados

        # Mês anterior
        if mes_sel != "Todos":
            m_int, a_int = int(m), int(a)
            m_ant = m_int - 1 if m_int > 1 else 12
            a_ant = a_int if m_int > 1 else a_int - 1
            dados_ant = [d for d in dados
                         if d["Data"].month == m_ant and d["Data"].year == a_ant]
        else:
            dados_ant = []

        self._render_cards_resumo(dados_mes, dados_ant)
        self._render_pizza_categorias(dados_mes)
        self._render_barras_mensais(dados)
        self._render_evolucao_saldo(dados)
        self._render_top5(dados_mes)

    def _section(self, titulo, row, col, colspan=1):
        f = tk.Frame(self._analises_frame, bg=self.CARD)
        f.grid(row=row, column=col, columnspan=colspan,
               sticky="nsew", padx=(0, 8) if col == 0 else 0, pady=(0, 12))
        tk.Label(f, text=titulo, bg=self.CARD, fg=self.FG2,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        return f

    def _render_cards_resumo(self, dados_mes, dados_ant):
        f = self._section("RESUMO DO PERÍODO", row=0, col=0, colspan=2)
        inner = tk.Frame(f, bg=self.CARD)
        inner.pack(fill="x", padx=14, pady=(0, 12))
        for i in range(4):
            inner.columnconfigure(i, weight=1)

        rec   = sum(d["Receita"] for d in dados_mes)
        desp  = sum(d["Despesa"] for d in dados_mes if d["Tipo"] != "Despesa Cartão")
        saldo = rec - desp
        n     = len(dados_mes)

        rec_ant  = sum(d["Receita"] for d in dados_ant)
        desp_ant = sum(d["Despesa"] for d in dados_ant if d["Tipo"] != "Despesa Cartão")

        def var_str(atual, ant):
            if ant == 0:
                return ""
            diff = atual - ant
            pct  = (diff / ant) * 100
            cor  = "#10b981" if diff <= 0 else "#f87171"
            if atual == rec:  # receita: subir é bom
                cor = "#10b981" if diff >= 0 else "#f87171"
            return (f"{'▲' if diff > 0 else '▼'} {abs(pct):.1f}%", cor)

        cards = [
            ("Receitas", fmt(rec),  var_str(rec, rec_ant),   "#10b981"),
            ("Despesas", fmt(desp), var_str(desp, desp_ant), "#f87171"),
            ("Saldo",    fmt(saldo), "",                     self.FG if saldo >= 0 else "#f87171"),
            ("Lançamentos", str(n), "",                      self.FG2),
        ]
        for i, (titulo, valor, var, cor) in enumerate(cards):
            c = tk.Frame(inner, bg=self.BORDA, padx=12, pady=10)
            c.grid(row=0, column=i, sticky="nsew", padx=(0, 8) if i < 3 else 0)
            tk.Label(c, text=titulo, bg=self.BORDA, fg=self.FG2,
                     font=("Segoe UI", 8)).pack(anchor="w")
            tk.Label(c, text=valor, bg=self.BORDA, fg=cor,
                     font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(2, 0))
            if var:
                txt, vcor = var
                tk.Label(c, text=txt, bg=self.BORDA, fg=vcor,
                         font=("Segoe UI", 8)).pack(anchor="w")

    def _render_pizza_categorias(self, dados_mes):
        f = self._section("GASTOS POR CATEGORIA", row=1, col=0)
        despesas = [d for d in dados_mes if d["Tipo"] != "Receita"]
        if not despesas:
            tk.Label(f, text="Sem dados para o período.", bg=self.CARD, fg=self.FG2,
                     font=("Segoe UI", 9)).pack(padx=14, pady=20)
            return

        por_cat = defaultdict(float)
        for d in despesas:
            cat = d["Categoria"].replace("(D) ", "").replace("(R) ", "")
            por_cat[cat] += d["Despesa"]

        cats   = sorted(por_cat.items(), key=lambda x: x[1], reverse=True)
        labels = [c[0] for c in cats]
        vals   = [c[1] for c in cats]
        cores  = CORES_CAT[:len(vals)]

        bg = self.CARD
        fig, ax = plt.subplots(figsize=(4.2, 3.2), facecolor=bg)
        ax.set_facecolor(bg)
        wedges, _ = ax.pie(vals, colors=cores, startangle=90,
                           wedgeprops={"linewidth": 0.5, "edgecolor": bg})
        ax.axis("equal")
        ax.format_coord = lambda x, y: ""

        # Legenda
        patches = [mpatches.Patch(color=cores[i],
                   label=f"{labels[i]}: {fmt(vals[i])}")
                   for i in range(len(labels))]
        ax.legend(handles=patches, loc="center left", bbox_to_anchor=(1, 0.5),
                  fontsize=7, frameon=False,
                  labelcolor=self.FG,
                  facecolor=bg)
        fig.patch.set_facecolor(bg)
        plt.tight_layout(pad=0.5)

        # Tooltip para pizza
        tooltip_ann = [None]
        def on_pie_hover(event):
            if event.inaxes != ax:
                if tooltip_ann[0]:
                    tooltip_ann[0].remove()
                    tooltip_ann[0] = None
                    canvas_obj[0].draw_idle()
                return
            for i, wedge in enumerate(wedges):
                if wedge.contains_point([event.x, event.y]):
                    pct = vals[i] / sum(vals) * 100
                    txt = f"{labels[i]}\n{fmt(vals[i])} ({pct:.1f}%)"
                    if tooltip_ann[0]:
                        tooltip_ann[0].remove()
                    tooltip_ann[0] = ax.annotate(
                        txt,
                        xy=(event.xdata, event.ydata),
                        xytext=(10, 10), textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.3", facecolor=self.BORDA,
                                  edgecolor=self.FG2, linewidth=0.5),
                        color=self.FG, fontsize=8,
                    )
                    canvas_obj[0].draw_idle()
                    return
            if tooltip_ann[0]:
                tooltip_ann[0].remove()
                tooltip_ann[0] = None
                canvas_obj[0].draw_idle()

        canvas_obj = [None]
        fig._pie_hover_cb = on_pie_hover
        fig.canvas.mpl_connect("motion_notify_event", on_pie_hover)

        self._embed_chart(fig, f)
        canvas_obj[0] = fig.canvas

    def _embed_chart(self, fig, parent):
        """Embeds a matplotlib figure with interactive toolbar."""
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        toolbar_frame = tk.Frame(parent, bg=self.CARD)
        toolbar_frame.pack(fill="x", padx=8)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.config(background=self.CARD)
        for w in toolbar.winfo_children():
            try:
                w.config(background=self.CARD, foreground=self.FG2,
                         activebackground=self.BORDA)
            except:
                pass
        toolbar.update()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 4))
        # Tooltip on hover
        self._add_tooltip(fig, canvas)

    def _add_tooltip(self, fig, canvas):
        """Shows value tooltip on mouse hover."""
        tooltip_box = [None]

        def on_motion(event):
            if event.inaxes is None:
                if tooltip_box[0]:
                    tooltip_box[0].remove()
                    tooltip_box[0] = None
                    canvas.draw_idle()
                return
            ax = event.inaxes
            txt = ""
            for line in ax.get_lines():
                xdata, ydata = line.get_xdata(), line.get_ydata()
                if len(xdata) == 0:
                    continue
                # Find nearest point
                dists = [abs(x - event.xdata) for x in xdata]
                idx = dists.index(min(dists))
                if min(dists) < (max(xdata) - min(xdata) + 1) * 0.05 + 1:
                    txt = f"R$ {ydata[idx]:,.2f}".replace(",","X").replace(".",",").replace("X",".")
                    break
            if txt:
                if tooltip_box[0]:
                    tooltip_box[0].remove()
                tooltip_box[0] = ax.annotate(
                    txt,
                    xy=(event.xdata, event.ydata),
                    xytext=(10, 10), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=self.BORDA,
                              edgecolor=self.FG2, linewidth=0.5),
                    color=self.FG, fontsize=8,
                )
                canvas.draw_idle()
            elif tooltip_box[0]:
                tooltip_box[0].remove()
                tooltip_box[0] = None
                canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_motion)

    def _render_barras_mensais(self, dados):
        f = self._section("RECEITA VS DESPESA", row=1, col=1)
        mes_sel = self._analise_mes.get()

        if mes_sel == "Todos":
            # Mostra últimos 12 meses
            por_mes = defaultdict(lambda: {"rec": 0, "desp": 0})
            for d in dados:
                chave = f"{str(d['Data'].month).zfill(2)}/{d['Data'].year}"
                if d["Tipo"] == "Receita":
                    por_mes[chave]["rec"] += d["Receita"]
                elif d["Tipo"] != "Despesa Cartão":
                    por_mes[chave]["desp"] += d["Despesa"]
            meses_sorted = sorted(por_mes.keys(),
                                  key=lambda x: (int(x.split("/")[1]), int(x.split("/")[0])))[-12:]
            recs  = [por_mes[m]["rec"]  for m in meses_sorted]
            desps = [por_mes[m]["desp"] for m in meses_sorted]
            labels = [f"{m.split('/')[0]}/{m.split('/')[1][2:]}" for m in meses_sorted]
        else:
            # Mostra só o mês selecionado
            m_int, a_int = int(mes_sel.split("/")[0]), int(mes_sel.split("/")[1])
            dados_mes = [d for d in dados
                         if d["Data"].month == m_int and d["Data"].year == a_int]
            if not dados_mes:
                tk.Label(f, text="Sem dados para o período.", bg=self.CARD, fg=self.FG2,
                         font=("Segoe UI", 9)).pack(padx=14, pady=20)
                return
            rec  = sum(d["Receita"] for d in dados_mes)
            desp = sum(d["Despesa"] for d in dados_mes if d["Tipo"] != "Despesa Cartão")
            recs   = [rec]
            desps  = [desp]
            labels = [f"{mes_sel.split('/')[0]}/{mes_sel.split('/')[1][2:]}"]

        if not dados:
            tk.Label(f, text="Sem dados.", bg=self.CARD, fg=self.FG2,
                     font=("Segoe UI", 9)).pack(padx=14, pady=20)
            return

        bg = self.CARD
        fig, ax = plt.subplots(figsize=(4.2, 3.2), facecolor=bg)
        ax.set_facecolor(bg)

        x = range(len(labels))
        w = 0.35
        ax.bar([i - w/2 for i in x], recs,  width=w, color="#1D9E75", label="Receita")
        ax.bar([i + w/2 for i in x], desps, width=w, color="#E24B4A", label="Despesa")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=7, color=self.FG2, rotation=30, ha="right")
        ax.tick_params(axis="y", labelsize=7, labelcolor=self.FG2, colors=self.FG2)
        ax.spines[["top","right","left","bottom"]].set_visible(False)
        ax.yaxis.grid(True, color=self.BORDA, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.legend(fontsize=7, frameon=False, labelcolor=self.FG)
        ax.format_coord = lambda x, y: ""
        fig.patch.set_facecolor(bg)
        plt.tight_layout(pad=0.5)

        # Tooltip para barras
        bar_tooltip = [None]
        all_bars = [(b, recs[i], "Receita") for i, b in enumerate(ax.patches[:len(recs)])] +                    [(b, desps[i], "Despesa") for i, b in enumerate(ax.patches[len(recs):])]
        def on_bar_hover(event):
            if event.inaxes != ax:
                if bar_tooltip[0]:
                    bar_tooltip[0].remove()
                    bar_tooltip[0] = None
                    bar_canvas[0].draw_idle()
                return
            for bar, val, tipo in all_bars:
                if bar.contains_point([event.x, event.y]):
                    txt = f"{tipo}\n{fmt(val)}"
                    if bar_tooltip[0]:
                        bar_tooltip[0].remove()
                    bar_tooltip[0] = ax.annotate(
                        txt,
                        xy=(event.xdata, event.ydata),
                        xytext=(10, 10), textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.3", facecolor=self.BORDA,
                                  edgecolor=self.FG2, linewidth=0.5),
                        color=self.FG, fontsize=8,
                    )
                    bar_canvas[0].draw_idle()
                    return
            if bar_tooltip[0]:
                bar_tooltip[0].remove()
                bar_tooltip[0] = None
                bar_canvas[0].draw_idle()

        bar_canvas = [None]
        fig.canvas.mpl_connect("motion_notify_event", on_bar_hover)
        self._embed_chart(fig, f)
        bar_canvas[0] = fig.canvas

    def _render_evolucao_saldo(self, dados):
        f = self._section("EVOLUÇÃO DO SALDO NO MÊS", row=2, col=0, colspan=2)
        mes_sel = self._analise_mes.get()

        # Filtra dados do mês selecionado (ou mês atual se Todos)
        if mes_sel == "Todos":
            t = date.today()
            m_ref, a_ref = t.month, t.year
        else:
            m_ref, a_ref = int(mes_sel.split("/")[0]), int(mes_sel.split("/")[1])

        dados_mes = [d for d in dados
                     if d["Data"].month == m_ref and d["Data"].year == a_ref]

        if not dados_mes:
            tk.Label(f, text="Sem dados para o período.", bg=self.CARD, fg=self.FG2,
                     font=("Segoe UI", 9)).pack(padx=14, pady=20)
            return

        import calendar
        ultimo_dia = calendar.monthrange(a_ref, m_ref)[1]
        dias = list(range(1, ultimo_dia + 1))

        # Agrupa por dia
        por_dia = defaultdict(lambda: {"rec": 0, "desp": 0})
        for d in dados_mes:
            dia = d["Data"].day
            if d["Tipo"] == "Receita":
                por_dia[dia]["rec"] += d["Receita"]
            elif d["Tipo"] != "Despesa Cartão":
                por_dia[dia]["desp"] += d["Despesa"]

        # Acumula dia a dia
        saldos = []
        acum = 0
        hoje = date.today()
        dia_limite = hoje.day if (m_ref == hoje.month and a_ref == hoje.year) else ultimo_dia
        dias_exib = [d for d in dias if d <= dia_limite]

        for dia in dias_exib:
            acum += por_dia[dia]["rec"] - por_dia[dia]["desp"]
            saldos.append(acum)

        if not saldos:
            tk.Label(f, text="Sem dados.", bg=self.CARD, fg=self.FG2,
                     font=("Segoe UI", 9)).pack(padx=14, pady=20)
            return

        bg = self.CARD
        fig, ax = plt.subplots(figsize=(8.4, 2.8), facecolor=bg)
        ax.set_facecolor(bg)

        ax.plot(dias_exib, saldos, color="#378ADD", linewidth=2, zorder=3)
        ax.fill_between(dias_exib, saldos, 0,
                        where=[s >= 0 for s in saldos],
                        color="#1D9E75", alpha=0.15)
        ax.fill_between(dias_exib, saldos, 0,
                        where=[s < 0 for s in saldos],
                        color="#E24B4A", alpha=0.15)
        ax.axhline(0, color=self.BORDA, linewidth=0.8)

        # Pontos nos dias com movimentação
        for dia, saldo in zip(dias_exib, saldos):
            if dia in por_dia:
                cor = "#10b981" if saldo >= 0 else "#f87171"
                ax.scatter(dia, saldo, color=cor, zorder=4, s=25)

        # Xticks: mostra só alguns dias para não poluir
        step = max(1, len(dias_exib) // 10)
        ticks = [dias_exib[i] for i in range(0, len(dias_exib), step)]
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(d) for d in ticks], fontsize=7, color=self.FG2)
        ax.tick_params(axis="y", labelsize=7, labelcolor=self.FG2)
        ax.spines[["top","right","left","bottom"]].set_visible(False)
        ax.yaxis.grid(True, color=self.BORDA, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.set_xlabel("Dia do mês", fontsize=7, color=self.FG2)
        ax.format_coord = lambda x, y: ""
        fig.patch.set_facecolor(bg)
        plt.tight_layout(pad=0.5)

        self._embed_chart(fig, f)

    def _normalizar_nome(self, nome):
        import re
        n = re.sub(r"^\[.*?\]\s*", "", nome).strip()
        n = re.sub(r"\s+", " ", n).strip()
        return n.lower()
    def _render_top5(self, dados_mes):
        f = self._section("TOP 5 MAIORES GASTOS", row=3, col=0, colspan=2)
        despesas_raw = [d for d in dados_mes if d["Tipo"] != "Receita"]

        # Agrupa por nome normalizado
        agrupado = defaultdict(lambda: {"valor": 0, "desc": "", "cat": ""})
        for d in despesas_raw:
            chave = self._normalizar_nome(d["Descrição"])
            agrupado[chave]["valor"] += d["Despesa"]
            if not agrupado[chave]["desc"]:
                agrupado[chave]["desc"] = d["Descrição"]
                agrupado[chave]["cat"]  = d["Categoria"]

        despesas = sorted(agrupado.values(), key=lambda x: x["valor"], reverse=True)[:5]
        # Converte para formato compatível
        despesas = [{"Descrição": d["desc"], "Despesa": d["valor"],
                     "Categoria": d["cat"]} for d in despesas]

        if not despesas:
            tk.Label(f, text="Sem despesas no período.", bg=self.CARD, fg=self.FG2,
                     font=("Segoe UI", 9)).pack(padx=14, pady=12)
            return

        inner = tk.Frame(f, bg=self.CARD)
        inner.pack(fill="x", padx=14, pady=(0, 12))
        inner.columnconfigure(1, weight=1)

        total = sum(d["Despesa"] for d in despesas)

        for i, d in enumerate(despesas):
            row_f = tk.Frame(inner, bg=self.CARD)
            row_f.pack(fill="x", pady=3)

            # Rank
            tk.Label(row_f, text=f"#{i+1}", bg=self.CARD, fg=self.FG2,
                     font=("Segoe UI", 8), width=3).pack(side="left")

            # Info
            info = tk.Frame(row_f, bg=self.CARD)
            info.pack(side="left", fill="x", expand=True, padx=(6, 0))
            tk.Label(info, text=d.get("Descrição", d.get("desc", "")), bg=self.CARD, fg=self.FG,
                     font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x")

            # Barra proporcional
            pct = d["Despesa"] / total if total > 0 else 0
            barra_bg = tk.Frame(info, bg=self.BORDA, height=3)
            barra_bg.pack(fill="x", pady=(2, 0))
            barra_bg.pack_propagate(False)
            cor = CORES_CAT[i]
            def _draw(e, b=barra_bg, p=pct, c=cor):
                for w in b.winfo_children(): w.destroy()
                ws = max(1, int(p * b.winfo_width()))
                tk.Frame(b, bg=c, height=3).place(x=0, y=0, width=ws, height=3)
            barra_bg.bind("<Configure>", _draw)

            # Valor + categoria
            right = tk.Frame(row_f, bg=self.CARD)
            right.pack(side="right", padx=(8, 0))
            tk.Label(right, text=fmt(d["Despesa"]), bg=self.CARD, fg=CORES_CAT[i],
                     font=("Segoe UI", 9, "bold")).pack(anchor="e")
            tk.Label(right, text=d["Categoria"].replace("(D) ", ""),
                     bg=self.CARD, fg=self.FG2,
                     font=("Segoe UI", 8)).pack(anchor="e")