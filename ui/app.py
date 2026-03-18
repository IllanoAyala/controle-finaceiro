import tkinter as tk
from tkinter import ttk
import webbrowser
import os

from constants import TEMAS
from database import init_db
from ui.aba_lancamentos import AbaLancamentos
from ui.aba_cartoes import AbaCartoes
from ui.aba_analises import AbaAnalises
from ui.widgets import entry_widget, btn


class App(tk.Tk, AbaLancamentos, AbaCartoes, AbaAnalises):

    def __init__(self):
        super().__init__()
        self.title("Controle Financeiro")
        self.geometry("980x700")
        self.configure(bg=self.BG if hasattr(self, "BG") else "#0a0a0a")
        self.resizable(True, True)
        try:
            import sys
            _root = sys.path[0]  # raiz definida pelo main.py
            _ico = os.path.join(_root, "icone.ico")
            if os.path.exists(_ico):
                self.iconbitmap(default=_ico)
        except:
            pass
        init_db()
        self.style = ttk.Style(self)
        self._tema_atual = "dark"
        self._configurar_estilo(self._tema_atual)
        self._criar_interface()

    def _configurar_estilo(self, tema=None):
        if tema is None: tema = getattr(self, "_tema_atual", "dark")
        self.style.theme_use("clam")
        _TEMAS = {
            "dark":  {"BG": "#0a0a0a", "CARD": "#141414", "BORDA": "#2e2e2e",
                      "FG": "#ffffff", "FG2": "#888888", "ENTRY_BG": "#1c1c1c"},
            "light": {"BG": "#f5f5f5", "CARD": "#ffffff", "BORDA": "#e0e0e0",
                      "FG": "#111111", "FG2": "#666666", "ENTRY_BG": "#eeeeee"},
        }
        t = _TEMAS[tema]
        self.BG       = t["BG"]
        self.CARD     = t["CARD"]
        self.BORDA    = t["BORDA"]
        self.FG       = t["FG"]
        self.FG2      = t["FG2"]
        self.ENTRY_BG = t["ENTRY_BG"]
        bg, card, borda, fg, fg2, entry_bg = (
            self.BG, self.CARD, self.BORDA, self.FG, self.FG2, self.ENTRY_BG)
        self.configure(bg=bg)
        self.style.configure(".", background=bg, foreground=fg, font=("Segoe UI", 10))
        self.style.configure("TFrame", background=bg)
        self.style.configure("Card.TFrame", background=card)
        self.style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", background=bg, foreground=fg, font=("Segoe UI", 18, "bold"))
        self.style.configure("Card.TLabel", background=card, foreground=fg, font=("Segoe UI", 10))
        self.style.configure("CardTitle.TLabel", background=card, foreground=fg2, font=("Segoe UI", 9))
        self.style.configure("CardVal.TLabel", background=card, foreground=fg, font=("Segoe UI", 16, "bold"))
        self.style.configure("Receita.TLabel", background=card, foreground=fg, font=("Segoe UI", 16, "bold"))
        self.style.configure("Despesa.TLabel", background=card, foreground=fg2, font=("Segoe UI", 16, "bold"))
        self.style.configure("TCombobox", fieldbackground=entry_bg, background=entry_bg,
                             foreground=fg, selectbackground=borda, font=("Segoe UI", 10))
        self.style.map("TCombobox", fieldbackground=[("readonly", entry_bg)],
                       foreground=[("readonly", fg)])
        tree_bg = "#111111" if tema == "dark" else "#f9f9f9"
        self.style.configure("Treeview", background=tree_bg, foreground=fg,
                             fieldbackground=tree_bg, font=("Segoe UI", 9), rowheight=26)
        self.style.configure("Treeview.Heading", background=card, foreground=fg2,
                             font=("Segoe UI", 9, "bold"), relief="flat")
        self.style.map("Treeview", background=[("selected", borda)])
        self.style.configure("TSeparator", background=borda)

    def _entry_widget(self, parent, row=None, col=None, width=None):
        kw = dict(bg=self.ENTRY_BG, fg=self.FG, insertbackground=self.FG,
                  font=("Segoe UI", 10), relief="flat", bd=4)
        if width:
            kw["width"] = width
        e = tk.Entry(parent, **kw)
        if row is not None:
            e.grid(row=row, column=col, sticky="ew", pady=4, ipady=4)
        return e

    def _btn(self, parent, text, cmd, bg=None, fg=None):
        if bg is None: bg = self.FG
        if fg is None: fg = self.BG
        return tk.Button(parent, text=text, command=cmd,
                        bg=bg, fg=fg, font=("Segoe UI", 10, "bold"),
                        relief="flat", cursor="hand2", padx=12, pady=6,
                        activebackground=bg, activeforeground=fg)


    def _toggle_tema(self):
        novo_tema = 'light' if self._tema_atual == 'dark' else 'dark'
        cor_bg = "#f5f5f5" if novo_tema == "light" else "#0a0a0a"
        cor_fg = "#111111" if novo_tema == "light" else "#ffffff"

        # Tela de loading
        for w in self.winfo_children():
            w.destroy()
        self.configure(bg=cor_bg)
        loading_frame = tk.Frame(self, bg=cor_bg)
        loading_frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(loading_frame, text="Alterando tema...", bg=cor_bg, fg=cor_fg,
                 font=("Segoe UI", 11)).pack(pady=(0, 16))

        # Canvas do spinner
        spin_canvas = tk.Canvas(loading_frame, width=40, height=40,
                                bg=cor_bg, highlightthickness=0)
        spin_canvas.pack()

        angle = [0]
        arc_id = spin_canvas.create_arc(4, 4, 36, 36, start=90, extent=270,
                                         outline=cor_fg, width=3, style="arc")

        def _spin():
            try:
                if not hasattr(self, "_spinning"):
                    return
                angle[0] = (angle[0] + 12) % 360
                spin_canvas.itemconfig(arc_id, start=angle[0])
                self.after(30, _spin)
            except Exception:
                pass

        self._spinning = True
        _spin()

        def _aplicar():
            self._spinning = False
            self._tema_atual = novo_tema
            self._configurar_estilo(self._tema_atual)
            for attr in ['lbl_cartao_lanc', 'combo_cartao_lanc', 'tree_cartoes',
                         'tree_faturas', 'frame_cards_cartoes', 'fat_cards_frame',
                         'card_fatura_total', 'card_proximas', 'card_limite_total', 'card_terceiros',
                         'card_disponivel', 'frame_btns_cartoes', '_fat_canvas',
                         '_cartao_idx_sel', '_btn_tema', '_analise_mes', '_analises_frame', '_analises_win', '_tab_lines']:
                if hasattr(self, attr):
                    delattr(self, attr)
            for w in self.winfo_children():
                w.destroy()
            self._criar_interface()

        self.after(600, _aplicar)

    def _criar_interface(self):
        header = ttk.Frame(self, style="TFrame", padding=(24, 16, 24, 8))
        header.pack(fill="x")
        ttk.Label(header, text="Controle Financeiro", style="Title.TLabel").pack(side="left")

        tema_label = "☀" if self._tema_atual == "dark" else "⏾"
        self._btn_tema = tk.Button(header, text=tema_label, command=self._toggle_tema,
                                   bg=self.BORDA, fg=self.FG2,
                                   font=("Segoe UI", 9), relief="flat",
                                   cursor="hand2", padx=10, pady=4,
                                   activebackground=self.BORDA, activeforeground=self.FG)
        self._btn_tema.pack(side="right")
        # Tab bar com linha inferior no ativo
        tab_bar_outer = tk.Frame(self, bg=self.BG)
        tab_bar_outer.pack(fill="x", padx=24, pady=(0, 4))
        tab_bar = tk.Frame(tab_bar_outer, bg=self.BG)
        tab_bar.pack(fill="x")
        tab_bar.columnconfigure(0, weight=1)
        tab_bar.columnconfigure(1, weight=1)
        tab_bar.columnconfigure(2, weight=1)
        # Linha separadora na base
        tk.Frame(tab_bar_outer, bg=self.BORDA, height=1).pack(fill="x")
        self.aba_atual = tk.IntVar(value=0)
        self._tab_btns = []
        self._abas = []
        container = tk.Frame(self, bg=self.BG)
        container.pack(fill="both", expand=True, padx=24, pady=(0, 0))

        # Footer — linha superior, centralizado
        import webbrowser

        footer = tk.Frame(self, bg=self.CARD)
        footer.pack(fill="x", side="bottom")
        tk.Frame(footer, bg=self.BORDA, height=1).pack(fill="x")

        inner = tk.Frame(footer, bg=self.CARD)
        inner.pack(pady=8)

        tk.Label(inner, text="desenvolvido por", bg=self.CARD,
                 fg=self.FG2, font=("Segoe UI", 9)).pack(side="left")

        nome = tk.Label(inner, text="Illano Ayala", bg=self.CARD,
                        fg=self.FG, font=("Segoe UI", 9, "bold"), cursor="hand2")
        nome.pack(side="left", padx=(3, 0))
        nome.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/IllanoAyala"))
        nome.bind("<Enter>",    lambda e: nome.config(fg=self.FG2))
        nome.bind("<Leave>",    lambda e: nome.config(fg=self.FG))
        aba1 = ttk.Frame(container, style="TFrame", padding=(0, 12, 0, 0))
        aba2 = ttk.Frame(container, style="TFrame", padding=(0, 12, 0, 0))
        aba3 = ttk.Frame(container, style="TFrame", padding=(0, 12, 0, 0))
        self._abas = [aba1, aba2, aba3]

        def trocar_aba(idx):
            self.aba_atual.set(idx)
            for i, frame in enumerate(self._abas):
                if i == idx:
                    frame.place(relx=0, rely=0, relwidth=1, relheight=1)
                else:
                    frame.place_forget()
            for i, b in enumerate(self._tab_btns):
                if i == idx:
                    b.config(bg=self.BG, fg=self.FG,
                             font=("Segoe UI", 10, "bold"),
                             relief="flat", bd=0)
                    # Linha inferior ativa
                    self._tab_lines[i].config(bg=self.FG)
                else:
                    b.config(bg=self.BG, fg=self.FG2,
                             font=("Segoe UI", 10),
                             relief="flat", bd=0)
                    self._tab_lines[i].config(bg=self.BG)

        self._tab_lines = []
        for i, label in enumerate(["  📋  Lançamentos  ", "  💳  Cartões de Crédito  ", "  📊  Análises  "]):
            cell = tk.Frame(tab_bar, bg=self.BG)
            cell.grid(row=0, column=i, sticky="ew")
            b = tk.Button(cell, text=label, font=("Segoe UI", 10),
                          relief="flat", bd=0, highlightthickness=0,
                          cursor="hand2", pady=10,
                          bg=self.BG, fg=self.FG2,
                          activebackground=self.BG, activeforeground=self.FG,
                          command=lambda i=i: trocar_aba(i))
            b.pack(fill="x")
            line = tk.Frame(cell, bg=self.BG, height=2)
            line.pack(fill="x")
            self._tab_btns.append(b)
            self._tab_lines.append(line)

        container.update_idletasks()
        for frame in self._abas:
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._construir_aba_lancamentos(aba1)
        self._construir_aba_cartoes(aba2)
        self._construir_aba_analises(aba3)
        trocar_aba(0)

    # ══════════════════════════════════════════════════════════════════════════
    # ABA LANÇAMENTOS
    # ══════════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    app = App()
    app.mainloop()