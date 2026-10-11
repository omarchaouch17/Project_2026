"""db.py - one database layer for two worlds:

* without DATABASE_URL -> SQLite file patients.db (local development and tests)
* with    DATABASE_URL -> PostgreSQL (e.g. Neon). Data survives restarts and redeploys
                          of the Render server.

All SQL is written with ? placeholders; for PostgreSQL they are converted to %s automatically.
"""
import os
import sqlite3

SQLITE_FILE = "patients.db"


def postgres_enabled():
    return bool(os.environ.get("DATABASE_URL"))


def _pg_url():
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgres://"):          # older spelling
        url = "postgresql://" + url[len("postgres://"):]
    return url


def connect():
    if postgres_enabled():
        import psycopg                           # only needed when PostgreSQL is used
        return psycopg.connect(_pg_url(), connect_timeout=10)
    return sqlite3.connect(SQLITE_FILE)


def _sql(sql):
    return sql.replace("?", "%s") if postgres_enabled() else sql


def id_column():
    """Column type for the automatic ID."""
    return "SERIAL PRIMARY KEY" if postgres_enabled() else "INTEGER PRIMARY KEY"


def query(sql, params=()):
    """SELECT -> list of tuples."""
    connection = connect()
    try:
        return connection.execute(_sql(sql), params).fetchall()
    finally:
        connection.close()


def execute(sql, params=()):
    """INSERT/UPDATE/DELETE/CREATE without a return value."""
    execute_many([(sql, params)])


def execute_many(statements):
    """Several statements in ONE transaction (all or nothing)."""
    connection = connect()
    try:
        if not postgres_enabled():
            connection.execute("BEGIN")      # SQLite would otherwise run DDL statements outside a transaction
        for sql, params in statements:
            connection.execute(_sql(sql), params)
        connection.commit()
    finally:
        connection.close()


def insert(sql, params=()):
    """INSERT and return the new ID (the table needs an id column)."""
    connection = connect()
    try:
        if postgres_enabled():
            new_id = connection.execute(_sql(sql) + " RETURNING id", params).fetchone()[0]
        else:
            new_id = connection.execute(sql, params).lastrowid
        connection.commit()
        return new_id
    finally:
        connection.close()


def table_exists(table):
    if postgres_enabled():
        rows = query("SELECT 1 FROM information_schema.tables WHERE table_name = ? AND table_schema = current_schema()",
                     (table,))
    else:
        rows = query("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,))
    return bool(rows)


def columns(table):
    """Names of the existing columns (for simple migrations)."""
    if postgres_enabled():
        rows = query("SELECT column_name FROM information_schema.columns "
                     "WHERE table_name = ? AND table_schema = current_schema()", (table,))
        return [row[0] for row in rows]
    connection = connect()
    try:
        return [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
    finally:
        connection.close()
