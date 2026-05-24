document.querySelectorAll('.filtro-auto').forEach(select => {

    select.addEventListener('change', () => {
        select.form.submit();
    });

});

