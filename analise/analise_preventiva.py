import pandas as pd
from datetime import datetime
import os
import sys


caminho_script = os.path.abspath(__file__)
diretorio_analise = os.path.dirname(caminho_script)
diretorio_raiz = os.path.dirname(diretorio_analise)
sys.path.append(diretorio_raiz)
caminho_dados = os.path.join(diretorio_raiz, 'dados_preventiva')

from app.utils import formatar_colunas
from db.db_preventiva import salvar_no_banco

for arquivo in os.listdir(caminho_dados):
    caminho_arquivo = os.path.join(caminho_dados, arquivo)

    if 'Preventiva' in arquivo:
        df_preventiva = pd.read_excel(caminho_arquivo)
        df_preventiva = formatar_colunas(df_preventiva)
        df_preventiva = df_preventiva.add_prefix('Preventiva_')
    elif 'Carreta' in arquivo:
        df_carreta = pd.read_excel(caminho_arquivo)
        df_carreta = formatar_colunas(df_carreta)
        df_carreta = df_carreta.add_prefix('Carreta_')
    elif 'magazine' in arquivo:
        df_esl = pd.read_excel(caminho_arquivo)
        df_esl = formatar_colunas(df_esl)
        df_esl = df_esl.add_prefix('Esl_')
    elif 'Mobile' in arquivo:
        df_mobile = pd.read_excel(caminho_arquivo)
        df_mobile = formatar_colunas(df_mobile)
        df_mobile = df_mobile.add_prefix('Mobile_')
    elif 'bipe_produtos' in arquivo:
        df_bipe = pd.read_excel(caminho_arquivo)
        df_bipe = formatar_colunas(df_bipe)
        df_bipe = df_bipe.add_prefix('Bipe_Prod_')
    elif 'Bipe_de_notas' in arquivo:
        df_bipe_notas = pd.read_excel(caminho_arquivo, sheet_name='Plan1')
        df_bipe_notas = formatar_colunas(df_bipe_notas)
        df_bipe_notas = df_bipe_notas.add_prefix('Bipe_Notas_')
        

# df_preventiva = df_preventiva.drop_duplicates(subset='Preventiva_Pedido 1P/Full', keep='first')


df_final = (
    df_preventiva
        .merge(
            df_carreta[['Carreta_Pedido', 'Carreta_Nf`S', 'Carreta_Chave', 'Carreta_Data Entrada', 'Carreta_Tipo_Fluxo']],
            left_on='Preventiva_Pedido 1P/Full',  right_on='Carreta_Pedido',
            how='left'
        )
        .drop(columns=['Carreta_Pedido'])

        .merge(
            # Ajuste: Prefixo 'Mobile_' + Title Case
            df_mobile[['Mobile_Pedido', 'Mobile_Tipo', 'Mobile_Entregador']],
            left_on='Preventiva_Pedido 1P/Full',
            right_on='Mobile_Pedido',
            how='left'
        )
        .drop(columns=['Mobile_Pedido'])

        .merge(
            # Ajuste: Prefixo 'Esl_' + Title Case (inclusive em siglas como NF-E -> Nf-E)
            df_esl[[
                'Esl_Nota Fiscal/Chave Nf-E',            # .title() transforma "NF-E" em "Nf-E"
                'Esl_Última Ocorrência/Observações',
                'Esl_Pessoa/Nome',
                'Esl_Última Ocorrência/Data Ocorrência'
            ]],
            left_on='Carreta_Chave',
            right_on='Esl_Nota Fiscal/Chave Nf-E',
            how='left'
        )
        .drop(columns=['Esl_Nota Fiscal/Chave Nf-E'])

        .merge(
            # Ajuste: Prefixo 'Bipe_Prod_' + Title Case
            df_bipe[['Bipe_Prod_Pedido', 'Bipe_Prod_Status_Deposito']],
            left_on='Preventiva_Pedido 1P/Full',
            right_on='Bipe_Prod_Pedido',
            how='left'
        )
        .drop(columns=['Bipe_Prod_Pedido'])

        .merge(
            # Ajuste: Prefixo 'Bipe_Notas_' + Title Case (NF vira Nf)
            df_bipe_notas[['Bipe_Notas_Nf', 'Bipe_Notas_Ocorrencia']],
            left_on='Carreta_Nf`S', 
            right_on='Bipe_Notas_Nf',
            how='left'
        )
        .drop(columns=['Bipe_Notas_Nf'])
)

# Ajuste do df_final_2 (Correlação Carreta x ESL)
df_final_2 = (
    pd.merge(
        df_carreta,
        df_esl[['Esl_Nota Fiscal/Chave Nf-E', 'Esl_Ocorrência/Ocorrência']], 
        left_on='Carreta_Chave', 
        right_on='Esl_Nota Fiscal/Chave Nf-E', 
        how='left'
    )
    
)


# Definição das colunas de observação (Title Case)
coluna_obs = 'Esl_Última Ocorrência/Observações'
coluna_ocorrencia = 'Esl_Ocorrência/Ocorrência'

df_final[coluna_obs] = df_final[coluna_obs].fillna('Não informado')

# Merge final
df_final_3 = pd.merge(
    df_final, 
    df_final_2[['Esl_Nota Fiscal/Chave Nf-E', coluna_ocorrencia]], 
    left_on='Carreta_Chave', 
    right_on='Esl_Nota Fiscal/Chave Nf-E', 
    how='left'
).drop(columns=['Esl_Nota Fiscal/Chave Nf-E'])

# Preenchimento condicional
filtro = df_final_3[coluna_obs] == 'Não informado'
df_final_3.loc[filtro, coluna_obs] = df_final_3.loc[filtro, coluna_ocorrencia]

df_final_3 = df_final_3.drop(columns=[coluna_ocorrencia])

#movendo a coluna chave para o final da planilha
coluna_chave = df_final_3.pop('Carreta_Chave')
df_final_3['Chave_nf-e'] = coluna_chave

# Formatação de datas (Nomes atualizados)
colunas_datas = [
    'Carreta_Data Entrada',
    'Esl_Última Ocorrência/Data Ocorrência'
]



df_final_3 = df_final_3.drop_duplicates(subset='Preventiva_Pedido 1P/Full', keep='first')

for col in colunas_datas:
    
    if col in df_final_3.columns:
        df_final_3[col] = pd.to_datetime(df_final_3[col], errors='coerce').dt.strftime('%d/%m/%Y').fillna('Não informado')


salvar_no_banco(df_final_3)

data_hoje = datetime.today().strftime('%d-%m-%Y')
nome_arquivo = f'Analise_preventiva {data_hoje}.xlsx'
caminho_saida = os.path.join(caminho_dados, nome_arquivo)

with pd.ExcelWriter(
    caminho_saida,
    engine='xlsxwriter',
    datetime_format='dd/mm/yyyy'
) as writer:
    
    df_final_3.to_excel( 
        writer,
        sheet_name='Relatorio_diario',
        index=False
    )

print('processamento encerrou!')

# resultado_json = df_final_3.to_json(orient='records')
# print(resultado_json)