import pandas as pd
import os
import json
import sys
import re # Importando biblioteca de expressões regulares

# ==============================================================================
# --- CONFIGURAÇÕES DE DIRETÓRIOS ---
# ==============================================================================
caminho_script = os.path.abspath(__file__)
diretorio_analise = os.path.dirname(caminho_script)
diretorio_raiz = os.path.dirname(diretorio_analise)
caminho_dados = os.path.join(diretorio_raiz, 'dados')

# ==============================================================================
# --- COLUNAS CHAVE PARA IDENTIFICAÇÃO ---
# ==============================================================================
COLUNA_IDENTIFICADORA_PREVENTIVA = "PEDIDO 1P/FULL"
COLUNA_IDENTIFICADORA_RELATORIO = "Pedido"

TEXTO_STATUS_ENTREGUE = "Entrega Realizada Normalmente"
TEXTO_STATUS_DEVOLVIDO = "Mercadoria devolvida ao CD"

df_preventiva = None
df_relatorio = None
nome_preventiva_encontrado = "Não identificado"
nome_relatorio_encontrado = "Não identificado"

print("Iniciando varredura inteligente de arquivos...", file=sys.stderr)

# ==============================================================================
# --- VARREDURA INTELIGENTE ---
# ==============================================================================
arquivos_na_pasta = [f for f in os.listdir(caminho_dados) if not f.startswith('.') and f != 'Resultado_Monitoramento.xlsx']

for arquivo in arquivos_na_pasta:
    caminho_completo = os.path.join(caminho_dados, arquivo)
    df_temp = None
    
    try:
        if arquivo.lower().endswith('.csv'):
            try:
                df_temp = pd.read_csv(caminho_completo, sep='\t', encoding='latin-1')
                if len(df_temp.columns) <= 1: 
                    df_temp = pd.read_csv(caminho_completo, sep=';', encoding='latin-1')
            except:
                continue 
                
        elif arquivo.lower().endswith(('.xlsx', '.xls')):
            df_temp = pd.read_excel(caminho_completo)
        else:
            continue 
            
    except Exception as e:
        print(f"Alerta: Não consegui ler o arquivo {arquivo}. Motivo: {e}", file=sys.stderr)
        continue

    if df_temp is not None:
        df_temp.columns = df_temp.columns.str.strip()

        if COLUNA_IDENTIFICADORA_PREVENTIVA in df_temp.columns and df_preventiva is None:
            df_preventiva = df_temp
            nome_preventiva_encontrado = arquivo
            print(f"-> IDENTIFICADO: Preventiva encontrada no arquivo '{arquivo}'", file=sys.stderr)
        
        elif COLUNA_IDENTIFICADORA_RELATORIO in df_temp.columns and df_relatorio is None:
            df_relatorio = df_temp
            nome_relatorio_encontrado = arquivo
            print(f"-> IDENTIFICADO: Relatório Mobile encontrado no arquivo '{arquivo}'", file=sys.stderr)

# ==============================================================================
# --- VALIDAÇÃO ---
# ==============================================================================
if df_preventiva is None:
    print("-" * 30, file=sys.stderr)
    print("ERRO CRÍTICO: Arquivo de PREVENTIVA não identificado.", file=sys.stderr)
    exit(1)

if df_relatorio is None:
    print("-" * 30, file=sys.stderr)
    print("ERRO CRÍTICO: Arquivo de RELATÓRIO DE ENTREGAS não identificado.", file=sys.stderr)
    exit(1)

# ==============================================================================
# --- TRATAMENTO DE DADOS (Lógica Nova Aqui) ---
# ==============================================================================
print("Validando e padronizando dados...", file=sys.stderr)

# --- 1. Tratamento do Relatório Mobile (Mantido) ---
df_relatorio['Pedido'] = df_relatorio['Pedido'].astype(str).replace('nan', '')
df_relatorio['Pedido Cliente'] = df_relatorio['Pedido Cliente'].astype(str).replace('nan', '')

def corrigir_pedido_relatorio(row):
    pedido_atual = row['Pedido']
    pedido_cliente = row['Pedido Cliente']
    
    if not pedido_atual or pedido_atual.strip() == '' or pedido_atual.lower() == 'nan':
        if pedido_cliente.endswith('.0'):
            pedido_cliente = pedido_cliente[:-2]
        return f"{pedido_cliente}-1"
    
    if pedido_atual.endswith('.0'):
        return pedido_atual[:-2]
    return pedido_atual

df_relatorio['Pedido'] = df_relatorio.apply(corrigir_pedido_relatorio, axis=1)

# --- 2. Tratamento da Preventiva (NOVA LÓGICA PEDIDA) ---
# Primeiro removemos '.0' se houver
df_preventiva[COLUNA_IDENTIFICADORA_PREVENTIVA] = df_preventiva[COLUNA_IDENTIFICADORA_PREVENTIVA].astype(str).str.replace('.0', '', regex=False)

def padronizar_preventiva(pedido):
    pedido = str(pedido).strip()
    
    # Verifica se tem mais de 10 digitos
    if len(pedido) > 10:
        # Regex para encontrar padrão final "-X" onde X é um dígito
        # Se terminar com -2, -3, -4 etc, substituímos por -1
        if re.search(r'-\d+$', pedido):
            # Se já terminar com -1, mantemos. Se for diferente, trocamos.
            if not pedido.endswith('-1'):
                # Corta o sufixo antigo e adiciona -1
                base = pedido.rsplit('-', 1)[0]
                return f"{base}-1"
    
    return pedido

# Aplica a nova função na coluna da preventiva
df_preventiva[COLUNA_IDENTIFICADORA_PREVENTIVA] = df_preventiva[COLUNA_IDENTIFICADORA_PREVENTIVA].apply(padronizar_preventiva)


# Filtro de Cidade
if 'Cidade Cliente' in df_preventiva.columns:
    df_preventiva = df_preventiva[df_preventiva['cidade_cliente'] != 'ITUMBIARA']
else:
    print("Aviso: Coluna 'cidade_cliente' não encontrada. Ignorando filtro.", file=sys.stderr)

print("Cruzando as informações...", file=sys.stderr)

df_resultado = pd.merge(
    df_preventiva, 
    df_relatorio, 
    left_on=COLUNA_IDENTIFICADORA_PREVENTIVA, 
    right_on=COLUNA_IDENTIFICADORA_RELATORIO, 
    how="left"
)

# Separação por Status
coluna_status = "Tipo"
if coluna_status not in df_resultado.columns:
    df_resultado[coluna_status] = 'Sem Status'

pendentes_mask = (
    (df_resultado[coluna_status] != TEXTO_STATUS_ENTREGUE) &
    (df_resultado[coluna_status] != TEXTO_STATUS_DEVOLVIDO) |
    (df_resultado[coluna_status].isna())
)

df_pendentes = df_resultado[pendentes_mask]
df_finalizados = df_resultado[~pendentes_mask]

# Cálculos
total_pedidos = len(df_preventiva)
pedidos_finalizados = len(df_finalizados)
pedidos_pendentes = len(df_pendentes)
performance = (pedidos_finalizados / total_pedidos) * 100 if total_pedidos > 0 else 0
meta_performance = 96.00

# Geração do Excel
output_filename = os.path.join(caminho_dados, "Resultado_Monitoramento.xlsx")
print(f"Gerando relatório final em: {output_filename}", file=sys.stderr)

df_performance = pd.DataFrame({
    "TOTAL": [total_pedidos], 
    "ENTREGUES": [pedidos_finalizados], 
    "INSUCESSO": [pedidos_pendentes],
    "PERFORMANCE": [f'{round(performance, 2)}%']
})

with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
    df_pendentes.to_excel(writer, sheet_name="Pendentes", index=False)
    df_finalizados.to_excel(writer, sheet_name="Finalizados", index=False)
    df_preventiva.to_excel(writer, sheet_name="Preventiva", index=False)
    df_performance.to_excel(writer, sheet_name="Performance", index=False)

# JSON para Frontend
colunas_display = ['cidade_cliente', 'PEDIDO 1P/FULL', 'Entregador', 'Tipo']

def preparar_dados(df):
    temp = df.copy()
    for col in colunas_display:
        if col not in temp.columns:
            temp[col] = 'N/A'
    return temp[colunas_display].fillna('Status não disponível').to_dict(orient='records')

resultados_json = {
    "total_pedidos": total_pedidos,
    "pedidos_finalizados": pedidos_finalizados,
    "pedidos_pendentes": pedidos_pendentes,
    "meta_performance": meta_performance,
    "performance_atual": round(performance, 2),
    "nome_relatorio": "Resultado_Monitoramento.xlsx",
    "arquivos_usados": f"{nome_preventiva_encontrado} + {nome_relatorio_encontrado}",
    "lista_pendentes": preparar_dados(df_pendentes),
    "lista_finalizados": preparar_dados(df_finalizados),
    "lista_total": preparar_dados(df_resultado)
}

print(json.dumps(resultados_json))