def formatar_colunas(df):
    df.columns = df.columns.str.strip().str.lower().str.title()
    return df



def formatar_colunas2(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(' ', '_')
        .str.replace('/', '_', regex=False)
    )
    return df


def colunas_para_excel(df):
    df.columns = (
        df.columns
        .str.replace('_', ' ')
        .str.title()
    )
    return df

# Uso:
# df_final_2 = colunas_para_excel(df_final_2)
# df_final_2.to_excel('Relatorio_Diario.xlsx', index=False)
