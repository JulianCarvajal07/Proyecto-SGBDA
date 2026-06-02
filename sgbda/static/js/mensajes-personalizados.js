/*document.addEventListener("DOMContentLoaded", function () {
    const alerta = document.getElementById("mi-alerta");

    if (alerta) {
        // Aparece suavemente
        setTimeout(() => {
            alerta.classList.add("show");
        }, 100);

        // Desaparece suavemente después de 3 segundos
        setTimeout(() => {
            alerta.classList.remove("show");

            // eliminar del DOM cuando termine la animación
            setTimeout(() => {
                alerta.remove();
            }, 500); // debe coincidir con el transition
        }, 3000);
    }
}); */



// Auto-dismiss alerts after 5 seconds
document.querySelectorAll('.alert-custom').forEach(alert => {
    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-12px)';
        alert.style.transition = 'all 0.4s ease';
        setTimeout(() => alert.remove(), 400);
    }, 10000);
});
