import pandas as pd
import os

# ==============================================================================
# --- CONFIGURAções E PADRÕES DE NOMES ---
# ==============================================================================
PADRAO_ARQUIVO_PREVENTIVA = "PREVENTIVA"
PADRAO_ARQUIVO_RELATORIO = "entregas"
COLUNA_CHAVE_PREVENTIVA = "PEDIDO"
COLUNA_CHAVE_RELATORIO = "Pedido"
COLUNA_STATUS = "Tipo"
TEXTO_STATUS_ENTREGUE = "Entrega Realizada Normalmente"
# ==============================================================================
# --- FIM DAS CONFIGURAÇÕES ---
# ==============================================================================

print("Procurando os arquivos na pasta...")
nome_arquivo_preventiva = None
nome_arquivo_relatorio = None

# --- LÓGICA DE BUSCA CORRIGIDA ---
for nome_do_arquivo in os.listdir("."):
    # Verifica o padrão E a extensão do arquivo para ser mais específico
    if nome_do_arquivo.startswith(PADRAO_ARQUIVO_PREVENTIVA) and nome_do_arquivo.endswith(".xlsx"):
        nome_arquivo_preventiva = nome_do_arquivo
        print(f"-> Arquivo de preventiva encontrado: {nome_arquivo_preventiva}")
        
    if PADRAO_ARQUIVO_RELATORIO in nome_do_arquivo and nome_do_arquivo.endswith(".xls"):
        nome_arquivo_relatorio = nome_do_arquivo
        print(f"-> Arquivo de relatório encontrado: {nome_arquivo_relatorio}")

if not nome_arquivo_preventiva or not nome_arquivo_relatorio:
    print("-" * 30)
    print("ERRO: Um ou ambos os arquivos não foram encontrados na pasta.")
    exit()

try:
    print("\nLendo a planilha de preventiva...")
    df_preventiva = pd.read_excel(nome_arquivo_preventiva)
    
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
    exit()

if COLUNA_CHAVE_RELATORIO not in df_relatorio.columns:
    print(f"ERRO: A coluna '{COLUNA_CHAVE_RELATORIO}' não foi encontrada no relatório!")
    exit()

print("Cruzando os dados dos dois arquivos...")
df_resultado = pd.merge(
    df_preventiva, 
    df_relatorio, 
    left_on=COLUNA_CHAVE_PREVENTIVA, 
    right_on=COLUNA_CHAVE_RELATORIO, 
    how="left"
)

print("Analisando e separando os pedidos...")
pendentes_mask = (df_resultado[COLUNA_STATUS] != TEXTO_STATUS_ENTREGUE) | (df_resultado[COLUNA_STATUS].isna())
df_pendentes = df_resultado[pendentes_mask]

entregues_mask = df_resultado[COLUNA_STATUS] == TEXTO_STATUS_ENTREGUE
df_entregues = df_resultado[entregues_mask]

output_filename = "Resultado_Monitoramento.xlsx"
print(f"Gerando o arquivo de resultado: {output_filename}")

with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
    df_pendentes.to_excel(writer, sheet_name="Pendentes", index=False)
    df_entregues.to_excel(writer, sheet_name="Entregues", index=False)
    
print("-" * 30)
print("Análise concluída com sucesso!")
print(f"Total de pedidos na preventiva: {len(df_preventiva)}")
print(f"Pedidos entregues: {len(df_entregues)}")
print(f"Pedidos pendentes para cobrar: {len(df_pendentes)}")
print(f"O relatório '{output_filename}' foi criado nesta pasta.")