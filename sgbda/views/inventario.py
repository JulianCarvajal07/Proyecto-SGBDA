import pyodbc
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import instancia, cliente, servidor, checkSQL, actualizaciones
from sgbda.services.actualizar_instancias import actualizar_instancias_desde_conexiones
from django.utils import timezone


#=================================================================================
#=================================================================================
#=================================================================================
#=================================================================================

def listar_inventario(request):

    all_inventario =  instancia.objects.select_related(
        'servidor', 
        'servidor__cliente'
    ).prefetch_related(
        'servicios',
        'checksql'
    ).all()

    all_clientes = cliente.objects.all()

    return render(request, 'paginas/inventario.html',{
        'instancias': all_inventario,
        'clientes': all_clientes,
    })

#=================================================================================
#=================================================================================
#=================================================================================
#=================================================================================

def actualizar_inventario(request):

    try:

        result = actualizar_instancias_desde_conexiones()

        nuevos_servidores = result["servidores_nuevos"]
        nuevas_instancias = result["instancias_nuevas"]
        errores = result["errores"]

        messages.success(
            request,
            f"Servidores nuevos: {nuevos_servidores} | Instancias nuevas: {nuevas_instancias}"
        )

        for error in errores:
            messages.error(request, error)

        # ✅ opcional: avisar si todo salió limpio
        if not errores:
            messages.success(request, "Inventario actualizado sin errores.")

    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")

    return redirect('listar_inventario')

#=================================================================================
#=================================================================================
#=================================================================================
#=================================================================================


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

#=================================================================================
#=================================================================================
#=================================================================================
#=================================================================================

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

#=================================================================================
#=================================================================================
#=================================================================================
#=================================================================================

def ejecutar_check_builds(request):
    
    instancias = instancia.objects.all()
    
    checks_realizados = 0
    errores = []

    for inst in instancias:

        try:
            # Extraer solo el año de la major_version de la instancia
            match = re.search(r'\d{4}', inst.major_version)
            version_normalizada = match.group() if match else inst.major_version

            # 1. Buscar la actualización más reciente para esa major_version
            ultima_actualizacion = actualizaciones.objects.filter(
                major_version=version_normalizada,
                soportado=True
            ).order_by('-release_date').first()

            if not ultima_actualizacion:
                errores.append(f"No se encontró referencia para versión {inst.major_version} en instancia {inst.nombre_instancia}")
                continue

            build_instancia   = inst.build
            build_referencia  = ultima_actualizacion.build
            nombre_ultima_update = ultima_actualizacion.descripcion
            fecha_publicacion = ultima_actualizacion.release_date

            # 2. Comparar builds
            if build_instancia == build_referencia:
                estado  = "Actualizado"
                detalle = f"La instancia está en el build más reciente ({build_referencia})"

            else:
                estado  = "Desactualizado"
                detalle = f"Build actual: {build_instancia} | Build más reciente: {build_referencia} ({ultima_actualizacion.kb})"

            # 3. Guardar resultado en checkSQL
            checkSQL.objects.create(
                instancia        = inst,
                build_detectado  = build_instancia,
                build_referencia = build_referencia,
                estado           = estado,
                nombre_ultima_update = nombre_ultima_update,
                fecha_publicacion = fecha_publicacion,
                fecha_check      = timezone.now(),
                detalle          = detalle
            )

            checks_realizados += 1

        except Exception as e:
            errores.append(f"Error en instancia {inst.nombre_instancia}: {str(e)}")

    # 4. Mensajes al template
    messages.success(request, f"Checks realizados: {checks_realizados}")

    for error in errores:
        messages.error(request, error)

    return redirect('listar_inventario')