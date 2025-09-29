import pandas as pd
import os

# pd.set_option('display.max_rows', None)

# # Configura pandas para mostrar todas as colunas
# pd.set_option('display.max_columns', None)

# ==============================================================================
# --- CONFIGURAções E PADRÕES DE NOMES ---
# ==============================================================================
PADRAO_ARQUIVO_PREVENTIVA = "cd-etapa"
PADRAO_ARQUIVO_RELATORIO = "entregas"
COLUNA_CHAVE_PREVENTIVA = "pedido_gemco"
COLUNA_CHAVE_RELATORIO = "Pedido"
COLUNA_STATUS = "Tipo"
TEXTO_STATUS_ENTREGUE = "Entrega Realizada Normalmente"
TEXTO_STATUS_DEVOLVIDO = "Mercadoria devolvida ao CD"
# ==============================================================================
# --- FIM DAS CONFIGURAÇÕES ---
# ==============================================================================

print("Procurando os arquivos na pasta...")
nome_arquivo_preventiva_csv = None
nome_arquivo_preventiva_excel = None
nome_arquivo_relatorio = None

# --- LÓGICA DE BUSCA CORRIGIDA ---
for nome_do_arquivo in os.listdir("."): #Retorna uma lista de nomes de arquivos e pastas dentro do diretório - "." isso significa o diretório atual
    # Verifica o padrão E a extensão do arquivo para ser mais específico
    if nome_do_arquivo.startswith(PADRAO_ARQUIVO_PREVENTIVA) and nome_do_arquivo.endswith(".csv"):
        nome_arquivo_preventiva_csv = nome_do_arquivo
        print(f"-> Arquivo de preventiva encontrado: {nome_arquivo_preventiva_csv}")
    elif nome_do_arquivo.startswith(PADRAO_ARQUIVO_PREVENTIVA) and nome_do_arquivo.endswith(".xlsx"):
        nome_arquivo_preventiva_excel = nome_do_arquivo
        print(f"-> Arquivo de preventiva encontrado: {nome_arquivo_preventiva_excel}")

    if PADRAO_ARQUIVO_RELATORIO in nome_do_arquivo and nome_do_arquivo.endswith(".xls"): 
        nome_arquivo_relatorio = nome_do_arquivo
        print(f"-> Arquivo de relatório encontrado: {nome_arquivo_relatorio}")

if not nome_arquivo_preventiva_csv and not nome_arquivo_preventiva_excel or not nome_arquivo_relatorio:
    print("-" * 30)
    print("ERRO: Um ou ambos os arquivos não foram encontrados na pasta.")
    exit()

try:
    print("\nLendo a planilha de preventiva...")
    if nome_arquivo_preventiva_csv:
       df_preventiva = pd.read_csv(nome_arquivo_preventiva_csv,sep='\t',encoding='latin-1')
    elif nome_arquivo_preventiva_excel:
        df_preventiva = pd.read_excel(nome_arquivo_preventiva_excel)

    print("Lendo o relatório do Mobile Entregas...")
    df_relatorio = pd.read_excel(nome_arquivo_relatorio)
    
except Exception as e:
    print(f"Ocorreu um erro inesperado ao ler os arquivos: {e}")
    exit()

# --- O RESTANTE DO CÓDIGO PERMANECE O MESMO ---
print("\nLimpando nomes das colunas...")
df_preventiva.columns = df_preventiva.columns.str.strip()
df_relatorio.columns = df_relatorio.columns.str.strip()

if COLUNA_CHAVE_PREVENTIVA not in df_preventiva.columns:
    print(f"ERRO: A coluna '{COLUNA_CHAVE_PREVENTIVA}' não foi encontrada no arquivo de preventiva!")
    exit() #exit() é usado para parar a execução do programa imediatamente

if COLUNA_CHAVE_RELATORIO not in df_relatorio.columns:
    print(f"ERRO: A coluna '{COLUNA_CHAVE_RELATORIO}' não foi encontrada no relatório!")
    exit()

print("Cruzando os dados dos dois arquivos...")
df_resultado = pd.merge(df_preventiva, df_relatorio, left_on=COLUNA_CHAVE_PREVENTIVA, right_on=COLUNA_CHAVE_RELATORIO, how="left"
)

print("Analisando e separando os pedidos...")

pendentes_mask = (
    (df_resultado[COLUNA_STATUS] != TEXTO_STATUS_ENTREGUE) &
    (df_resultado[COLUNA_STATUS] != TEXTO_STATUS_DEVOLVIDO) |
    (df_resultado[COLUNA_STATUS].isna())
)
df_pendentes = df_resultado[pendentes_mask]
entregues_mask = df_resultado[COLUNA_STATUS] == TEXTO_STATUS_ENTREGUE
df_entregues = df_resultado[entregues_mask]
devolvidos_mask = df_resultado[COLUNA_STATUS] == TEXTO_STATUS_DEVOLVIDO
df_devolvidos = df_resultado[devolvidos_mask]
df_finalizados = df_resultado[df_resultado[COLUNA_STATUS].isin([TEXTO_STATUS_ENTREGUE, TEXTO_STATUS_DEVOLVIDO])]

#Gerando performance
performance = (len(df_finalizados) / len(df_preventiva)) * 100
meta_performance = 96.00

#Gerando o arquivo de resultado
output_filename = "Resultado_Monitoramento.xlsx"
print(f"Gerando o arquivo de resultado: {output_filename}")

with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
    df_pendentes.to_excel(writer, sheet_name="Pendentes", index=False)
    df_entregues.to_excel(writer, sheet_name="Entregues", index=False)
    df_devolvidos.to_excel(writer, sheet_name="Devolvidos", index=False)


print("-" * 30)
print("Análise concluída com sucesso!")
print(f"Total de pedidos na preventiva: {len(df_preventiva)}")
print(f"Pedidos finalizados: {len(df_finalizados)}")
print(f"Pedidos pendentes para cobrar: {len(df_pendentes)}")
print(f'Meta de Performance: {meta_performance:.2f}%')
print(f'Performance Atual: {performance:.2f}%')
print(f"O relatório '{output_filename}' foi criado nesta pasta.")

resposta = input('Deseja ver a lista de pedidos pendentes? Sim/Não: ')

if resposta == 'Sim':
   df_resultado_relatorio = pd.read_excel('Resultado_Monitoramento.xlsx', sheet_name="Pendentes")
   df_resultado_relatorio = df_resultado_relatorio[['Entregador', 'Tipo','pedido_gemco']]

   print(f'Lista de pedidos: {df_resultado_relatorio}')
else:
    print('Analise Finalizada!')



