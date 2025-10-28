from flask import  request, Blueprint

from services import (iniciar_app , deletar_dados)

rotas = Blueprint('rotas', __name__)

@rotas.route('/', methods=['GET', 'POST'])
def iniciar():
    return iniciar_app(request)
 
# Esta rota agora é opcional, mas podemos mantê-la para o caso de acesso direto
@rotas.route('/resultado')
def resultado():
    # Como não temos mais dados, mostramos uma mensagem
    return "<h1>Resultado da Análise</h1><p>Por favor, envie os arquivos na <a href='/'>página inicial</a> para ver um relatório.</p>"


@rotas.route('/excluir_dados')
def excluir_dados():
    return deletar_dados()
   