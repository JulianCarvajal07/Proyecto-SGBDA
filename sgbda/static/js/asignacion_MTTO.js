// Inicializar modal de Bootstrap (una sola vez al cargar)
const modalElement = document.getElementById('modalAsignacion');
const modalBootstrap = new bootstrap.Modal(modalElement);



function abrirModal(year, month, dia) {
    // Pre-llenar fecha del formulario
    document.getElementById('modal-fecha-exacta').value = `${year}-${month}-${dia}`;

    // Abrir modal con API de Bootstrap
    modalBootstrap.show();
}

// Limpiar formulario al cerrar modal
modalElement.addEventListener('hidden.bs.modal', function () {
    document.getElementById('form-asignacion').reset();
});

// cerrar modal cuando se escuche la peticion de creacion
document.body.addEventListener('htmx:afterRequest', function (event) {
    if (event.target.id === 'form-asignacion' && event.detail.successful) {
        modalBootstrap.hide();
        document.getElementById('form-asignacion').reset();
    }
});