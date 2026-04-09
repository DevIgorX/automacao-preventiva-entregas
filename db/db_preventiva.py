import sqlite3
import pandas as pd
import os

# Caminho para o banco de dados na raiz do projeto
caminho_script = os.path.abspath(__file__)
pasta_db = os.path.dirname(caminho_script)
diretorio_raiz = os.path.dirname(pasta_db)

diretorio_db = os.path.join(diretorio_raiz,'dados_preventiva.db')
DB_PATH = diretorio_db

def salvar_no_banco(df, nome_tabela="analise_resultado"):
    """Salva o DataFrame no SQLite, sobrescrevendo a tabela anterior."""
    conn = sqlite3.connect(DB_PATH)
    # index=False evita criar uma coluna extra para o índice do Pandas
    df.to_sql(nome_tabela, conn, if_exists='append', index=False)
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


def buscar_pedido_historico(pedido_id):
    conn = sqlite3.connect(DB_PATH)
    # Busca o histórico na tabela de resultados já processados
    query = "SELECT * FROM analise_resultado WHERE `Preventiva_Pedido 1P/Full` = ?"
    df = pd.read_sql(query, conn, params=(pedido_id,))
    conn.close()
    return df.to_dict(orient='records')


def buscar_ultimo_raw(nome_tabela):
    """Procura os dados mais recentes de uma tabela 'raw'."""
    conn = sqlite3.connect(DB_PATH)
    try:
        # Procuramos os dados da tabela. 
        # Idealmente, cada tabela raw deve ter uma coluna 'data_processamento'
        query = f"SELECT * FROM {nome_tabela}"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        conn.close()
        return None