// Función auxiliar para leer cookies en JavaScript
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function generarInformeModal(urlGenerar) {
    const modalElement = document.getElementById('modalInformeOracle');
    const modalBs = new bootstrap.Modal(modalElement);
    const cuerpoModal = document.getElementById('modalCuerpoInforme');
    
    // Spinner de Carga
    cuerpoModal.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status"></div>
            <h5 class="mt-3 text-muted">Conectando por SSH a la base de datos...</h5>
        </div>
    `;
    
    modalBs.show();

    // Obtener el token directamente de la cookie de sesión
    const csrftoken = getCookie('csrftoken');

    fetch(urlGenerar, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken, // Token obtenido dinámicamente
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok && !response.headers.get('content-type')?.includes('application/json')) {
            throw new Error(`Error en el servidor web (Estatus: ${response.status})`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'ok') {
            cuerpoModal.innerHTML = data.html;
        } else {
            cuerpoModal.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <h5>❌ Error al generar el informe</h5>
                    <p class="mb-0">${data.message}</p>
                </div>
            `;
        }
    })
    .catch(error => {
        cuerpoModal.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <h5>❌ Error de comunicación</h5>
                <p class="mb-0">${error.message || error}</p>
            </div>
        `;
    });
}