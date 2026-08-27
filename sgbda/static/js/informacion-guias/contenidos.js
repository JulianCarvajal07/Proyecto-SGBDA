document.querySelectorAll('[data-dropdown]').forEach(dropdown => {
    const trigger = dropdown.querySelector('.select-trigger');

    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = dropdown.classList.contains('open');

        // Cierra todos los demás
        document.querySelectorAll('[data-dropdown].open').forEach(d => {
            if (d !== dropdown) d.classList.remove('open');
        });

        dropdown.classList.toggle('open');
        trigger.setAttribute('aria-expanded', !isOpen);
    });
});

// Cierra al hacer click fuera
document.addEventListener('click', (e) => {
    if (!e.target.closest('[data-dropdown]')) {
        document.querySelectorAll('[data-dropdown].open').forEach(d => {
            d.classList.remove('open');
            d.querySelector('.select-trigger').setAttribute('aria-expanded', 'false');
        });
    }
});