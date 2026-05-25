const sidebar = document.querySelector('.sidebar');
const toggleBtn = document.getElementById('toggleSidebar');

// Revisar estado guardado al cargar la página
if (localStorage.getItem('sidebar') === 'collapsed') {
    sidebar.classList.add('collapsed');
}

// Evento del botón
toggleBtn.addEventListener('click', () => {

    sidebar.classList.toggle('collapsed');

    // Guardar estado
    if (sidebar.classList.contains('collapsed')) {
        localStorage.setItem('sidebar', 'collapsed');
    } else {
        localStorage.setItem('sidebar', 'expanded');
    }
});