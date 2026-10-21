
from contextlib import contextmanager
from io import BytesIO
import json
import os
import re
from pathlib import Path
import secrets
import shutil
import tempfile
import threading
import time
import zipfile

import pandas as pd
from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, session, url_for, abort
from .engine import read_table, merge_tables

bp = Blueprint('cruzamento', __name__, url_prefix='/cruzar-planilhas')
# Waitress usa threads em um processo. Slots fixos evitam acumular locks por sessão.
_locks = [threading.RLock() for _ in range(64)]
TTL = 24*60*60


def root():
    path = Path(current_app.config.get('CRUZAMENTO_TEMP_DIR',
                Path(tempfile.gettempdir())/'preventiva-cruzamentos'))
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def workdir():
    sid = session.get('cruzamento_id', '')
    if len(sid) != 64 or any(c not in '0123456789abcdef' for c in sid):
        sid = secrets.token_hex(32)
        session['cruzamento_id'] = sid
    return root()/sid


def save_json(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(
        data, ensure_ascii=False), encoding='utf-8')
    os.replace(temporary, path)


def save_frame(path, df):
    save_json(path, {'columns': list(df.columns), 'data': df.values.tolist()})


def load_frame(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    return pd.DataFrame(data['data'], columns=data['columns'], dtype=str)


@contextmanager
def workspace():
    path = workdir()
    with _locks[int(path.name, 16) % len(_locks)]:
        now = time.time()
        if path.exists() and now-path.stat().st_mtime > TTL:
            shutil.rmtree(path)
        path.mkdir(mode=0o700, exist_ok=True)
        os.utime(path, None)
        yield path


def cleanup():
    now = time.time()
    for path in root().iterdir():
        if path.is_dir() and len(path.name) == 64 and all(c in '0123456789abcdef' for c in path.name):
            with _locks[int(path.name, 16) % len(_locks)]:
                if path.exists() and now-path.stat().st_mtime > TTL:
                    shutil.rmtree(path)


@bp.before_request
def protect():
    if 'cruzamento_csrf' not in session:
        session['cruzamento_csrf'] = secrets.token_hex(32)
    if request.method == 'POST':
        # Limite específico do novo módulo, sem mudar uploads antigos.
        if request.content_length and request.content_length > 25*1024*1024:
            abort(413, description='Envie arquivos de até 25 MB.')
        if not secrets.compare_digest(request.form.get('csrf', ''), session['cruzamento_csrf']):
            abort(
                400, description='A sessão mudou. Recarregue a página antes de continuar.')


@bp.route('/', methods=['GET', 'POST'])
def index():
    cleanup()
    with workspace() as folder:
        state_path = folder/'state.json'
        state = json.loads(state_path.read_text(
            encoding='utf-8')) if state_path.exists() else {'steps': []}
        if request.method == 'POST':
            try:
                action = request.form.get('action')
                if action == 'finish':
                    shutil.rmtree(folder)
                    session.pop('cruzamento_id', None)
                    flash(
                        'Análise encerrada. Arquivos temporários excluídos.', 'success')
                    return redirect(url_for('cruzamento.index'))
                if action == 'upload':
                    file = request.files.get('file')
                    ext = Path(
                        file.filename or '').suffix.lower() if file else ''
                    if ext not in ('.xlsx', '.xls', '.csv'):
                        raise ValueError(
                            'Selecione um arquivo XLSX, XLS ou CSV.')
                    target = folder/('upload-'+secrets.token_hex(8)+ext)
                    file.save(target)
                    try:
                        if ext == '.xlsx':
                            with zipfile.ZipFile(target) as z:
                                if sum(i.file_size for i in z.infolist()) > 150*1024*1024:
                                    raise ValueError(
                                        'O conteúdo descompactado excede o limite de 150 MB.')
                        if ext == '.csv':
                            sheets = ['CSV']
                        else:
                            with pd.ExcelFile(target) as book:
                                sheets = book.sheet_names
                        if state.get('pending'):
                            (folder/state['pending']['path']
                             ).unlink(missing_ok=True)
                        state['pending'] = {
                            'path': target.name, 'name': file.filename, 'sheets': sheets, 'sheet': sheets[0], 'header': 1}
                    except Exception:
                        target.unlink(missing_ok=True)
                        raise
                elif action == 'preview':
                    pending = state.get('pending')
                    if not pending:
                        raise ValueError('Envie uma planilha primeiro.')
                    sheet = request.form.get('sheet')
                    if sheet not in pending['sheets']:
                        raise ValueError('Escolha uma aba válida.')
                    header = int(request.form.get('header', 1))
                    df = read_table(
                        folder/pending['path'], sheet=sheet if sheet != 'CSV' else 0, header=header)
                    save_frame(folder/'source.json', df)
                    pending.update(sheet=sheet, header=header, ready=True)
                elif action in ('base', 'merge'):
                    pending = state.get('pending')
                    if not pending or not pending.get('ready'):
                        raise ValueError(
                            'Confira a prévia da planilha primeiro.')
                    source = load_frame(folder/'source.json')
                    if action == 'base':
                        if (folder/'result.json').exists():
                            raise ValueError(
                                'Encerre a análise atual antes de escolher outra base.')
                        save_frame(folder/'result.json', source)
                        state['base'] = pending['name']
                    else:
                        base = load_frame(folder/'result.json')
                        pairs = [(request.form.get(f'left{i}', ''), request.form.get(
                            f'right{i}', '')) for i in range(3)]
                        if any(bool(a) != bool(b) for a, b in pairs):
                            raise ValueError(
                                'Preencha os dois lados de cada par de chaves.')
                        pairs = [(a, b) for a, b in pairs if a and b]
                        result, stats = merge_tables(base, source, [a for a, b in pairs], [b for a, b in pairs], request.form.getlist(
                            'columns'), request.form.get('label', ''), request.form.get('policy', 'error'))
                        save_frame(folder/'result.json', result)
                        state['steps'].append(stats)
                        flash(
                            f"Cruzamento concluído: {stats['encontradas']} linhas encontradas e {stats['sem_correspondencia']} sem correspondência.", 'success')
                    (folder/pending['path']).unlink(missing_ok=True)
                    (folder/'source.json').unlink(missing_ok=True)
                    state.pop('pending', None)
                else:
                    raise ValueError('Ação inválida.')
                save_json(state_path, state)
                return redirect(url_for('cruzamento.index'))
            except (ValueError, KeyError, OSError, zipfile.BadZipFile) as exc:
                flash(str(exc), 'danger')
            except Exception:
                current_app.logger.exception('Erro no cruzamento de planilhas')
                flash(
                    'Não foi possível ler ou cruzar o arquivo. Confira o formato e os títulos das colunas.', 'danger')
        base = load_frame(folder/'result.json') if (folder /
                                                    'result.json').exists() else None
        source = load_frame(folder/'source.json') if state.get('pending',
                                                               {}).get('ready') and (folder/'source.json').exists() else None
        return render_template('cruzamento.html', state=state, base=base, source=source)


@bp.get('/baixar')
def download():
    with workspace() as folder:
        if not (folder/'result.json').exists():
            flash('A análise expirou ou ainda não foi criada.', 'warning')
            return redirect(url_for('cruzamento.index'))
        df = load_frame(folder/'result.json')
        for col in request.args.getlist('numeric'):
            if col not in df:
                abort(400, description='Coluna numérica inválida.')
            values = df[col].map(lambda v: str(v).strip())
            if not values.map(lambda v: v == '' or bool(re.fullmatch(r'(?:0|[1-9][0-9]{0,14})', v))).all():
                flash(
                    f'A coluna {col} contém valores que não podem ser convertidos sem perda. Mantenha-a como texto.', 'warning')
                return redirect(url_for('cruzamento.index'))
            df[col] = values.map(lambda v: int(
                v) if v else None).astype(object)
        state = json.loads((folder/'state.json').read_text(encoding='utf-8'))
        output = BytesIO()
        # Evita interpretar conteúdo de células como fórmulas ou links executáveis.
        with pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={'options': {'strings_to_formulas': False, 'strings_to_urls': False}}) as writer:
            df.to_excel(writer, sheet_name='Resultado', index=False)
            ws = writer.sheets['Resultado']
            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, len(df), len(df.columns)-1)
            ws.set_column(0, len(df.columns)-1, 24)
            if state['steps']:
                pd.DataFrame(state['steps']).to_excel(
                    writer, sheet_name='Cruzamentos', index=False)
        output.seek(0)
    return send_file(output, as_attachment=True, download_name='Cruzamento_planilhas.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


def init_app(app):
    app.register_blueprint(bp)

    @app.cli.command('limpar-cruzamentos')
    def clean_command():
        """Remove sessões expiradas; pode ser executado por agendador do servidor."""
        cleanup()
