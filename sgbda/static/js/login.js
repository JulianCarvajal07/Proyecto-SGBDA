document.getElementById('login-form').addEventListener('submit', function(e) {
    e.preventDefault()  // evita que el form recargue la página

    const formData = new FormData(this)

    fetch('/login/', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect_url  // redirige
        } else {
            alert(data.error)  // muestra el error
        }
    })
})