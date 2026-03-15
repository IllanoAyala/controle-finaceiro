import os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "controle_financeiro.db")

CATEGORIAS_DESPESA = [
    "(D) Alimentação", "(D) Ajuda/Presente", "(D) Besteira", "(D) Compras",
    "(D) Moradia", "(D) Profissionalização", "(D) Saúde", "(D) Transporte",
    "(D) Cartão de Crédito",
]
CATEGORIAS_RECEITA = ["(R) Ajuda/Presente", "(R) Bolsa", "(R) Dinheiro Extra"]

MESES = {
    1: "JAN", 2: "FEV", 3: "MAR", 4: "ABR",
    5: "MAI", 6: "JUN", 7: "JUL", 8: "AGO",
    9: "SET", 10: "OUT", 11: "NOV", 12: "DEZ",
}

TEMAS = {
    "dark": {
        "BG": "#0a0a0a", "CARD": "#141414", "BORDA": "#2e2e2e",
        "FG": "#ffffff", "FG2": "#888888", "ENTRY_BG": "#1c1c1c",
    },
    "light": {
        "BG": "#f5f5f5", "CARD": "#ffffff", "BORDA": "#e0e0e0",
        "FG": "#111111", "FG2": "#666666", "ENTRY_BG": "#eeeeee",
    },
}

CORES_GRAFICOS = ["#E24B4A", "#1D9E75", "#378ADD", "#BA7517", "#D4537E", "#7F77DD"]
