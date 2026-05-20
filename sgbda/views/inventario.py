import pyodbc

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import instancia, cliente, servidor
from sgbda.services.actualizar_instancias import actualizar_instancias_desde_conexiones

def listar_inventario(request):

    all_inventario =  instancia.objects.select_related('servidor', 'servidor__cliente').all()

    return render(request, 'paginas/inventario.html',{
        'instancias': all_inventario,
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

def asignar_cliente(request):

    if request.method == "POST":

        servidor_id = request.POST.get("id_servidor")
        nombre_cliente = request.POST.get("nombre_cliente")

        if not nombre_cliente:

            messages.error(
                request,
                "Debe ingresar un nombre"
            )

            return redirect("listar_inventario")

        nombre_cliente = nombre_cliente.strip()

        # obtener servidor
        servidor_obj = servidor.objects.get(
            id_servidor=servidor_id
        )

        # SI YA TIENE CLIENTE -> modificar nombre
        if servidor_obj.cliente:

            servidor_obj.cliente.nombre = nombre_cliente
            servidor_obj.cliente.save()

            messages.success(
                request,
                "Cliente actualizado correctamente."
            )

        else:

            cliente_obj = cliente.objects.create(
                    nombre=nombre_cliente
                )

            # asignar cliente al servidor
            servidor_obj.cliente = cliente_obj
            servidor_obj.save()

            messages.success(
                request,
                "Cliente asignado correctamente."
            )

    return redirect("listar_inventario")


