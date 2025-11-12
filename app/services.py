from flask import render_template, redirect, url_for, current_app
import os
import subprocess
import json 
import locale


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
        
        
   
    return redirect(url_for('rotas.iniciar'))


def login():
    return render_template('login.html')