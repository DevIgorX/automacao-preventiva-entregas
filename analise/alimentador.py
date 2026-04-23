# Crie este arquivo em: analise/alimentador.py

import pandas as pd
# Importa a sua função de limpar as colunas que já existe no utils
from app.utils import formatar_colunas 
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
        salvar_dados_base(df, "raw_carreta")
        return "Carreta"
        
    elif 'Mobile' in nome_arquivo:
        df = df.add_prefix('Mobile_')
        salvar_dados_base(df, "raw_mobile")
        return "Mobile"
        
    elif 'magazine' in nome_arquivo or 'Esl' in nome_arquivo:
        df = df.add_prefix('Esl_')
        salvar_dados_base(df, "raw_esl")
        return "Esl"
        
    elif 'bipe_produtos' in nome_arquivo:
        df = df.add_prefix('Bipe_Prod_')
        salvar_dados_base(df, "raw_bipe_produtos")
        return "Bipe Produtos"
        
    elif 'Bipe_de_notas' in nome_arquivo:
        df = df.add_prefix('Bipe_Notas_')
        salvar_dados_base(df, "raw_bipe_notas")
        return "Bipe Notas"

    elif 'preventiva' in nome_arquivo:
        df = df.add_prefix('Preventiva_')
        salvar_dados_base(df,'raw preventiva')
        return 'Preventiva'
    
    return None