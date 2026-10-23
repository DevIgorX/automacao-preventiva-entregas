from flask import render_template, redirect, url_for, current_app , send_from_directory, flash
import os
import subprocess
import json 
import locale
from datetime import datetime
from .helpers import FormularioLogin
from db.db_preventiva import buscar_dados_paginados , buscar_pedido_historico 

from analise.alimentador import processar_e_salvar_tabela
from analise.consultas import extrair_pedidos_e_consultar


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
        return render_template('resultado_performance.html', data=dados_analise)

    # Se for GET, apenas mostra a página de upload
    return render_template('analise_performance.html')

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

# O envio guiado fica separado das regras de negócio e dos demais módulos.
def pagina_analise_preventiva():
    from .preventiva_uploads import pagina
    return pagina()


def adicionar_arquivo(request):
    from .preventiva_uploads import acao_upload
    return acao_upload()


def conferencia_arquivos():
    # Endereço antigo: o processamento agora é iniciado pelo formulário POST.
    return redirect(url_for('rotas.pagina_analise'))


def analisar_preventiva(request):
    from .preventiva_uploads import executar, resultado_pagina
    if request.method == 'POST':
        return executar()
    return resultado_pagina()


def excluir_arquivos():
    from .preventiva_uploads import nova_analise
    return nova_analise()


def baixar_preventiva():
    from .preventiva_uploads import baixar
    return baixar()


def pagina_consulta(request):
    resultados = []
    pedido_id = ""
    if request.method == 'POST':
        pedido_id = request.form.get('pedido')
        print(f'pedido recebido na rota: {pedido_id}')
        if pedido_id:
            resultados = buscar_pedido_historico(pedido_id)
        
        print('resultado da função:')
        print(resultados)
            
    return render_template('consulta.html', resultados=resultados, pedido_procurado=pedido_id)

#1 Alimentar base de dados

def alimentar_base_dados(request):
    """Gerencia o upload de arquivos via formulário e chama o processador."""
    
    arquivos_enviados = request.files.getlist('arquivos')
    
    if not arquivos_enviados or arquivos_enviados[0].filename == '':
        flash("Nenhum arquivo selecionado.", "danger")
        return redirect(url_for('rotas.rota_alimentar_base'))

    for arquivo in arquivos_enviados:
        nome_arquivo = arquivo.filename
        
        # Chama a função externa que lida com o Pandas e Banco de Dados
        tabela_atualizada = processar_e_salvar_tabela(arquivo, nome_arquivo)
        print(tabela_atualizada)
        
        if tabela_atualizada:
            flash(f"Base {tabela_atualizada} atualizada com sucesso!", "success")
        else:
            flash(f"Arquivo '{nome_arquivo}' ignorado (tipo não reconhecido).", "warning")

    return redirect(url_for('rotas.rota_alimentar_base'))

#2 alteração
def processar_consulta_lote(request):
    """Recebe o arquivo do formulário web e delega a consulta para o Pandas."""
    
    arquivo_pedidos = request.files.get('arquivo_pedidos')
    
    if not arquivo_pedidos or arquivo_pedidos.filename == '':
        flash("Nenhum arquivo enviado para consulta.", "danger")
        return redirect(url_for('rotas.rota_consulta_lote'))

    # Delega o trabalho pesado: O Pandas e o Banco de Dados rodam aqui
    dados_cruzados = extrair_pedidos_e_consultar(arquivo_pedidos)
    
    if not dados_cruzados: # Prevenção caso a planilha venha vazia
        flash("Nenhum dado encontrado na consulta.", "warning")
        return redirect(url_for('rotas.rota_consulta_lote'))
    
    dados_formatados = {
        "Excel": dados_cruzados,
        "pagina_atual": 1,
        "total_paginas": 1
    }

    # Envia o resultado para o seu template (usando o formato que ele já espera)
    return render_template('resultado_preventiva.html', dados=dados_formatados)



def validar_acesso(request):

    if request.method == 'POST':
        senha_digitada = request.form.get('senha')

        if senha_digitada == 'alohomora95':
            flash('acesso liberado com sucesso!',"success")
            return redirect(url_for('rotas.rota_alimentar_base'))
        else:
            flash('senha incorreta. Acesso negado.', 'danger')
            redirect(url_for('rotas.rota_acesso_base'))
    
    return render_template('pedir_senha.html')
