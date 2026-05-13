    // Toggle Dark / Light Mode
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    themeToggle.addEventListener('click', () => {
        if (html.getAttribute('data-bs-theme') === 'dark') {
            html.setAttribute('data-bs-theme', 'light');
            themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
        } else {
            html.setAttribute('data-bs-theme', 'dark');
            themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
        }
    });