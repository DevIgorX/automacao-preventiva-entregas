import os

from dotenv import load_dotenv

load_dotenv() #Carrega as variáveis do arquivo .env


# Pega o caminho absoluto do script atual (main.py)
caminho_script = os.path.abspath(__file__)
# Pega o diretório do script (pasta 'app')
diretorio_app = os.path.dirname(caminho_script)
# Sobe um nível para chegar na pasta raiz do projeto
diretorio_raiz = os.path.dirname(diretorio_app)
# Define o caminho para a pasta de dados
caminho_dados = os.path.join(diretorio_raiz, 'dados')
arquivo_gitkeep = os.path.abspath(os.path.join(caminho_dados,'.gitkeep'))

SECRET_KEY = os.getenv('SECRET_KEY', 'chave-padrao-insegura') # Valor padrão apenas para evitar erros locais se esquecer o .env
DEBUG = os.getenv('FLASK_DEBUG', '0') == '1' # Converte string '1' para boolean True

UPLOAD_FOLDER = caminho_dados
ROOT_DIR = diretorio_raiz
GITKEEP = arquivo_gitkeep







