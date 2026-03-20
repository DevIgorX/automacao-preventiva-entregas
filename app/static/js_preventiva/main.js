// static/js_preventiva/main.js

document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const inputArquivos = document.getElementById('arquivos');
    const fileList = document.getElementById('file-list');
    const formAnalise = document.getElementById('form-analise');
    const loader = document.getElementById('loader-overlay');
    const alerts = document.querySelectorAll('.alert');


     // Auto fechar alerts  (mensagens do flash)
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                let bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        }, 5000); 
    }

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



});