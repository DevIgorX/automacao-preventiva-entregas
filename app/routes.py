from flask import render_template, request, redirect, url_for, Blueprint
import os
import subprocess
from main import app


# Pega o caminho absoluto do script atual (main.py)
caminho_script = os.path.abspath(__file__)
# Pega o diretório do script (pasta 'app')
diretorio_app = os.path.dirname(caminho_script)
# Sobe um nível para chegar na pasta raiz do projeto
diretorio_raiz = os.path.dirname(diretorio_app)
# Define o caminho para a pasta de dados
caminho_dados = os.path.join(diretorio_raiz, 'dados')

# Configura a pasta de upload
app.config['UPLOAD_FOLDER'] = caminho_dados

rotas = Blueprint('rotas', __name__)

@rotas.route('/', methods=['GET', 'POST'])
def iniciar():
    if request.method == 'POST':
        # Verifica se os arquivos foram enviados
        if 'preventiva' not in request.files or 'relatorio' not in request.files:
            return "Erro: Ambos os arquivos são necessários."

        arquivo_preventiva = request.files['preventiva']
        arquivo_relatorio = request.files['relatorio']

        # Verifica se os nomes dos arquivos não estão vazios
        if arquivo_preventiva.filename == '' or arquivo_relatorio.filename == '':
            return "Erro: Nomes de arquivos não podem ser vazios."

        # Salva os arquivos na pasta 'dados'
        arquivo_preventiva.save(os.path.join(app.config['UPLOAD_FOLDER'], arquivo_preventiva.filename))
        arquivo_relatorio.save(os.path.join(app.config['UPLOAD_FOLDER'], arquivo_relatorio.filename))

        # Executa o script de análise e captura a saída
        caminho_analise = os.path.join(diretorio_raiz, 'analise', 'analise_entregas.py')
        resultado = subprocess.run(['python', caminho_analise], capture_output=True, text=True)
        
        # Passa a saída para a página de resultados
        return redirect(url_for('resultado', saida=resultado.stdout))

    return render_template('index.html')

@rotas.route('/resultado')
def resultado():
    saida = request.args.get('saida', '')
    return render_template('resultado.html', saida=saida)
