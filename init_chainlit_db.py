"""
Script de inicialización de tablas SQLite para Chainlit SQLAlchemyDataLayer.
Crea las tablas users, threads, steps, elements y feedbacks con todas las columnas
requeridas por Chainlit (incluyendo objectKey y page en elements, y defaultOpen, autoCollapse, etc. en steps).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "chainlit_historial.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    identifier TEXT NOT NULL UNIQUE,
    createdAt TEXT NOT NULL,
    metadata TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    createdAt TEXT,
    name TEXT,
    userId TEXT,
    userIdentifier TEXT,
    tags TEXT,
    metadata TEXT,
    FOREIGN KEY (userId) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS steps (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    threadId TEXT NOT NULL,
    parentId TEXT,
    disableFeedback BOOLEAN,
    streaming BOOLEAN,
    waitForAnswer BOOLEAN,
    isError BOOLEAN,
    metadata TEXT,
    tags TEXT,
    input TEXT,
    output TEXT,
    createdAt TEXT,
    start TEXT,
    "end" TEXT,
    generation TEXT,
    showInput TEXT,
    language TEXT,
    autoScroll BOOLEAN,
    command TEXT,
    modes TEXT,
    defaultOpen BOOLEAN,
    autoCollapse BOOLEAN,
    icon TEXT,
    feedback TEXT,
    FOREIGN KEY (threadId) REFERENCES threads(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS elements (
    id TEXT PRIMARY KEY,
    threadId TEXT,
    type TEXT,
    url TEXT,
    objectKey TEXT,
    chainlitKey TEXT,
    name TEXT NOT NULL,
    display TEXT,
    size TEXT,
    language TEXT,
    page INTEGER,
    autoPlay BOOLEAN,
    playerConfig TEXT,
    forId TEXT,
    mime TEXT,
    props TEXT,
    FOREIGN KEY (threadId) REFERENCES threads(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedbacks (
    id TEXT PRIMARY KEY,
    forId TEXT NOT NULL,
    threadId TEXT NOT NULL,
    value INTEGER NOT NULL,
    comment TEXT,
    FOREIGN KEY (threadId) REFERENCES threads(id) ON DELETE CASCADE
);
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(SCHEMA_SQL)
    
    # Migrar columnas existentes si la base de datos fue creada con un esquema previo
    step_columns = {
        'command': 'TEXT',
        'modes': 'TEXT',
        'defaultOpen': 'BOOLEAN',
        'autoCollapse': 'BOOLEAN',
        'icon': 'TEXT',
        'feedback': 'TEXT'
    }
    cursor.execute('PRAGMA table_info(steps)')
    existing_step_cols = {row[1] for row in cursor.fetchall()}
    for col, col_type in step_columns.items():
        if col not in existing_step_cols:
            cursor.execute(f'ALTER TABLE steps ADD COLUMN {col} {col_type}')

    elem_columns = {
        'objectKey': 'TEXT',
        'page': 'INTEGER',
        'playerConfig': 'TEXT',
        'props': 'TEXT',
        'mime': 'TEXT',
        'autoPlay': 'BOOLEAN',
        'forId': 'TEXT'
    }
    cursor.execute('PRAGMA table_info(elements)')
    existing_elem_cols = {row[1] for row in cursor.fetchall()}
    for col, col_type in elem_columns.items():
        if col not in existing_elem_cols:
            cursor.execute(f'ALTER TABLE elements ADD COLUMN {col} {col_type}')

    conn.commit()
    conn.close()
    print("Base de datos SQLite de Chainlit inicializada/actualizada correctamente.")

if __name__ == "__main__":
    init_db()
