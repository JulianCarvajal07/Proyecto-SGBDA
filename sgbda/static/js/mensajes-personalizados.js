document.addEventListener("DOMContentLoaded", function () {
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
});
