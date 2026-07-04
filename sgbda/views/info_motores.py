from django.shortcuts import render

def informacion_motores(request):

    return render(request, 'paginas/info_motores.html')