document.addEventListener('DOMContentLoaded', function() {
    // 1. Elementos da Interface
    const inputArquivos = document.getElementById('arquivos');
    const listaArquivos = document.getElementById('file-list');
    const formAnalise = document.getElementById('form-analise');
    const loader = document.getElementById('loader-overlay');
    const uploadArea = document.getElementById('upload-area')

    // 2. Mostrar nomes dos arquivos selecionados
    if (inputArquivos) {
        inputArquivos.addEventListener('change', function (e) {
            const files = e.target.files;
            if (files.length > 0) {
                listaArquivos.innerHTML = `${files.length} arquivo(s) selecionado(s)`;
            }
        });
    }

    // 3. Mostrar o Loader ao processar análise
    if (formAnalise) {
        formAnalise.addEventListener('submit', function() {
            // Exibe o overlay de carregamento
            if (loader) {
                loader.style.display = 'flex';
            }
            
            // Desabilita o botão para evitar cliques duplos
            const btn = this.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-sync fa-spin me-2"></i>Processando...';
            }
        });
    }

    if (uploadArea && inputArquivos) {
        uploadArea.addEventListener('click', function () {
            inputArquivos.click();
        });
    }

});