from django.shortcuts import render, redirect
from django.contrib import messages
from sgbda.models import usuario

def bienvenida(request):

    # Si ya existe un usuario, no permitir acceso
    if usuario.objects.exists():
        return redirect('login')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Crear superusuario
        usuario.objects.create_user(
            nombre=username,
            rol='Administrador',
            password=password
        )

        return redirect('login')

    return render(request, 'paginas/bienvenida.html')
