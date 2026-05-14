from django.shortcuts import render, redirect, get_object_or_404
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


def eliminar_usuario(request, id):

    if request.method == "POST":
        user_to_delete = get_object_or_404(usuario, id=id)

        # ❌ evitar que se elimine a sí mismo
        if request.user.id == user_to_delete.id:
            messages.error(request, "No puedes eliminar tu propio usuario")
            return redirect("listar_usuarios")

        user_to_delete.delete()
        messages.success(request, "Usuario eliminado correctamente")

    return redirect("listar_usuarios")