import sqlite3
from typing import List, Tuple, Dict, Optional

DB_NOME = "militares.db"

# =========================
# Conexão
# =========================
def conectar() -> sqlite3.Connection:
    return sqlite3.connect(DB_NOME)

# =========================
# Tabela MILITARES
# =========================
def criar_tabela_militares():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS militares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            posto TEXT NOT NULL,
            nome TEXT NOT NULL,
            nome_guerra TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            prec_cp TEXT UNIQUE NOT NULL,
            idt TEXT UNIQUE NOT NULL,
            banco TEXT,
            agencia TEXT,
            conta TEXT,
            foto TEXT,
            ano TEXT,
            data_nascimento TEXT,
            data_praca TEXT,
            endereco TEXT,
            cep TEXT,
            recebe_pre_escolar TEXT,
            valor_pre_escolar TEXT,
            recebe_aux_transporte TEXT,
            valor_aux_transporte TEXT,
            pnr TEXT
        )
    """)
    con.commit()
    con.close()

def _fmt2(v) -> str:
    try:
        return f"{float(v):.2f}"
    except Exception:
        return "0.00"

# -------- CRUD militares --------
def inserir_militar(dados: Tuple):
    """
    dados: (posto, nome, nome_guerra, cpf, prec_cp, idt, banco, agencia, conta, foto,
            ano, data_nascimento, data_praca, endereco, cep,
            recebe_pre_escolar, valor_pre_escolar, recebe_aux_transporte, valor_aux_transporte, pnr)
    """
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO militares (
            posto, nome, nome_guerra, cpf, prec_cp, idt, banco, agencia, conta, foto,
            ano, data_nascimento, data_praca, endereco, cep,
            recebe_pre_escolar, valor_pre_escolar, recebe_aux_transporte, valor_aux_transporte, pnr
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, dados)
    con.commit()
    con.close()

def buscar_todos() -> List[Tuple]:
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT id, posto, nome, nome_guerra, cpf, prec_cp, idt, banco, agencia, conta, foto,
               ano, data_nascimento, data_praca, endereco, cep,
               recebe_pre_escolar, valor_pre_escolar, recebe_aux_transporte, valor_aux_transporte, pnr
        FROM militares
    """)
    rows = cur.fetchall()
    con.close()
    return rows

def buscar_por_id(id_militar: int) -> Optional[Tuple]:
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT id, posto, nome, nome_guerra, cpf, prec_cp, idt, banco, agencia, conta, foto,
               ano, data_nascimento, data_praca, endereco, cep,
               recebe_pre_escolar, valor_pre_escolar, recebe_aux_transporte, valor_aux_transporte, pnr
        FROM militares
        WHERE id = ?
    """, (id_militar,))
    row = cur.fetchone()
    con.close()
    return row

def atualizar_militar(id_militar: int, dados: Tuple):
    """
    dados: (posto, nome, nome_guerra, cpf, prec_cp, idt, banco, agencia, conta, foto,
            ano, data_nascimento, data_praca, endereco, cep,
            recebe_pre_escolar, valor_pre_escolar, recebe_aux_transporte, valor_aux_transporte, pnr)
    """
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        UPDATE militares SET
            posto=?, nome=?, nome_guerra=?, cpf=?, prec_cp=?, idt=?, banco=?, agencia=?, conta=?, foto=?,
            ano=?, data_nascimento=?, data_praca=?, endereco=?, cep=?,
            recebe_pre_escolar=?, valor_pre_escolar=?, recebe_aux_transporte=?, valor_aux_transporte=?, pnr=?
        WHERE id=?
    """, dados + (id_militar,))
    con.commit()
    con.close()

def excluir_militar(id_militar: int):
    con = conectar()
    cur = con.cursor()
    cur.execute("DELETE FROM militares WHERE id=?", (id_militar,))
    con.commit()
    con.close()

def atualizar_aux_transporte(militar_id: int, total_mensal: float, recebe: str = "Sim") -> bool:
    """
    Atualiza valor_aux_transporte (total mensal de 22 dias) e marca recebe_aux_transporte.
    """
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        UPDATE militares
           SET valor_aux_transporte = ?, recebe_aux_transporte = ?
         WHERE id = ?
    """, (_fmt2(total_mensal), recebe, militar_id))
    con.commit()
    ok = cur.rowcount > 0
    con.close()
    return ok

# =========================
# Catálogos: POSTOS e BANCOS
# =========================
def criar_tabela_catalogos():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS postos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bancos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        )
    """)
    con.commit()
    con.close()

def inserir_posto(nome: str) -> bool:
    """
    Insere um posto novo. Retorna True se inseriu, False se já existia.
    Também garante soldo 0.00 na tabela soldos_por_posto.
    """
    nome = (nome or "").strip()
    if not nome:
        return False
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO postos (nome) VALUES (?)", (nome,))
        con.commit()
        inserted = True
    except sqlite3.IntegrityError:
        inserted = False
    finally:
        con.close()

    if inserted:
        try:
            atualizar_soldo_posto(nome, 0.0)
        except Exception:
            pass
    return inserted

def inserir_banco(nome: str) -> bool:
    """
    Insere um banco novo. Retorna True se inseriu, False se já existia.
    """
    nome = (nome or "").strip()
    if not nome:
        return False
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO bancos (nome) VALUES (?)", (nome,))
        con.commit()
        inserted = True
    except sqlite3.IntegrityError:
        inserted = False
    finally:
        con.close()
    return inserted

def listar_postos() -> List[str]:
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT nome FROM postos ORDER BY id ASC")
    rows = [r[0] for r in cur.fetchall()]
    con.close()
    return rows

def listar_bancos() -> List[str]:
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT nome FROM bancos ORDER BY id ASC")
    rows = [r[0] for r in cur.fetchall()]
    con.close()
    return rows

def garantir_catalogos(postos_default: List[str] = None, bancos_default: List[str] = None):
    """
    Garante que as tabelas existam e insere defaults mantendo a ordem.
    """
    criar_tabela_catalogos()
    con = conectar()
    cur = con.cursor()

    if postos_default:
        for p in postos_default:
            try:
                cur.execute("INSERT OR IGNORE INTO postos (nome) VALUES (?)", (p,))
            except Exception:
                pass

    if bancos_default:
        for b in bancos_default:
            try:
                cur.execute("INSERT OR IGNORE INTO bancos (nome) VALUES (?)", (b,))
            except Exception:
                pass

    con.commit()
    con.close()

# =========================
# SOLDOS POR POSTO
# =========================
def criar_tabela_soldos_por_posto():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS soldos_por_posto (
            posto TEXT PRIMARY KEY,
            soldo REAL NOT NULL DEFAULT 0
        )
    """)
    con.commit()
    con.close()

def obter_soldo_por_posto(posto: str) -> float:
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT soldo FROM soldos_por_posto WHERE posto = ?", (posto,))
    row = cur.fetchone()
    con.close()
    return float(row[0]) if row and row[0] is not None else 0.0

def obter_soldos_dict() -> Dict[str, float]:
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT posto, soldo FROM soldos_por_posto")
    data = {p: float(s if s is not None else 0.0) for p, s in cur.fetchall()}
    con.close()
    return data

def atualizar_soldo_posto(posto: str, soldo: float) -> bool:
    """
    Upsert do soldo por posto.
    Requer SQLite 3.24+ (disponível nas versões recentes do Python).
    """
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO soldos_por_posto (posto, soldo)
        VALUES (?, ?)
        ON CONFLICT(posto) DO UPDATE SET soldo = excluded.soldo
    """, (posto, float(soldo)))
    con.commit()
    ok = cur.rowcount > 0
    con.close()
    return ok

def garantir_soldos_para_postos(postos_lista: List[str] = None):
    criar_tabela_soldos_por_posto()
    if postos_lista is None:
        try:
            postos_lista = listar_postos()
        except Exception:
            postos_lista = []
    con = conectar()
    cur = con.cursor()
    for p in postos_lista:
        cur.execute("INSERT OR IGNORE INTO soldos_por_posto (posto, soldo) VALUES (?, 0)", (p,))
    con.commit()
    con.close()

# =========================
# INIT ÚNICO
# =========================
def init(postos_default: List[str] = None, bancos_default: List[str] = None):
    """
    Chame no início do app:
        from database.db import init
        init(postos_default=[...], bancos_default=[...])
    """
    criar_tabela_militares()
    criar_tabela_catalogos()
    criar_tabela_soldos_por_posto()

    try:
        garantir_catalogos(postos_default or [
            "Capitão", "1º Tenente", "2º Tenente", "Subtenente",
            "1º Sargento", "2º Sargento", "3º Sargento",
            "Cabo Efetivo Profissional", "Soldado Efetivo Profissional", "Soldado Efetivo Variável"
        ], bancos_default or [
            "001 - Banco do Brasil S.A", "341 - Itaú Unibanco S.A",
            "033 - Banco Santander (Brasil) S.A", "237 - Banco Bradesco S.A",
            "104 - Caixa Econômica Federal"
        ])
    except Exception:
        pass

    # garantir soldos zerados para todos os postos existentes
    try:
        garantir_soldos_para_postos(listar_postos())
    except Exception:
        pass
