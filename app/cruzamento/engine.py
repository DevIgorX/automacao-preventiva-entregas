"""Cruzamentos independentes do nome dos arquivos e do banco operacional."""
import csv
import re
from pathlib import Path
import pandas as pd

MAX_ROWS = 200_000


def read_table(path, sheet=0, header=1):
    if not 1 <= int(header) <= 100:
        raise ValueError('A linha dos títulos deve estar entre 1 e 100.')
    if Path(path).suffix.lower() == '.csv':
        raw = Path(path).read_bytes()
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            text = raw.decode('latin-1')
        from io import StringIO
        try:
            delimiter = csv.Sniffer().sniff(text[:16384], delimiters=';,\t,').delimiter
        except csv.Error:
            delimiter = ';'
        df = pd.read_csv(StringIO(text), sep=delimiter, header=int(header)-1,
                         dtype=str, keep_default_na=False, nrows=MAX_ROWS+1)
    else:
        df = pd.read_excel(path, sheet_name=sheet, header=int(header)-1,
                           dtype=str, keep_default_na=False, nrows=MAX_ROWS+1)
    if len(df) > MAX_ROWS:
        raise ValueError('Este arquivo excede o limite de 200 mil linhas por análise.')
    if df.empty or not len(df.columns):
        raise ValueError('A aba selecionada está vazia.')
    df.columns = [str(c).strip() for c in df.columns]
    if len(set(df.columns)) != len(df.columns):
        raise ValueError('Existem títulos repetidos. Renomeie as colunas antes de continuar.')
    return df.fillna('')


def normalize(value):
    value = str(value).strip()
    if value.startswith('="') and value.endswith('"'):
        value = value[2:-1].strip()
    # Não converte para float: preserva zeros iniciais e as 44 posições da chave NF-e.
    if re.fullmatch(r'\d+\.0', value):
        value = value[:-2]
    return value


def merge_tables(base, source, left_keys, right_keys, columns, label, policy='error'):
    if not left_keys or len(left_keys) != len(right_keys):
        raise ValueError('Escolha pares de colunas para o cruzamento.')
    if len(set(left_keys)) != len(left_keys) or len(set(right_keys)) != len(right_keys):
        raise ValueError('Não repita uma coluna nos pares de chaves.')
    if not columns:
        raise ValueError('Selecione ao menos uma informação para acrescentar.')
    if any(c not in base for c in left_keys) or any(c not in source for c in right_keys+columns):
        raise ValueError('Uma das colunas selecionadas não existe.')
    if policy not in ('error', 'first', 'last', 'join', 'expand'):
        raise ValueError('Tratamento de correspondências inválido.')
    label = label.strip()
    if not label or len(label) > 60:
        raise ValueError('Informe um nome para a fonte com até 60 caracteres.')
    names = [f'{label} · {c}' for c in columns]
    if len(set(names)) != len(names) or any(n in base for n in names):
        raise ValueError('Já existem colunas com esse nome. Escolha outro nome para a fonte.')
    # Chaves calculadas separadamente: as colunas originais nunca são alteradas.
    def keys(df, selected):
        normalized = df[selected].map(normalize) if hasattr(df, 'map') else df[selected].applymap(normalize)
        return [tuple(row) if all(row) else None for row in normalized.itertuples(index=False, name=None)]
    left = keys(base, left_keys)
    right = keys(source, right_keys)
    groups = {}
    for i, key in enumerate(right):
        if key is not None:
            groups.setdefault(key, []).append(i)
    duplicates = sum(len(v)>1 for v in groups.values())
    if duplicates and policy == 'error':
        raise ValueError(f'A fonte tem {duplicates} chave(s) com várias correspondências. Escolha como tratar essas repetições.')
    matched = sum(key in groups for key in left)
    size = sum(len(groups.get(key, [])) or 1 for key in left) if policy == 'expand' else len(base)
    if size > MAX_ROWS:
        raise ValueError('O cruzamento geraria mais de 200 mil linhas. Escolha outro tratamento para as repetições.')
    output = []
    records = source[columns].values.tolist()
    for row, key in zip(base.values.tolist(), left):
        indices = groups.get(key, [])
        if not indices:
            output.append(row + ['']*len(columns))
        elif policy == 'join':
            values = [' | '.join(dict.fromkeys(str(records[i][j]) for i in indices if str(records[i][j]))) for j in range(len(columns))]
            output.append(row + values)
        else:
            chosen = indices if policy == 'expand' else [indices[-1] if policy == 'last' else indices[0]]
            output.extend(row + records[i] for i in chosen)
    result = pd.DataFrame(output, columns=list(base.columns)+names)
    return result, {'fonte': label, 'entrada': len(base), 'encontradas': matched,
                    'sem_correspondencia': len(base)-matched, 'saida': len(result),
                    'chaves_repetidas_fonte': duplicates, 'tratamento': policy,
                    'chaves': ' + '.join(left_keys)+' ↔ '+' + '.join(right_keys)}
