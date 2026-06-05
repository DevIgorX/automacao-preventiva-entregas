
import pandas as pd
# Importa a sua função de limpar as colunas que já existe no utils
from app.utils import formatar_colunas , formatar_coluna_pedidos , formatar_coluna_data
# Importa a nova função do banco de dados que substitui/atualiza a tabela
from db.db_preventiva import salvar_dados_base 

def processar_e_salvar_tabela(arquivo, nome_arquivo):
    """
    Recebe o arquivo do upload, identifica o tipo, usa o Pandas para limpar 
    as colunas com a função utils e salva no banco de dados.
    """
    # O Pandas consegue ler o arquivo direto da memória do Flask!
    

    if 'Bipe_de_notas' in nome_arquivo:
        df = pd.read_excel(arquivo, sheet_name='Plan1')
    else: 
        df = pd.read_excel(arquivo)


    df = formatar_colunas(df)
    
    if 'Carreta' in nome_arquivo:
        df = df.add_prefix('Carreta_')
        df = formatar_coluna_pedidos(df,'Carreta_Pedido')
        df = formatar_coluna_pedidos(df,'Carreta_Nf`S')
        salvar_dados_base(df,'raw_carreta', coluna_chave='Carreta_Pedido')
        return 'Carreta'
        
    elif 'Mobile' in nome_arquivo:
        df = df.add_prefix('Mobile_')
        df = formatar_coluna_pedidos(df, 'Mobile_Pedido')
        salvar_dados_base(df, "raw_mobile", coluna_chave="Mobile_Pedido")
        return "Mobile"
        
    elif 'magazine' in nome_arquivo or 'Esl' in nome_arquivo:
        df = df.add_prefix('Esl_')
        salvar_dados_base(df, "raw_esl", coluna_chave="Esl_Nota Fiscal/Chave Nf-E")
        return "Esl"
        
    elif 'bipe_produtos' in nome_arquivo:
        df = df.add_prefix('Bipe_Prod_')
        df = formatar_coluna_pedidos(df, 'Bipe_Prod_Pedido')
        salvar_dados_base(df, 'raw_bipe_produtos',  coluna_chave='Bipe_Prod_Pedido')
        return "Bipe Produtos"
        
    elif 'Bipe_de_notas' in nome_arquivo:
        df = df.add_prefix('Bipe_Notas_')
        df = formatar_coluna_pedidos(df, 'Bipe_Notas_Nf')
        salvar_dados_base(df, "raw_bipe_notas", coluna_chave="Bipe_Notas_Nf")
        return "Bipe Notas"

    elif 'Preventiva' in nome_arquivo:
        df = df.add_prefix('Preventiva_')
        df = formatar_coluna_pedidos(df,'Preventiva_Pedido 1P/Full')
        df = formatar_coluna_data(df, 'Preventiva_Data_Vencimento', pd)
        salvar_dados_base(df, "raw_preventiva", coluna_chave="Preventiva_Pedido 1P/Full")
        return 'Preventiva'
    
    return None