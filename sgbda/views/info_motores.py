from django.shortcuts import render

def informacion_motores(request):

    return render(request, 'paginas/info_motores.html')

def mantenimientos_SqlServer(request):

    return render(request, 'paginas/contenidos-DBA/Mantenimientos.html')