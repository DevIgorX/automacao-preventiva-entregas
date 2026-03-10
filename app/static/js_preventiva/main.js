// static/js_preventiva/main.js

document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const inputArquivos = document.getElementById('arquivos');
    const fileList = document.getElementById('file-list');
    const formAnalise = document.getElementById('form-analise');
    const loaderOverlay = document.getElementById('loader-overlay');

    // 1. Abre o seletor de arquivos ao clicar na área de upload
    if (uploadArea && inputArquivos) {
        uploadArea.addEventListener('click', function() {
            inputArquivos.click();
        });
    }

    // 2. Mostra a quantidade de arquivos selecionados
    if (inputArquivos && fileList) {
        inputArquivos.addEventListener('change', function() {
            let files = this.files;
            if (files.length > 0) {
                fileList.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> ${files.length} arquivo(s) selecionado(s).`;
            } else {
                fileList.innerHTML = "";
            }
        });
    }

    // 3. Ativa o loader ao enviar formulários (como o de upload)
    if (formAnalise && loaderOverlay) {
        formAnalise.addEventListener('submit', function() {
            loaderOverlay.style.display = 'flex';
        });
    }

    // 4. NOVA FUNCIONALIDADE: Captura o clique no link de "Processar"
    // Procuramos por qualquer link que contenha "processar=true" na URL
    const btnProcessar = document.querySelector('a[href*="processar=true"]');
    
    if (btnProcessar && loaderOverlay) {
        btnProcessar.addEventListener('click', function(e) {
            // Exibe o overlay de carregamento que você gosta
            loaderOverlay.style.display = 'flex';
            
            // Opcional: Adiciona um efeito visual no próprio botão
            this.classList.add('disabled');
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processando Dados...';
        });
    }
});