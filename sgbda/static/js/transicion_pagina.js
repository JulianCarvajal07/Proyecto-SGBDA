/* 
EXPLICACION DEL CODIGO:
document.addEventListener("DOMContentLoaded", () => { ... });
Espera a que el HTML esté completamente cargado y parseado.

- El navegador lee el HTML de arriba hacia abajo
- Cuando termina de construir el DOM (árbol de elementos), dispara el evento DOMContentLoaded
- Solo entonces ejecuta el código dentro

 + ¿Por qué? Porque si intentas seleccionar .transicion-pagina 
 antes de que exista en el DOM, querySelector devuelve null y falla.

requestAnimationFrame(() => { ... });

    Espera al próximo frame de dibujo del navegador.

+ El navegador dibuja la pantalla aproximadamente 60 veces por segundo. 
rAF dice: "ejecuta esto justo antes del siguiente dibujo".

+ Es como decirle al navegador: "Primero muéstrame la página invisible, 
y después empieza a hacerla visible".

1. Navegador recibe HTML
   <body class="transicion-pagina fade-enter">
   
   Estado: opacity: 0  ←── INVISIBLE

        ↓

2. DOMContentLoaded (HTML listo)
   
        ↓

3. requestAnimationFrame (espera al siguiente frame)
   
        ↓

4. Navegador PINTA por primera vez
   [pantalla negra / invisible]
   
        ↓

5. Se ejecuta el callback de rAF
   Quita .fade-enter
   
   Estado ahora: opacity: 1  ←── VISIBLE
   PERO con transition: opacity .35s ease
   
        ↓

6. Navegador detecta cambio de opacity
   Anima: 0 → 1 durante 0.35 segundos
   
   [página aparece suavemente]
*/

document.addEventListener("DOMContentLoaded", () => {

    requestAnimationFrame(() => {
        document
            .querySelector(".transicion-pagina")
            ?.classList.remove("fade-enter");
    });

});


/* 
EXPLICACION DEL CODIGO:
document.querySelectorAll(".page-transition")

    Busca TODOS los elementos con clase page-transition

+ Devuelve una lista (NodeList) con todos los enlaces que 
tienen esa clase. Estos son los botones/enlaces que activarán 
la transición al hacer clic.

.forEach(link => { ... })

    Recorre cada enlace uno por uno

+ Por cada enlace encontrado, ejecuta el código que le sigue. 
Así todos los enlaces con esa clase tendrán el mismo comportamiento.

link.addEventListener("click", function(e){ ... })

    Escucha el clic en cada enlace

+ Cuando el usuario hace clic, se dispara la función. El e es 
el evento del clic y contiene información sobre qué pasó.

¿Por qué function y no =>?
Porque usa this.href más adelante. Con function, this apunta 
al elemento clickeado (el <a>). Con =>, this sería diferente.

e.preventDefault();
    
    BLOQUEA la acción por defecto del enlace

const contenido = document.querySelector(".transicion-pagina");
  
    Busca el elemento que se va a desvanecer

+ Generalmente es el <body> o un contenedor principal 
que envuelve todo el contenido de la página.

contenido.classList.add("fade-out");

    Agrega la clase que inicia el desvanecimiento

setTimeout(() => { ... }, 50);
    
    Espera 50 milisegundos y luego navega

*/

document.querySelectorAll(".page-transition").forEach(link => {

    link.addEventListener("click", function(e){
        e.preventDefault();

        const contenido = document.querySelector(".transicion-pagina");
        contenido.classList.add("fade-out");

        setTimeout(() => {
            window.location = this.href;
        },50);

    });

});

