document.addEventListener('DOMContentLoaded', function () {
    const button = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    if (!button || !sidebar) return;
    button.setAttribute('aria-label', 'Abrir ou recolher menu');
    button.setAttribute('aria-expanded', String(!sidebar.classList.contains('active')));
    button.addEventListener('click', function () {
        sidebar.classList.toggle('active');
        button.setAttribute('aria-expanded', String(!sidebar.classList.contains('active')));
    });
});
