
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
    
    # if 'Carreta' in nome_arquivo:
    #     df = df.add_prefix('Carreta_')
    #     df = formatar_coluna_pedidos(df,'Carreta_Pedido')
    #     df = formatar_coluna_pedidos(df,'Carreta_Nf`S')
    #     salvar_dados_base(df,'raw_carreta', coluna_chave='Carreta_Pedido')
    #     return 'Carreta'
    if 'Carreta' in nome_arquivo:
        df = df.add_prefix('Carreta_')
        df = formatar_coluna_pedidos(df, 'Carreta_Pedido')
        df = formatar_coluna_pedidos(df, 'Carreta_Nf`S')
        
        # --- ADICIONE ESTA LINHA: ---
        # Garante que a chave da carreta não tem espaços e cruza perfeitamente com o ESL
        if 'Carreta_Chave' in df.columns:
            df = formatar_coluna_pedidos(df, 'Carreta_Chave')
            
        salvar_dados_base(df, 'raw_carreta', coluna_chave='Carreta_Pedido')
        return 'Carreta'
        
    elif 'Mobile' in nome_arquivo:
        df = df.add_prefix('Mobile_')
        df = formatar_coluna_pedidos(df, 'Mobile_Pedido')
        salvar_dados_base(df, "raw_mobile", coluna_chave="Mobile_Pedido")
        return "Mobile"
        
    elif 'magazine' in nome_arquivo or 'Esl' in nome_arquivo:
        df = df.add_prefix('Esl_')
        
        # --- 1. TRAVA DE SEGURANÇA DOS CABEÇALHOS ---
        # Mapeamento para garantir que o banco recebe o nome exato esperado nas consultas
        # independente de como o Excel enviar (maiúscula, minúscula, etc)
        mapa_colunas = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'chave nf' in col_lower:
                mapa_colunas[col] = 'Esl_Nota Fiscal/Chave Nf-E'
            elif 'data ocorr' in col_lower and 'ação' not in col_lower:
                mapa_colunas[col] = 'Esl_Última Ocorrência/Data Ocorrência'
            elif 'observa' in col_lower and 'última' in col_lower:
                mapa_colunas[col] = 'Esl_Última Ocorrência/Observações'
            elif 'ocorrência/ocorrência' in col_lower or 'ocorrencia/ocorrencia' in col_lower:
                mapa_colunas[col] = 'Esl_Ocorrência/Ocorrência'
            elif 'pessoa/nome' in col_lower:
                mapa_colunas[col] = 'Esl_Pessoa/Nome'
                
        df.rename(columns=mapa_colunas, inplace=True)
        
        # --- 2. LIMPEZA DA CHAVE DE ACESSO ---
        # Usa a sua própria função do utils para tirar '.0' e espaços em branco da chave 44 dígitos
        if 'Esl_Nota Fiscal/Chave Nf-E' in df.columns:
            df = formatar_coluna_pedidos(df, 'Esl_Nota Fiscal/Chave Nf-E')
            
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