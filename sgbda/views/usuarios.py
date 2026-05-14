from django.shortcuts import render, redirect
from sgbda.models import usuario
from django.contrib import messages


def listar_usuarios(request):
    
    todos_usuarios = usuario.objects.all()
    
    return render(request, 'paginas/usuarios.html', {
        "usuarios": todos_usuarios
    })


def registro_usuarios(request):

    if request.method == "POST":
        nombre = request.POST.get("usuario")
        rol = request.POST.get("rol")
        password = request.POST.get("contraseña")

        # crear usuario en base de datos
        usuario.objects.create_user(
            nombre=nombre,
            rol=rol,
            password=password
        )

        messages.success(request, "Usuario registrado correctamente")
        return redirect("listar_usuarios")
    
    
    return render(request, 'paginas/usuarios.html')