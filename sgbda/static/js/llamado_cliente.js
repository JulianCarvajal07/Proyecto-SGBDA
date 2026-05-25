document.addEventListener("DOMContentLoaded", function () {

    let modal = document.getElementById("modalId");

    modal.addEventListener("show.bs.modal", function (event) {

        console.log("escucho el evento")
        
        let button = event.relatedTarget;

        // Leer valores del botón
        let idcliente = button.getAttribute("id-cliente");
        let nombre = button.getAttribute("data-nombre");
        let idservidor = button.getAttribute("id-servidor");


        console.log(nombre)

        // Poner valores en los inputs del modal
        document.getElementById("cliente-id").value = idcliente;
        document.getElementById("nombre-cliente").value =  idcliente; 
        document.getElementById("servidor-id").value = idservidor;
    });
});