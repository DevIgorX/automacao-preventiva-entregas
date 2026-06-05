from flask import  request, Blueprint, render_template

from .services import iniciar_app , deletar_dados, login, baixar_relatorio, pagina_analise_preventiva , adicionar_arquivo, analisar_preventiva , excluir_arquivos , baixar_preventiva, conferencia_arquivos , pagina_consulta , alimentar_base_dados , processar_consulta_lote

rotas = Blueprint('rotas', __name__)



@rotas.route('/')
def pagina_inicial():
    return render_template('dashboard.html')

@rotas.route('/performance', methods=['GET', 'POST'])
def analise_performance():
    return iniciar_app(request)


# Esta rota agora é opcional, mas podemos mantê-la para o caso de acesso direto
@rotas.route('/resultado')
def resultado():
    # Como não temos mais dados, mostramos uma mensagem
    return "<h1>Resultado da Análise</h1><p>Por favor, envie os arquivos na <a href='/'>página inicial</a> para ver um relatório.</p>"


@rotas.route('/excluir_dados')
def excluir_dados():
    return deletar_dados()


@rotas.route('/login')
def executar_login():
    return login()


@rotas.route('/download/relatorio')
def download_relatorio_excel():
    return baixar_relatorio()


@rotas.route('/pagina_analise')
def pagina_analise():
    return pagina_analise_preventiva()

@rotas.route('/adicionar_dados', methods=['POST'])
def adicionar_dados():
    return adicionar_arquivo(request)
   
@rotas.route('/analisar_dados')
def analisar_dados():
    return analisar_preventiva(request)

@rotas.route('/limpar_arquivos')
def limpar_arquivo():
    return excluir_arquivos()

@rotas.route('/baixar_relatorio_preventiva')
def baixar_relatorio_preventiva():
    return baixar_preventiva()

@rotas.route('/conferencia_arquivos')
def conferencia_qtd_arquivos():
    return conferencia_arquivos()


@rotas.route('/consulta_pedido', methods=['GET', 'POST'])
def rota_consulta():
    return pagina_consulta(request)



# 1. ROTA DE ALIMENTAÇÃO DA BASE
@rotas.route('/alimentar_base', methods=['GET', 'POST'])
def rota_alimentar_base():
    
    if request.method == 'POST':
        return alimentar_base_dados(request)
    
    
    return render_template('alimentar_base.html')


# 2. ROTA DE CONSULTA EM LOTE
@rotas.route('/consulta_lote', methods=['GET', 'POST'])
def rota_consulta_lote():
    """
    Página onde você sobe apenas o arquivo principal com a lista de pedidos (ex: Preventiva).
    O sistema vai ler os pedidos, consultar o banco e retornar o Excel cruzado.
    """
    if request.method == 'POST':
        # Redireciona a requisição para fazer a consulta SQL
        return processar_consulta_lote(request)
    
    # Se for GET, mostra a página para enviar o arquivo de pedidos
    # (Você precisará criar ou adaptar um template HTML para esta página)
    return render_template('consulta_lote.html')