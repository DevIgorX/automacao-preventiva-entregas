import sqlite3


conn = sqlite3.connect('automacao.db')
cursor = conn.cursor()

tabela_usuario = """
CREATE TABLE IF NOT EXISTS usuarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    senha TEXT
)
"""

cursor.execute(tabela_usuario)

cursor.execute("INSERT INTO usuarios(nome, senha) values ('Tauam Igor', '1234')")

#consultando dados

conn.commit()
conn.close()