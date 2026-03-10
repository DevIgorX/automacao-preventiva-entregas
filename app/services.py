from flask import render_template, redirect, url_for, current_app , send_from_directory, flash
import os
import subprocess
import json 
import locale
from datetime import datetime
from .helpers import FormularioLogin
from db.db_preventiva import buscar_dados_paginados


def iniciar_app(request):
    if request.method == 'POST':
        
        if 'preventiva' not in request.files or 'relatorio' not in request.files:
            return "Erro: Ambos os arquivos são necessários."

        arquivo_preventiva = request.files['preventiva']
        arquivo_relatorio = request.files['relatorio']

        if arquivo_preventiva.filename == '' or arquivo_relatorio.filename == '':
            return "Erro: Nomes de arquivos não podem ser vazios."

        pasta_upload = current_app.config['UPLOAD_FOLDER']
        
        arquivo_preventiva.save(os.path.join(pasta_upload, arquivo_preventiva.filename))
        arquivo_relatorio.save(os.path.join(pasta_upload, arquivo_relatorio.filename))

        diretorio_raiz_da_config = current_app.config['ROOT_DIR']
        caminho_analise = os.path.join(diretorio_raiz_da_config, 'analise', 'analise_entregas.py')
        #localizar o encoding padrão, utf-8 ou latim-1
        encoding_padrao = locale.getpreferredencoding(False)
        # O resultado agora terá o JSON em stdout e os logs em stderr
        resultado = subprocess.run(['python', caminho_analise], capture_output=True, text=True, encoding=encoding_padrao)
        
       # --- ESTA É A MUDANÇA PRINCIPAL ---
        # Se o script falhou (returncode != 0), renderiza a página de erro
        if resultado.returncode != 0:
            # O resultado.stderr conterá as mensagens de erro do seu script
            return render_template('erro.html', erro=resultado.stderr)
        
        # Carrega a string JSON para um dicionário Python
        try:
            dados_analise = json.loads(resultado.stdout)
        except json.JSONDecodeError:
            # Se o JSON falhar, também renderiza a página de erro
            mensagem_erro_json = f"Erro ao processar arquivo. \n\nLogs: {resultado.stderr}\n\nSaída: {resultado.stdout}"
            return render_template('erro.html', erro=mensagem_erro_json)

        # Se tudo deu certo, mostra a página de resultado
        return render_template('resultado.html', data=dados_analise)

    # Se for GET, apenas mostra a página de upload
    return render_template('index.html')

def deletar_dados():
    pasta_dados = current_app.config['UPLOAD_FOLDER']
    arquivo_gitkeep = current_app.config['GITKEEP']
    for arquivo in os.listdir(pasta_dados):
        caminho_arquivo = os.path.join(pasta_dados, arquivo)
        if caminho_arquivo != arquivo_gitkeep:
            os.remove(caminho_arquivo)
        
        
   
    return redirect(url_for('rotas.analise_performance'))


# ADICIONE ESTA NOVA FUNÇÃO NO FINAL DO ARQUIVO:
def baixar_relatorio():
    # Pega o caminho da pasta 'dados' a partir da configuração
    pasta_dados = current_app.config['UPLOAD_FOLDER']
    
    # Pega o nome do arquivo que o script de análise gera
    nome_arquivo = 'Resultado_Monitoramento.xlsx'
    
    # Usa a função segura do Flask para enviar o arquivo
    # as_attachment=True força o navegador a baixar o arquivo em vez de tentar exibi-lo
    return send_from_directory(pasta_dados, nome_arquivo, as_attachment=True)


def login():

    form = FormularioLogin()
    return render_template('login.html', form=form)

def pagina_analise_preventiva():
    pasta_dados = current_app.config['UPLOAD_FOLDER']

    arquivos_no_servidor = []

    if os.path.exists(pasta_dados):
        for arquivo in os.listdir(pasta_dados):
            if arquivo != '.gitkeep':
                arquivos_no_servidor.append(arquivo)

    return render_template('analise_dataframes.html', arquivos_presentes=arquivos_no_servidor)


def adicionar_arquivo(request):
    arquivos = request.files.getlist('arquivos')

    if not arquivos:
        flash("Nenhum arquivo enviado!","danger")
        return redirect(url_for('rotas.pagina_analise'))

    pasta_dados = current_app.config['UPLOAD_FOLDER']

    arquivos_pulados = []
    for arquivo in arquivos:
        caminho_completo = os.path.join(pasta_dados, arquivo.filename)

        if os.path.exists(caminho_completo):
            arquivos_pulados.append(caminho_completo)
            continue

        arquivo.save(caminho_completo)
    
    if arquivos_pulados:
        flash(f"Atenção! O arquivo já estava no servidor e foi ignorado: {', '.join(arquivos_pulados)}", "warning") # flash(mensagem, categoria)"warning" → cor amarelo (atenção)
    else:
        flash("Arquivo enviado com sucesso!", "success") #success cor verde
    
    return redirect(url_for('rotas.pagina_analise'))


def analisar_preventiva(request):
    pagina = request.args.get('pagina', 1, type=int)
    processar = request.args.get('processar', 'false').lower() == 'true'

    if processar:
        diretorio_raiz = current_app.config['ROOT_DIR']
        pasta_analise = os.path.join(diretorio_raiz, 'analise') 
        caminho_script = os.path.join(pasta_analise, 'analise_preventiva.py')
        encoding_padrao = locale.getpreferredencoding(False)
        
       
        resultado = subprocess.run(['python', caminho_script], capture_output=True, text=True, encoding=encoding_padrao)

        if resultado.returncode != 0:
            return render_template('erro.html', erro=resultado.stderr)

    itens_por_pg = 7
    try:
        lista_dados, total_itens = buscar_dados_paginados(pagina, itens_por_pg)
    except Exception as e:
        
        return render_template('erro.html', erro=f"Erro ao buscar dados: {e}")
    
    total_paginas = (total_itens + itens_por_pg - 1) // itens_por_pg

    dados_formatados = {
        "Excel": lista_dados,
        "pagina_atual": pagina,
        "total_paginas": total_paginas
    }

    return render_template('resultado_preventiva.html', dados=dados_formatados)

def excluir_arquivos():
    pasta_dados = current_app.config['UPLOAD_FOLDER']

    for arquivo in os.listdir(pasta_dados):
        caminho_arquivo = os.path.join(pasta_dados, arquivo)
        if arquivo != '.gitkeep':
            os.remove(caminho_arquivo)
    
    return redirect(url_for('rotas.pagina_analise'))
       
def baixar_preventiva():
    pasta_dados = current_app.config['UPLOAD_FOLDER']

    data_hoje = datetime.today().strftime('%d-%m-%Y')
    nome_arquivo = f'Analise_preventiva {data_hoje}.xlsx'

    return send_from_directory(pasta_dados, nome_arquivo, as_attachment=True)