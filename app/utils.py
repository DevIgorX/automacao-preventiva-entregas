def formatar_colunas(df):
    df.columns = df.columns.str.strip().str.lower().str.title()
    return df



def formatar_coluna_pedidos(df,coluna_pedido):
    df[coluna_pedido] = df[coluna_pedido].fillna('').astype(str).str.replace('.0', '', regex=False).str.strip()
    return df


def formatar_coluna_data(df, coluna_data, pd):
    df[coluna_data] = pd.to_datetime(df[coluna_data],errors='coerce').dt.strftime('%d/%m/%Y')
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
