document.addEventListener("DOMContentLoaded", function () {

    const btnActualizar = document.getElementById("btn-actualizar");
    const logContainer  = document.getElementById("log-container");
    const logOutput     = document.getElementById("log-output");

    // ocultar el contenedor hasta que se ejecute
    logContainer.style.display = "none";

    btnActualizar.addEventListener("click", function () {

        // limpiar y mostrar
        logOutput.innerHTML = "";
        logContainer.style.display = "block";
        btnActualizar.disabled = true;
        btnActualizar.textContent = "Actualizando...";

        const source = new EventSource("/actualizacion/stream/");

        source.onmessage = function (e) {
            const line = document.createElement("div");
            const texto = e.data;

            if (texto.includes("✘") || texto.toLowerCase().includes("error")) {
                line.style.color = "#f48771";
            } else if (texto.includes("✔") || texto.toLowerCase().includes("ok")) {
                line.style.color = "#89d185";
            } else if (texto.toLowerCase().includes("intento")) {
                line.style.color = "#dcdcaa";
            } else if (texto.toLowerCase().includes("conectando") || texto.toLowerCase().includes("consultando")) {
                line.style.color = "#9cdcfe";
            } else {
                line.style.color = "#d4d4d4";
            }

            line.textContent = texto;
            logOutput.appendChild(line);
            logContainer.scrollTop = logContainer.scrollHeight;
        };

        source.addEventListener("fin", function (e) {
            const line = document.createElement("div");
            line.style.color  = "#569cd6";
            line.style.marginTop = "8px";
            line.textContent  = "─── " + e.data + " ───";
            logOutput.appendChild(line);
            logContainer.scrollTop = logContainer.scrollHeight;

            source.close();
            btnActualizar.disabled    = false;
            btnActualizar.textContent = "Actualizar";

            // recargar la tabla después de 2s para reflejar los datos nuevos
            setTimeout(function () {
                window.location.reload();
            }, 2000);
        });

        source.onerror = function () {
            const line = document.createElement("div");
            line.style.color = "#f48771";
            line.textContent = "✘ Error en el stream — conexión perdida.";
            logOutput.appendChild(line);
            logContainer.scrollTop = logContainer.scrollHeight;

            source.close();
            btnActualizar.disabled    = false;
            btnActualizar.textContent = "Actualizar";
        };
    });
});