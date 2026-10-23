// O envio e a escolha do relatório funcionam também sem JavaScript.
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-confirmar-limpeza]').forEach(form => {
        form.addEventListener('submit', event => {
            if (!window.confirm('Começar uma nova análise? Os arquivos desta análise serão removidos. Baixe o resultado antes de continuar.')) {
                event.preventDefault();
            }
        });
    });
});
