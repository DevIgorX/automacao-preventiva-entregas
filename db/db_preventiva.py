import sqlite3
import pandas as pd
import os

# Caminho para o banco de dados na raiz do projeto
caminho_script = os.path.abspath(__file__)
pasta_db = os.path.dirname(caminho_script)
diretorio_raiz = os.path.dirname(pasta_db)

diretorio_db = os.path.join(diretorio_raiz,'dados_preventiva.db')
DB_PATH = diretorio_db

def salvar_dados_base(df, nome_tabela):
    """Salva os dados de suporte (Carreta, Mobile, etc) substituindo os antigos."""
    conn = sqlite3.connect(DB_PATH)
    # 'replace' garante que a tabela seja recriada com os novos dados
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
    query =  """
        SELECT 
            c.*, 
            m.Mobile_Tipo, m.Mobile_Entregador,
            e."Esl_Última Ocorrência/Observações", e."Esl_Pessoa/Nome",
            bp.Bipe_Prod_Status_Deposito,
            bn.Bipe_Notas_Ocorrencia
        FROM raw_carreta c
        LEFT JOIN raw_mobile m ON c.Carreta_Pedido = m.Mobile_Pedido
        LEFT JOIN raw_esl e ON c.Carreta_Chave = e."Esl_Nota Fiscal/Chave Nf-E"
        LEFT JOIN raw_bipe_produtos bp ON c.Carreta_Pedido = bp.Bipe_Prod_Pedido
        LEFT JOIN raw_bipe_notas bn ON c."Carreta_Nf`S" = bn.Bipe_Notas_Nf
        WHERE c.Carreta_Pedido = ?
        """
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

#mudança aqui
def consulta_join_pedidos(lista_pedidos):
    """Realiza o cruzamento de dados via SQL para uma lista de pedidos."""
    if not lista_pedidos:
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    
    # Cria os placeholders (?, ?, ?) para evitar SQL Injection
    placeholders = ', '.join(['?'] * len(lista_pedidos))
    
    # Query que faz o cruzamento (JOIN) das tabelas base
    query = f"""
    SELECT 
        c.*, 
        m.Mobile_Tipo, m.Mobile_Entregador,
        e."Esl_Última Ocorrência/Observações", e."Esl_Pessoa/Nome",
        bp.Bipe_Prod_Status_Deposito,
        bn.Bipe_Notas_Ocorrencia
    FROM raw_carreta c
    LEFT JOIN raw_mobile m ON c.Carreta_Pedido = m.Mobile_Pedido
    LEFT JOIN raw_esl e ON c.Carreta_Chave = e."Esl_Nota Fiscal/Chave Nf-E"
    LEFT JOIN raw_bipe_produtos bp ON c.Carreta_Pedido = bp.Bipe_Prod_Pedido
    LEFT JOIN raw_bipe_notas bn ON c."Carreta_Nf`S" = bn.Bipe_Notas_Nf
    WHERE c.Carreta_Pedido IN ({placeholders})
    """
    
    try:
        df = pd.read_sql(query, conn, params=lista_pedidos)
    except Exception as e:
        print(f"Erro na consulta SQL: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
        
    return df