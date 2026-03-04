import sqlite3


conn = sqlite3.connect('automacao.db') #conn para se conectar com o banco
cursor = conn.cursor() #cursor para executar as querys no banco

tabela_usuario = """
CREATE TABLE IF NOT EXISTS usuarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT,
    senha TEXT
)
"""

cursor.execute(tabela_usuario)

cursor.execute("INSERT INTO usuarios(nome, email, senha ) values ('Tauam Igor', 'tauamigor@gmail.com','1234')")

#consultando dados

consulta = """ SELECT * FROM usuarios """
resultado = cursor.execute(consulta).fetchall()
print(resultado)


conn.commit() #salva a alteração no banco
conn.close() #fecha a conexão com o banco de dados 