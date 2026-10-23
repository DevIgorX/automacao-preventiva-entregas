"""Envio guiado da preventiva, separado das regras de cruzamento."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile

import pandas as pd
from analise.tratamento_bipe_produtos import encontrar_aba_bipe
from flask import abort, current_app, flash, redirect, render_template, request, send_file, session, url_for


# Nomes internos compatíveis com o processamento existente.
RELATORIOS = {
    'preventiva': {'titulo': 'Preventiva', 'nome': 'Preventiva',
        'colunas': ['Pedido 1P/Full', 'Cidade_Cliente', 'Data_Vencimento']},
    'carreta': {'titulo': 'Entrada de Carreta', 'nome': 'Carreta',
        'colunas': ['Pedido', 'Nf`S', 'Chave', 'Data Entrada', 'Tipo_Fluxo']},
    'esl': {'titulo': 'Relatório ESL', 'nome': 'magazine',
        'colunas': ['Nota Fiscal/Chave Nf-E', 'Última Ocorrência/Observações',
                    'Pessoa/Nome', 'Última Ocorrência/Data Ocorrência', 'Ocorrência/Ocorrência']},
    'mobile': {'titulo': 'Mobile Entregas', 'nome': 'Mobile',
        'colunas': ['Pedido', 'Nota Fiscal', 'Tipo', 'Entregador']},
    'produtos': {'titulo': 'Bipe de produtos', 'nome': 'bipe_produtos',
        'colunas': ['Pedido', 'Status_Deposito']},
    'notas': {'titulo': 'Bipe de notas', 'nome': 'Bipe_de_notas',
        'colunas': ['Nf', 'Ocorrencia']},
}
MAX_BYTES = 25 * 1024 * 1024


def pasta_sessao():
    sid = session.get('preventiva_envio_id', '')
    if len(sid) != 64 or any(c not in '0123456789abcdef' for c in sid):
        sid = secrets.token_hex(32)
        session['preventiva_envio_id'] = sid
    raiz = Path(current_app.config.get('PREVENTIVA_TEMP_DIR',
        Path(tempfile.gettempdir()) / 'preventiva-automatica'))
    pasta = raiz / sid
    pasta.mkdir(parents=True, exist_ok=True)
    session.setdefault('preventiva_envio_csrf', secrets.token_hex(32))
    return pasta


def carregar(pasta):
    path = pasta / 'estado.json'
    estado = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    estado.setdefault('recebidos', {})
    return estado


def salvar(pasta, estado):
    temporario = pasta / 'estado.tmp'
    temporario.write_text(json.dumps(estado, ensure_ascii=False), encoding='utf-8')
    temporario.replace(pasta / 'estado.json')


def conferir_csrf():
    esperado = session.get('preventiva_envio_csrf', '')
    if not esperado or not secrets.compare_digest(esperado, request.form.get('csrf', '')):
        abort(400, 'A página expirou. Atualize a tela e tente novamente.')


@contextmanager
def uso_exclusivo(pasta):
    """Impede substituições enquanto esta análise está sendo executada."""
    lock = pasta / '.ocupado'
    # O sistema operacional libera o bloqueio mesmo se o processo for encerrado.
    with lock.open('a+b') as arquivo:
        arquivo.seek(0, os.SEEK_END)
        if arquivo.tell() == 0:
            arquivo.write(b'0')
            arquivo.flush()
        arquivo.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError('Esta análise está sendo preparada. Aguarde a conclusão e tente novamente.') from exc
        try:
            yield
        finally:
            arquivo.seek(0)
            if os.name == 'nt':
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(arquivo.fileno(), fcntl.LOCK_UN)


def pagina():
    pasta = pasta_sessao()
    estado = carregar(pasta)
    return render_template('analise_dataframes.html', relatorios=RELATORIOS,
        estado=estado, completos=len(estado['recebidos']) == len(RELATORIOS))


def encontrar_aba(path, tipo, aba_escolhida=''):
    """Valida os títulos sem converter as células nem alterar o arquivo original."""
    esperadas = set(RELATORIOS[tipo]['colunas'])
    try:
        if tipo == 'produtos':
            return encontrar_aba_bipe(path, aba_escolhida)
        with pd.ExcelFile(path) as livro:
            abas = [aba_escolhida] if aba_escolhida else livro.sheet_names
            if aba_escolhida and aba_escolhida not in livro.sheet_names:
                raise ValueError('Escolha uma aba existente neste arquivo.')
            candidatas = []
            menores_faltas = None
            for aba in abas:
                amostra = pd.read_excel(livro, sheet_name=aba, nrows=1, dtype=object)
                colunas = {str(c).strip().lower().title() for c in amostra.columns}
                faltas = esperadas - colunas
                if menores_faltas is None or len(faltas) < len(menores_faltas):
                    menores_faltas = faltas
                if not faltas:
                    if amostra.empty:
                        continue
                    candidatas.append(aba)
            if len(candidatas) == 1:
                return candidatas[0]
            if len(candidatas) > 1:
                raise ValueError('Há mais de uma aba compatível. Escolha a aba que deseja usar.')
            if menores_faltas:
                raise ValueError('Este arquivo não tem as colunas esperadas para '
                    f"{RELATORIOS[tipo]['titulo']}. Faltam: {', '.join(sorted(menores_faltas))}. "
                    'Confira o arquivo ou escolha outro tipo de relatório.')
            raise ValueError('A aba está vazia. Envie um relatório com dados.')
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('Não foi possível ler esta planilha. Confira se ela abre no Excel e não tem senha.') from exc


def invalidar_resultado(pasta, estado):
    estado.pop('resultado', None)
    shutil.rmtree(pasta / 'saida', ignore_errors=True)


def receber_arquivo(pasta, estado):
    arquivos = [a for a in request.files.getlist('arquivos') if a.filename]
    if len(arquivos) != 1:
        raise ValueError('Selecione um arquivo por vez.')
    substituir = request.form.get('substituir', '')
    if substituir and substituir not in estado['recebidos']:
        raise ValueError('O relatório a substituir não está mais disponível. Atualize a página.')
    if not substituir and len(estado['recebidos']) == len(RELATORIOS):
        raise ValueError('Os seis relatórios já foram enviados. Use o botão Substituir arquivo.')
    arquivo = arquivos[0]
    nome = arquivo.filename.replace('\\', '/').split('/')[-1]
    extensao = Path(nome).suffix.lower()
    if extensao not in ('.xlsx', '.xls'):
        raise ValueError('Envie uma planilha Excel no formato XLSX ou XLS.')
    destino = pasta / ('pendente-' + secrets.token_hex(16) + extensao)
    try:
        with destino.open('wb') as saida:
            total = 0
            while bloco := arquivo.stream.read(1024 * 1024):
                total += len(bloco)
                if total > MAX_BYTES:
                    raise ValueError('O arquivo ultrapassa 25 MB. Envie uma planilha menor.')
                saida.write(bloco)
        try:
            with pd.ExcelFile(destino) as livro:
                abas = livro.sheet_names
        except Exception as exc:
            raise ValueError('Não foi possível abrir esta planilha. Confira se ela abre no Excel e não tem senha.') from exc
        anterior = estado.get('pendente')
        estado['pendente'] = {'arquivo': destino.name, 'original': nome,
            'abas': abas, 'substituir': substituir, 'token': secrets.token_hex(16)}
        salvar(pasta, estado)
        if anterior:
            (pasta / anterior['arquivo']).unlink(missing_ok=True)
    except Exception:
        destino.unlink(missing_ok=True)
        raise


def confirmar_tipo(pasta, estado):
    pendente = estado.get('pendente')
    if not pendente or request.form.get('pendente') != pendente['token']:
        raise ValueError('Este envio já mudou. Confira o arquivo exibido na página.')
    tipo = request.form.get('tipo', '')
    if tipo not in RELATORIOS:
        raise ValueError('Selecione qual relatório você está enviando.')
    substituindo = pendente['substituir']
    if substituindo and tipo != substituindo:
        raise ValueError('Confirme o mesmo tipo do relatório que você está substituindo.')
    if tipo in estado['recebidos'] and tipo != substituindo:
        raise ValueError('Este relatório já foi enviado. Use Substituir arquivo para trocá-lo.')
    origem = pasta / pendente['arquivo']
    aba = encontrar_aba(origem, tipo, request.form.get('aba', ''))
    entrada = pasta / 'entrada'
    entrada.mkdir(exist_ok=True)
    nome = RELATORIOS[tipo]['nome'] + origem.suffix
    anterior = estado['recebidos'].get(tipo)
    origem.replace(entrada / nome)
    if anterior and anterior['arquivo'] != nome:
        (entrada / anterior['arquivo']).unlink(missing_ok=True)
    estado['recebidos'][tipo] = {'arquivo': nome, 'original': pendente['original'], 'aba': aba}
    estado.pop('pendente')
    invalidar_resultado(pasta, estado)
    salvar(pasta, estado)
    flash(f"{RELATORIOS[tipo]['titulo']}: arquivo recebido.", 'success')


def acao_upload():
    pasta = pasta_sessao()
    conferir_csrf()
    try:
        with uso_exclusivo(pasta):
            estado = carregar(pasta)
            acao = request.form.get('acao', 'enviar')
            if acao == 'enviar':
                receber_arquivo(pasta, estado)
            elif acao == 'confirmar':
                confirmar_tipo(pasta, estado)
            elif acao == 'cancelar':
                pendente = estado.pop('pendente', None)
                if pendente:
                    (pasta / pendente['arquivo']).unlink(missing_ok=True)
                salvar(pasta, estado)
            else:
                raise ValueError('Escolha uma ação válida.')
    except ValueError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('rotas.pagina_analise'))


def nova_analise():
    # Links antigos do menu apenas abrem a tela; apagar exige o botão do formulário.
    if request.method == 'POST':
        pasta = pasta_sessao()
        conferir_csrf()
        try:
            with uso_exclusivo(pasta):
                for path in pasta.iterdir():
                    if path.name == '.ocupado':
                        continue
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                salvar(pasta, {'recebidos': {}})
            flash('Tudo pronto para uma nova análise.', 'success')
        except ValueError as exc:
            flash(str(exc), 'warning')
    return redirect(url_for('rotas.pagina_analise'))


def executar():
    pasta = pasta_sessao()
    conferir_csrf()
    try:
        with uso_exclusivo(pasta):
            estado = carregar(pasta)
            faltando = [info['titulo'] for tipo, info in RELATORIOS.items()
                if tipo not in estado['recebidos'] or
                not (pasta / 'entrada' / estado['recebidos'][tipo]['arquivo']).is_file()]
            if faltando:
                raise ValueError('Antes de analisar, envie: ' + ', '.join(faltando) + '.')
            if estado.get('pendente'):
                raise ValueError('Confirme ou cancele o arquivo pendente antes de iniciar a análise.')
            invalidar_resultado(pasta, estado)
            salvar(pasta, estado)
            saida = pasta / 'saida'
            saida.mkdir(exist_ok=True)
            manifesto = pasta / 'entrada' / 'envio.json'
            manifesto.write_text(json.dumps(estado['recebidos'], ensure_ascii=False), encoding='utf-8')
            ambiente = os.environ.copy()
            ambiente.update(PREVENTIVA_INPUT_DIR=str(pasta / 'entrada'),
                PREVENTIVA_OUTPUT_DIR=str(saida), PYTHONIOENCODING='utf-8')
            script = Path(current_app.config['ROOT_DIR']) / 'analise' / 'analise_preventiva.py'
            resultado = subprocess.run([sys.executable, str(script)], capture_output=True,
                text=True, encoding='utf-8', errors='replace', env=ambiente,
                timeout=current_app.config.get('PREVENTIVA_TIMEOUT', 300))
            if resultado.returncode:
                current_app.logger.error('Falha na preventiva: %s\n%s', resultado.stdout, resultado.stderr)
                raise ValueError('Não foi possível concluir a análise. Os arquivos enviados foram mantidos. '
                    'Confira os dados das planilhas e tente novamente.')
            arquivos = list(saida.glob('Analise_preventiva *.xlsx'))
            if len(arquivos) != 1:
                raise ValueError('O relatório não foi gerado. Tente executar a análise novamente.')
            estado['resultado'] = arquivos[0].name
            salvar(pasta, estado)
    except subprocess.TimeoutExpired:
        flash('A análise demorou mais que o esperado. Os arquivos foram mantidos para tentar novamente.', 'danger')
        return redirect(url_for('rotas.pagina_analise'))
    except ValueError as exc:
        flash(str(exc), 'danger')
        return redirect(url_for('rotas.pagina_analise'))
    return redirect(url_for('rotas.analisar_dados'))


def caminho_resultado():
    pasta = pasta_sessao()
    nome = carregar(pasta).get('resultado')
    path = pasta / 'saida' / nome if nome else None
    return path if path and path.is_file() else None


def resultado_pagina():
    path = caminho_resultado()
    if path is None:
        flash('Envie os relatórios e inicie a análise para ver o resultado.', 'info')
        return redirect(url_for('rotas.pagina_analise'))
    df = pd.read_excel(path, dtype=object).fillna('')
    total_paginas = max(1, (len(df) + 4) // 5)
    pagina_atual = min(max(1, request.args.get('pagina', 1, type=int)), total_paginas)
    inicio = (pagina_atual - 1) * 5
    return render_template('resultado_preventiva.html', preventiva_guiada=True, dados={
        'Excel': df.iloc[inicio:inicio + 5].to_dict(orient='records'),
        'pagina_atual': pagina_atual, 'total_paginas': total_paginas})


def baixar():
    path = caminho_resultado()
    if path is None:
        flash('Faça a análise antes de baixar o relatório.', 'warning')
        return redirect(url_for('rotas.pagina_analise'))
    return send_file(path, as_attachment=True, download_name=path.name)
