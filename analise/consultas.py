# Crie este arquivo em: analise/consultas.py

import pandas as pd
from app.utils import formatar_colunas 
from db.db_preventiva import consulta_join_pedidos

def extrair_pedidos_e_consultar(arquivo):
    """
    Lê a planilha principal direto da memória, descobre qual é a coluna 
    de pedidos e faz a consulta no banco de dados.
    """
    # 1. Lê o Excel e formata as colunas
    df_pedidos = pd.read_excel(arquivo)
    df_pedidos = formatar_colunas(df_pedidos)
    
    # 2. Descobre qual coluna tem os IDs dos pedidos
    coluna_id = None
    if 'Pedido 1P/Full' in df_pedidos.columns:
        coluna_id = 'Pedido 1P/Full'
    else:
        # Se for uma planilha genérica sem o nome padrão, pega a primeira coluna
        coluna_id = df_pedidos.columns[0] 

    # 3. Transforma a coluna inteira em uma lista do Python
    lista_ids = df_pedidos[coluna_id].astype(str).tolist()

    # 4. Vai no banco de dados e cruza as informações
    df_resultado = consulta_join_pedidos(lista_ids)
    
    # (Opcional) Salva um backup físico da última consulta, caso precise baixar
    # df_resultado.to_excel("dados_preventiva/Ultima_Consulta_Lote.xlsx", index=False)

    # 5. Converte para dicionário (que é o formato que seu HTML entende)
    return df_resultado.to_dict(orient='records')