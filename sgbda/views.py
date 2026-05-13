from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login  as auth_login
from django.http import JsonResponse
from django.urls import reverse


def index(request):
    return render(request, 'paginas/login.html')


def login_usuario(request):
    if request.method == 'POST':
        usuario_input = request.POST['usuario']
        contraseña_input = request.POST['contraseña']
        user = authenticate(request, username=usuario_input, password=contraseña_input)

        if user is not None:
            auth_login(request, user)
            return JsonResponse({'success': True, 'redirect_url': reverse('bases_de_datos')})
            #return redirect('datos_cliente_proyecto')
        else:
            #error = "Usuario o contraseña incorrectos"
            return JsonResponse({'success': False, 'error': 'Usuario o contraseña incorrectos'})
            #return render(request, 'paginas/inicio_sesion.html', {'error': error})
    return render(request, 'paginas/login.html')


def bases_de_datos(request):

    return render(request, 'paginas/bases_de_datos.html')