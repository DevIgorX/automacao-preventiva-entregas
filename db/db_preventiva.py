import sqlite3
import pandas as pd
import os

# Caminho para o banco de dados na raiz do projeto
caminho_script = os.path.abspath(__file__)
pasta_db = os.path.dirname(caminho_script)
diretorio_raiz = os.path.dirname(pasta_db)
pasta_app = os.path.join(diretorio_raiz,'app')
diretorio_db = os.path.join(pasta_app,'dados_preventiva.db')
DB_PATH = diretorio_db

def salvar_no_banco(df, nome_tabela="analise_resultado"):
    """Salva o DataFrame no SQLite, sobrescrevendo a tabela anterior."""
    conn = sqlite3.connect(DB_PATH)
    # index=False evita criar uma coluna extra para o índice do Pandas
    df.to_sql(nome_tabela, conn, if_exists='replace', index=False)
    conn.close()

def buscar_dados_paginados(pagina, itens_por_pagina=10):
    """Busca apenas as linhas necessárias para a página atual."""
    conn = sqlite3.connect(DB_PATH)
    offset = (pagina - 1) * itens_por_pagina
    
    # Busca os dados limitados
    query = f"SELECT * FROM analise_resultado LIMIT {itens_por_pagina} OFFSET {offset}"
    df = pd.read_sql(query, conn)
    
    # Busca o total de registros para o cálculo de páginas no HTML
    total_registros = conn.execute("SELECT COUNT(*) FROM analise_resultado").fetchone()[0]
    conn.close()
    
    return df.to_dict(orient='records'), total_registros