import sqlite3
from datetime import datetime
from constants import DB, MESES


def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS lancamentos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            data      TEXT NOT NULL,
            mes       TEXT NOT NULL,
            descricao TEXT NOT NULL,
            tipo      TEXT NOT NULL,
            categoria TEXT NOT NULL,
            receita   REAL NOT NULL DEFAULT 0,
            despesa   REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS cartoes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT NOT NULL UNIQUE,
            limite     REAL NOT NULL DEFAULT 0,
            fatura     REAL NOT NULL DEFAULT 0,
            vencimento INTEGER NOT NULL DEFAULT 0,
            terceiro   INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS gastos_cartao (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            cartao_id INTEGER NOT NULL REFERENCES cartoes(id) ON DELETE CASCADE,
            descricao TEXT NOT NULL,
            valor     REAL NOT NULL,
            data      TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS faturas_futuras (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            cartao_id INTEGER NOT NULL REFERENCES cartoes(id) ON DELETE CASCADE,
            mes       TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor     REAL NOT NULL
        );
    ''')
    conn.commit()
    conn.close()


# ── Lançamentos ───────────────────────────────────────────────────────────────

def carregar_dados():
    return carregar_dados_com_id()


def carregar_dados_com_id():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, data, mes, descricao, tipo, categoria, receita, despesa "
        "FROM lancamentos ORDER BY data DESC, id DESC"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        try:
            dt = datetime.strptime(r[1], "%Y-%m-%d")
        except Exception:
            continue
        result.append({
            "id": r[0], "Data": dt, "Mês": r[2], "Descrição": r[3],
            "Tipo": r[4], "Categoria": r[5], "Receita": r[6], "Despesa": r[7],
        })
    return result


def adicionar_lancamento(data, descricao, tipo, categoria, valor):
    mes = MESES[data.month]
    conn = get_conn()
    conn.execute(
        "INSERT INTO lancamentos (data, mes, descricao, tipo, categoria, receita, despesa) "
        "VALUES (?,?,?,?,?,?,?)",
        (
            data.strftime("%Y-%m-%d"), mes, descricao, tipo, categoria,
            valor if tipo == "Receita" else 0.0,
            valor if tipo != "Receita" else 0.0,
        ),
    )
    conn.commit()
    conn.close()


def apagar_lancamento_db(lanc_id):
    conn = get_conn()
    conn.execute("DELETE FROM lancamentos WHERE id=?", (lanc_id,))
    conn.commit()
    conn.close()


def editar_lancamento_db(lanc_id, data, descricao, tipo, categoria, valor):
    mes = MESES[data.month]
    conn = get_conn()
    conn.execute(
        "UPDATE lancamentos SET data=?, mes=?, descricao=?, tipo=?, categoria=?, "
        "receita=?, despesa=? WHERE id=?",
        (
            data.strftime("%Y-%m-%d"), mes, descricao, tipo, categoria,
            valor if tipo == "Receita" else 0.0,
            valor if tipo != "Receita" else 0.0,
            lanc_id,
        ),
    )
    conn.commit()
    conn.close()


# ── Cartões ───────────────────────────────────────────────────────────────────

def carregar_cartoes():
    conn = get_conn()
    cartoes_rows = conn.execute(
        "SELECT id, nome, limite, fatura, vencimento, terceiro FROM cartoes"
    ).fetchall()
    result = []
    for cid, nome, limite, fatura, venc, terceiro in cartoes_rows:
        gastos = [
            {"desc": g[0], "valor": g[1], "data": g[2]}
            for g in conn.execute(
                "SELECT descricao, valor, data FROM gastos_cartao WHERE cartao_id=?", (cid,)
            ).fetchall()
        ]
        faturas = [
            {"mes": f[0], "desc": f[1], "valor": f[2]}
            for f in conn.execute(
                "SELECT mes, descricao, valor FROM faturas_futuras WHERE cartao_id=?", (cid,)
            ).fetchall()
        ]
        result.append({
            "id": cid, "nome": nome, "limite": limite, "fatura": fatura,
            "vencimento": venc, "terceiro": bool(terceiro),
            "gastos": gastos, "faturas": faturas,
        })
    conn.close()
    return result


def salvar_cartoes(cartoes):
    conn = get_conn()
    for c in cartoes:
        cid = c.get("id")
        if cid:
            conn.execute(
                "UPDATE cartoes SET nome=?, limite=?, fatura=?, vencimento=?, terceiro=? WHERE id=?",
                (c["nome"], c["limite"], c["fatura"], c["vencimento"],
                 1 if c.get("terceiro") else 0, cid),
            )
            conn.execute("DELETE FROM gastos_cartao WHERE cartao_id=?", (cid,))
            conn.execute("DELETE FROM faturas_futuras WHERE cartao_id=?", (cid,))
        else:
            cur = conn.execute(
                "INSERT INTO cartoes (nome, limite, fatura, vencimento, terceiro) VALUES (?,?,?,?,?)",
                (c["nome"], c["limite"], c["fatura"], c["vencimento"],
                 1 if c.get("terceiro") else 0),
            )
            cid = cur.lastrowid
            c["id"] = cid

        for g in c.get("gastos", []):
            conn.execute(
                "INSERT INTO gastos_cartao (cartao_id, descricao, valor, data) VALUES (?,?,?,?)",
                (cid, g["desc"], g["valor"], g.get("data", "")),
            )
        for f in c.get("faturas", []):
            conn.execute(
                "INSERT INTO faturas_futuras (cartao_id, mes, descricao, valor) VALUES (?,?,?,?)",
                (cid, f["mes"], f.get("desc", ""), f["valor"]),
            )
    conn.commit()
    conn.close()


def adicionar_cartao_db(nome, limite, fatura, vencimento, terceiro):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO cartoes (nome, limite, fatura, vencimento, terceiro) VALUES (?,?,?,?,?)",
        (nome, limite, fatura, vencimento, 1 if terceiro else 0),
    )
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def remover_cartao_db(cartao_id):
    conn = get_conn()
    conn.execute("DELETE FROM cartoes WHERE id=?", (cartao_id,))
    conn.commit()
    conn.close()
