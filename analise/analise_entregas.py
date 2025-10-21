import pandas as pd
import os
import json # Importe a biblioteca JSON
import sys  # Importe a biblioteca sys para redirecionar a saída

# ... (toda a parte inicial do seu código permanece igual)
# ... (lógica para encontrar caminhos, etc.)

# ==============================================================================
# --- Lógica para encontrar os caminhos das pastas ---
# ==============================================================================
# Pega o caminho absoluto do script atual
caminho_script = os.path.abspath(__file__)
# Pega o diretório do script (pasta 'analise')
diretorio_analise = os.path.dirname(caminho_script)
# Sobe um nível para chegar na pasta raiz do projeto
diretorio_raiz = os.path.dirname(diretorio_analise)

# Define os caminhos para a pasta de dados e para o arquivo de saída
caminho_dados = os.path.join(diretorio_raiz, 'dados')
caminho_saida = diretorio_raiz

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

# ALTERAÇÃO: Mande os logs para stderr para não poluir a saída de dados
print("Procurando os arquivos na pasta...", file=sys.stderr) 
nome_arquivo_preventiva_csv = None
nome_arquivo_preventiva_excel = None
nome_arquivo_relatorio = None

# --- LÓGICA DE BUSCA CORRIGIDA ---
for nome_do_arquivo in os.listdir(caminho_dados): 
    caminho_arquivo = os.path.join(caminho_dados, nome_do_arquivo)
    if nome_do_arquivo.startswith(PADRAO_ARQUIVO_PREVENTIVA) and nome_do_arquivo.endswith(".csv"):
        nome_arquivo_preventiva_csv = caminho_arquivo
        print(f"-> Arquivo de preventiva encontrado: {nome_arquivo_preventiva_csv}", file=sys.stderr)
    elif nome_do_arquivo.startswith(PADRAO_ARQUIVO_PREVENTIVA) and nome_do_arquivo.endswith(".xlsx"):
        nome_arquivo_preventiva_excel = caminho_arquivo
        print(f"-> Arquivo de preventiva encontrado: {nome_arquivo_preventiva_excel}", file=sys.stderr)
    if PADRAO_ARQUIVO_RELATORIO in nome_do_arquivo and nome_do_arquivo.endswith(".xls"):
        nome_arquivo_relatorio = caminho_arquivo
        print(f"-> Arquivo de relatório encontrado: {nome_arquivo_relatorio}", file=sys.stderr)

if not nome_arquivo_preventiva_csv and not nome_arquivo_preventiva_excel or not nome_arquivo_relatorio:
    print("-" * 30, file=sys.stderr)
    print("ERRO: Um ou ambos os arquivos não foram encontrados na pasta.", file=sys.stderr)
    exit()

try:
    print("\nLendo a planilha de preventiva...", file=sys.stderr)
    if nome_arquivo_preventiva_csv:
       df_preventiva = pd.read_csv(nome_arquivo_preventiva_csv,sep='\t',encoding='latin-1')
    elif nome_arquivo_preventiva_excel:
        df_preventiva = pd.read_excel(nome_arquivo_preventiva_excel)

    print("Lendo o relatório do Mobile Entregas...", file=sys.stderr)
    df_relatorio = pd.read_excel(nome_arquivo_relatorio)
    
except Exception as e:
    print(f"Ocorreu um erro inesperado ao ler os arquivos: {e}", file=sys.stderr)
    exit()

# --- O RESTANTE DO CÓDIGO PERMANECE O MESMO ---
print("\nLimpando nomes das colunas...", file=sys.stderr)
df_preventiva.columns = df_preventiva.columns.str.strip()
df_relatorio.columns = df_relatorio.columns.str.strip()

if COLUNA_CHAVE_PREVENTIVA not in df_preventiva.columns:
    print(f"ERRO: A coluna '{COLUNA_CHAVE_PREVENTIVA}' não foi encontrada no arquivo de preventiva!", file=sys.stderr)
    exit()

if COLUNA_CHAVE_RELATORIO not in df_relatorio.columns:
    print(f"ERRO: A coluna '{COLUNA_CHAVE_RELATORIO}' não foi encontrada no relatório!", file=sys.stderr)
    exit()
#desenvolver filtros para pedidos que estão foram de rota ex: Itumbiara

df_preventiva = df_preventiva.query(" `Cidade Cliente ` !=  'ITUMBIARA' ")
print("Cruzando os dados dos dois arquivos...", file=sys.stderr)
df_resultado = pd.merge(df_preventiva, df_relatorio, left_on=COLUNA_CHAVE_PREVENTIVA, right_on=COLUNA_CHAVE_RELATORIO, how="left")

print("Analisando e separando os pedidos...", file=sys.stderr)
pendentes_mask = (
    (df_resultado[COLUNA_STATUS] != TEXTO_STATUS_ENTREGUE) &
    (df_resultado[COLUNA_STATUS] != TEXTO_STATUS_DEVOLVIDO) |
    (df_resultado[COLUNA_STATUS].isna())
)
df_pendentes = df_resultado[pendentes_mask]
df_finalizados = df_resultado[df_resultado[COLUNA_STATUS].isin([TEXTO_STATUS_ENTREGUE, TEXTO_STATUS_DEVOLVIDO])]

performance = (len(df_finalizados) / len(df_preventiva)) * 100 if len(df_preventiva) > 0 else 0
meta_performance = 96.00

output_filename = os.path.join(caminho_dados, "Resultado_Monitoramento.xlsx")
print(f"Gerando o arquivo de resultado: {output_filename}", file=sys.stderr)

with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
    df_pendentes.to_excel(writer, sheet_name="Pendentes", index=False)
    # ... você pode salvar as outras abas também se quiser
    
# --- NOVA SEÇÃO PARA CRIAR A SAÍDA JSON ---

# Define as colunas que queremos mostrar nas tabelas
colunas_display = ['Cidade Cliente', 'pedido_gemco', 'Entregador', 'Tipo']

def preparar_df_para_json(df, colunas):
    """Função auxiliar para preparar o dataframe para a saída."""
    for col in colunas:
        if col not in df.columns:
            df[col] = 'N/A'
    df_resumo = df[colunas].fillna('Status não disponível')
    return df_resumo.to_dict(orient='records')

# Prepara as três listas de dados
lista_pendentes = preparar_df_para_json(df_pendentes, colunas_display)
lista_finalizados = preparar_df_para_json(df_finalizados, colunas_display)
lista_total = preparar_df_para_json(df_resultado, colunas_display) # df_resultado contém todos os pedidos

# Cria um dicionário com todos os resultados
resultados = {
    "total_pedidos": len(df_preventiva),
    "pedidos_finalizados": len(df_finalizados),
    "pedidos_pendentes": len(df_pendentes),
    "meta_performance": meta_performance,
    "performance_atual": round(performance, 2),
    "nome_relatorio": os.path.basename(output_filename),
    "lista_pendentes": lista_pendentes,
    "lista_finalizados": lista_finalizados,
    "lista_total": lista_total
}

# Converte o dicionário para uma string JSON e imprime na saída padrão
print(json.dumps(resultados))
