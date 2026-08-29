from django.shortcuts import render

def informacion_motores(request):

    return render(request, 'paginas/contenidos-DBA/info_motores.html')

def mantenimientos_SqlServer(request):

    return render(request, 'paginas/contenidos-DBA/Mantenimientos.html')

def Mover_datafiles(request):

    return render(request, 'paginas/contenidos-DBA/Mover_Datafiles.html')

def Instalar_Postgresql(request):

    return render(request, 'paginas/contenidos-DBA/Instalacion_PostgreSQL.html')

def Data_warehouse(request):

    return render(request, 'paginas/contenidos-DBA/Data_warehouse.html')

def SQL_avanzado(request):

    return render(request, 'paginas/contenidos-DBA/SQL_avanzado.html')

def Modelamiento_dimensional(request):

    return render(request, 'paginas/contenidos-DBA/Modelamiento_dimensional.html')