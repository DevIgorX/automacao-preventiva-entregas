

document.addEventListener('DOMContentLoaded', function() {
    

    // Script da Sidebar movido para cá
    const btnSidebar = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');

    if (btnSidebar && sidebar) {
        btnSidebar.addEventListener('click', function () {
            sidebar.classList.toggle('active');
        });
    }
});