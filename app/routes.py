from flask import render_template, request, redirect, url_for, Blueprint, current_app
import os
import subprocess
import json # Importe a biblioteca JSON aqui também

rotas = Blueprint('rotas', __name__)

@rotas.route('/', methods=['GET', 'POST'])
def iniciar():
    if request.method == 'POST':
        # ... (seu código para checar e salvar os arquivos permanece o mesmo)
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
        
        # O resultado agora terá o JSON em stdout e os logs em stderr
        resultado = subprocess.run(['python', caminho_analise], capture_output=True, text=True, encoding='utf-8')
        
        # Se o script falhou, mostre o erro
        if resultado.returncode != 0:
            return f"<h1>Ocorreu um erro ao processar os arquivos:</h1><pre>{resultado.stderr}</pre>"
        
        # Carrega a string JSON para um dicionário Python
        try:
            dados_analise = json.loads(resultado.stdout)
        except json.JSONDecodeError:
            return f"<h1>Erro ao ler o resultado da análise.</h1><pre>Saída recebida: {resultado.stdout}</pre><pre>Logs: {resultado.stderr}</pre>"


        # Em vez de redirecionar, renderiza a página de resultado diretamente com os dados
        return render_template('resultado.html', data=dados_analise)

    # Se for GET, apenas mostra a página de upload
    return render_template('index.html')

# Esta rota agora é opcional, mas podemos mantê-la para o caso de acesso direto
@rotas.route('/resultado')
def resultado():
    # Como não temos mais dados, mostramos uma mensagem
    return "<h1>Resultado da Análise</h1><p>Por favor, envie os arquivos na <a href='/'>página inicial</a> para ver um relatório.</p>"


@rotas.route('/excluir_dados')
def excluir_dados():
    pasta_dados = current_app.config['UPLOAD_FOLDER']
    arquivo_gitkeep = current_app.config['GITKEEP']
    for arquivo in os.listdir(pasta_dados):
        caminho_arquivo = os.path.join(pasta_dados, arquivo)
        if caminho_arquivo != arquivo_gitkeep:
            os.remove(caminho_arquivo)
        
        
   
    return redirect('/')