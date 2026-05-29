from django.shortcuts import render, redirect
from sgbda.models import usuario


def inicio(request):

    if usuario.objects.exists():
        return redirect('login')

    return redirect('bienvenida')


def bienvenida(request):

    # Si ya existe un superusuario, redirigir al login
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
