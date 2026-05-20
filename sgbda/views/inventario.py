import pyodbc

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import conexion, instancia
from sgbda.services.actualizar_instancias import actualizar_instancias_desde_conexiones

def listar_inventario(request):

    all_instancias = instancia.objects.all()
    
    return render(request, 'paginas/inventario.html',{
        'instancias': all_instancias,
    })


def actualizar_inventario(request):

    try:

        nuevos = actualizar_instancias_desde_conexiones()

        messages.success(
            request,
            f"Instancias actualizadas. Nuevas: {nuevos}"
        )

    except Exception as e:

        messages.error(
            request,
            str(e)
        )

    return redirect('listar_inventario')

