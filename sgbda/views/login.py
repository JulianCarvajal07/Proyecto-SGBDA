from django.shortcuts import render
from django.contrib.auth import authenticate, login  as auth_login
from django.http import JsonResponse
from django.urls import reverse

def login_usuario(request):
    if request.method == 'POST':
        usuario_input = request.POST['usuario']
        contraseña_input = request.POST['contraseña']
        user = authenticate(request, username=usuario_input, password=contraseña_input)

        if user is not None:
            auth_login(request, user)
            return JsonResponse({'success': True, 'redirect_url': reverse('listar_inventario')})
            #return redirect('datos_cliente_proyecto')
        else:
            #error = "Usuario o contraseña incorrectos"
            return JsonResponse({'success': False, 'error': 'Usuario o contraseña incorrectos'})
            #return render(request, 'paginas/inicio_sesion.html', {'error': error})
    return render(request, 'paginas/login.html')