import pyodbc

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import instancia, cliente, servidor
from sgbda.services.actualizar_instancias import actualizar_instancias_desde_conexiones

def listar_inventario(request):

    all_inventario =  instancia.objects.select_related(
        'servidor', 
        'servidor__cliente'
    ).prefetch_related(
        'servicios'
    ).all()

    all_clientes = cliente.objects.all()

    return render(request, 'paginas/inventario.html',{
        'instancias': all_inventario,
        'clientes': all_clientes,
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
        nombre_cliente = request.POST.get("cliente_id")

        if not nombre_cliente:

            messages.error(
                request,
                "Debe ingresar un nombre"
            )

            return redirect("listar_inventario")

        nombre_cliente = nombre_cliente.strip()

        # obtener servidor
        servidor_obj = servidor.objects.get(id_servidor=servidor_id)

        # SI YA TIENE CLIENTE -> modificar nombre
        if nombre_cliente:
            servidor_obj.cliente_id = nombre_cliente
            servidor_obj.save()

            messages.success(
                request,
                "Cliente actualizado correctamente."
            )

        else:

            messages.error(
                request,
                "Debe asignar un cliente."
            )

    return redirect("listar_inventario")

def eliminar_instancia(request):

    if request.method == 'POST':
        instancia_id = request.POST.get('id_instancia')
        instancia_obj= instancia.objects.get(id_instancia=instancia_id)
        
        if instancia_obj:
            instancia_obj.delete()
            messages.success(request,"sea eliminado la instancia correctamente")
            return redirect('listar_inventario')
        else:
            messages.error(request,"Error, al eliminar la instancia")
            return redirect('listar_inventario')


