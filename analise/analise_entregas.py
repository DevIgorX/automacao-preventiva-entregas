
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
# --- CONFIGURAções E PADRÕES DE NOMES ----
# ==============================================================================
PADRAO_ARQUIVO_PREVENTIVA = "cd-etapa"
PADRAO_ARQUIVO_PREVENTIVA_OP = "Relatorio_DOMICILIO"
PADRAO_ARQUIVO_RELATORIO = "entregas"
COLUNA_CHAVE_PREVENTIVA = "PEDIDO 1P/FULL"
COLUNA_CHAVE_RELATORIO = "Pedido"
COLUNA_STATUS = "Tipo"
TEXTO_STATUS_ENTREGUE = "Entrega Realizada Normalmente"
TEXTO_STATUS_DEVOLVIDO = "Mercadoria devolvida ao CD"
# ==============================================================================
# --- FIM DAS CONFIGURAÇÕES ---
# ==============================================================================

# ALTERAÇÃO: file=sys.stder muda a saida padrão do print que no caso seria no terminal, em vez disso envia para o canal de 'erro-padrao' ou sys.stderr
# print("Procurando os arquivos na pasta...", file=sys.stderr) #esse file faz parte de um paramentro da função print e que representa o destino da mensagem, no caso file=sys.stdout , ou seja o terminal
nome_arquivo_preventiva_csv = None
nome_arquivo_preventiva_excel = None
nome_arquivo_relatorio = None

# --- LÓGICA DE BUSCA CORRIGIDA ---
for nome_do_arquivo in os.listdir(caminho_dados): 
    caminho_arquivo = os.path.join(caminho_dados, nome_do_arquivo)
    if nome_do_arquivo.startswith(PADRAO_ARQUIVO_PREVENTIVA) and nome_do_arquivo.endswith(".csv"):
        nome_arquivo_preventiva_csv = caminho_arquivo
        # print(f"-> Arquivo de preventiva encontrado: {nome_arquivo_preventiva_csv}", file=sys.stderr)
    elif nome_do_arquivo.startswith(PADRAO_ARQUIVO_PREVENTIVA) and nome_do_arquivo.endswith(".xlsx"):
        nome_arquivo_preventiva_excel = caminho_arquivo
        # print(f"-> Arquivo de preventiva encontrado: {nome_arquivo_preventiva_excel}", file=sys.stderr)
    elif nome_do_arquivo.startswith(PADRAO_ARQUIVO_PREVENTIVA_OP) and nome_do_arquivo.endswith(".xlsx"):
        nome_arquivo_preventiva_excel = caminho_arquivo
        # print(f"-> Arquivo de preventiva encontrado: {nome_arquivo_preventiva_excel}", file=sys.stderr)
   

    if PADRAO_ARQUIVO_RELATORIO in nome_do_arquivo and nome_do_arquivo.endswith(".xls"):
        nome_arquivo_relatorio = caminho_arquivo
        # print(f"-> Arquivo de relatório encontrado: {nome_arquivo_relatorio}", file=sys.stderr)
   

if not nome_arquivo_preventiva_csv and not nome_arquivo_preventiva_excel:
    print("-" * 30, file=sys.stderr) #ele pega a string à esquerda "-" é multiplica 30 vezes formando um "-------------------------------------"
    print("ERRO: Arquivo de PREVENTIVA não encontrado.", file=sys.stderr)
    print(f"O arquivo deve começar com '{PADRAO_ARQUIVO_PREVENTIVA}' ou '{PADRAO_ARQUIVO_PREVENTIVA_OP}' e ser .csv ou .xlsx.", file=sys.stderr)
    exit() #exit para a execução do script imediatamente

if not nome_arquivo_relatorio:
    print("-" * 30, file=sys.stderr)
    print("ERRO: Arquivo de RELATÓRIO não encontrado.", file=sys.stderr)
    print(f"O arquivo deve conter '{PADRAO_ARQUIVO_RELATORIO}' no nome e ser .xls.", file=sys.stderr)
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


print("\nLimpando nomes das colunas...", file=sys.stderr)
df_preventiva.columns = df_preventiva.columns.str.strip()
df_relatorio.columns = df_relatorio.columns.str.strip()

# ==============================================================================
# --- NOVA VALIDAÇÃO: PREENCHER PEDIDO VAZIO COM PEDIDO CLIENTE + "-1" ---
# ==============================================================================
print("Validando e corrigindo coluna de Pedidos...", file=sys.stderr)

# 1. Garante que as colunas sejam tratadas como texto para evitar erros
# O astype(str) previne erro se o pandas leu como número
df_relatorio['Pedido'] = df_relatorio['Pedido'].astype(str).replace('nan', '')
df_relatorio['Pedido Cliente'] = df_relatorio['Pedido Cliente'].astype(str).replace('nan', '')

def corrigir_pedido(row):
    pedido_atual = row['Pedido']
    pedido_cliente = row['Pedido Cliente']
    
    # Verifica se o pedido está vazio, nulo ou é apenas espaço em branco
    if not pedido_atual or pedido_atual.strip() == '' or pedido_atual.lower() == 'nan':
        # Remove '.0' caso o pandas tenha lido o Pedido Cliente como float (ex: 12345.0)
        if pedido_cliente.endswith('.0'):
            pedido_cliente = pedido_cliente[:-2]
            
        return f"{pedido_cliente}-1"
    
    # Se já tiver pedido, remove o '.0' caso exista e retorna ele mesmo
    if pedido_atual.endswith('.0'):
        return pedido_atual[:-2]
        
    return pedido_atual

# Aplica a função linha a linha (axis=1)
df_relatorio['Pedido'] = df_relatorio.apply(corrigir_pedido, axis=1)

# Garante que a coluna chave da preventiva também esteja limpa de '.0' e seja string
df_preventiva[COLUNA_CHAVE_PREVENTIVA] = df_preventiva[COLUNA_CHAVE_PREVENTIVA].astype(str).str.replace('.0', '', regex=False)

# ==============================================================================
# --- FIM DA NOVA VALIDAÇÃO ---
# ==============================================================================

if COLUNA_CHAVE_PREVENTIVA not in df_preventiva.columns:
    print(f"ERRO: Arquivo de preventiva inválido!", file=sys.stderr)
    print(f"O arquivo enviado não contém a coluna obrigatória: '{COLUNA_CHAVE_PREVENTIVA}'.", file=sys.stderr)
    print("Por favor, verifique o arquivo e tente novamente.", file=sys.stderr)
    exit()

if COLUNA_CHAVE_RELATORIO not in df_relatorio.columns:
    print(f"ERRO: Arquivo de relatório inválido!", file=sys.stderr)
    print(f"O arquivo enviado não contém a coluna obrigatória: '{COLUNA_CHAVE_RELATORIO}'.", file=sys.stderr)
    print("Por favor, verifique o arquivo e tente novamente.", file=sys.stderr)
    exit()

#filtros para pedidos que estão foram de rota ex: Itumbiara
df_preventiva = df_preventiva[df_preventiva['Cidade Cliente'] != 'ITUMBIARA']

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

total_pedidos = len(df_preventiva)
pedidos_finalizados = len(df_finalizados)
pedidos_pendentes = len(df_pendentes)
meta_performance =  meta_performance
performance_atual = f'{round(performance, 2)}%'

df_performance = pd.DataFrame({
    "TOTAL": [total_pedidos], 
    "ENTREGUES": [pedidos_finalizados], 
    "INSUCESSO": [pedidos_pendentes] ,
    "PERFORMANCE": performance_atual })


output_filename = os.path.join(caminho_dados, "Resultado_Monitoramento.xlsx")
print(f"Gerando o arquivo de resultado: {output_filename}", file=sys.stderr)

with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
    df_pendentes.to_excel(writer, sheet_name="Pendentes", index=False)
    df_finalizados.to_excel(writer, sheet_name="Finalizados", index=False)
    df_preventiva.to_excel(writer, sheet_name="Preventiva", index=False)
    df_performance.to_excel(writer, sheet_name="Performance",index=False)
 
    
# --- NOVA SEÇÃO PARA CRIAR A SAÍDA JSON ---

# Define as colunas que queremos mostrar nas tabelas
colunas_display = ['Cidade Cliente', 'PEDIDO 1P/FULL', 'Entregador', 'Tipo']

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
