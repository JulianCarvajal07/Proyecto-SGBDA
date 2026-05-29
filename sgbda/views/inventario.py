import re
from django.shortcuts import render, redirect
from django.contrib import messages
from sgbda.models import instancia, cliente, servidor, checkSQL, actualizaciones
from sgbda.services.actualizar_instancias_v2 import actualizar_instancias_desde_conexiones
from django.utils import timezone
from django.db.models import Q


#=================================================================================
#=================================================================================
#=================================================================================
#=================================================================================

def listar_inventario(request):

    buscar = request.GET.get('buscar', '')
    version = request.GET.get('versiones_sql', '')
    version_pg = request.GET.get('versiones_pg', '')
    clientes_obj = request.GET.get('cliente_actual', '')
    administrado = request.GET.get('administrados')

    all_clientes = cliente.objects.all()

    all_inventario =  instancia.objects.select_related(
        'servidor', 
        'servidor__cliente'
    ).prefetch_related(
        'servicios',
        'checksql'
    ).all()

    # FILTRO DE TEXTO
    if buscar:
        all_inventario = all_inventario.filter(
            Q(nombre_instancia__icontains=buscar) |
            Q(build__icontains=buscar) |
            Q(edition__icontains=buscar) |
            Q(servidor__ip__icontains=buscar) |
            Q(servidor__hostname__icontains=buscar) |
            Q(servidor__sistema_operativo__icontains=buscar)
        )
    
    filtro_versiones = Q()

    # FILTRO COMBINADO PARA BUSCAR VERSIONES DE PG Y SQL SERVER AL TIEMPO
    if version:
        filtro_versiones |= Q(major_version__icontains=version)

    if version_pg:
        filtro_versiones |= Q(major_version__icontains=version_pg)

    if filtro_versiones:
        all_inventario = all_inventario.filter(filtro_versiones)

    # FILTRO SI ESTA ADMINISTRADA LA INSTANCIA 
    if administrado in ["True", "False"]:
        all_inventario = all_inventario.filter(
            administrado=(administrado == "True")
        )

    # FILTRO POR CLIENTE
    if clientes_obj:
        all_inventario = all_inventario.filter(
            servidor__cliente__nombre__icontains=clientes_obj
        )

    return render(request, 'paginas/inventario.html',{
        'instancias': all_inventario,
        'clientes': all_clientes,
        # devolver filtros al template
        'buscar': buscar,
        'versiones_sql': version,
        'versiones_pg': version_pg,
        'administrados': administrado,
        'cliente_actual': clientes_obj,
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

#===================================================================
#               PASO PARA VERIFICAR SI LAS INSTANCIAS
#               CUENTAN CON LA ULTIMA ACTUALIZACION
#===================================================================
    instancias = instancia.objects.all()
    
    checks_realizados = 0
    errores = []

    for inst in instancias:

        try:
            if inst.edition != 'PostgreSQL':
                # Extraer solo el año de la major_version de la instancia
                # la major_version en SQL SERVER se guarda como 'Microsoft SQL Server 2019'
                match = re.search(r'\d{4}', inst.major_version)
                version_normalizada = match.group() if match else inst.major_version
            else:
                # Extraer la version de postgresql
                # la major version en PostgreSQL se guarda como 'Postgresql 16'
                match = re.search(r'\d+', inst.major_version)
                version_normalizada = match.group() if match else inst.major_version
                            
            print(version_normalizada)

            # 1. Buscar la actualización más reciente para esa major_version
            ultima_actualizacion = actualizaciones.objects.filter(
                major_version=version_normalizada,
            ).order_by(
                '-release_date',
                '-build'
            ).first()

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
            checkSQL.objects.update_or_create(
                instancia=inst, #clave de busquedad
                defaults={
                    "build_detectado":     build_instancia,
                    "build_referencia":    build_referencia,
                    "estado":              estado,
                    "nombre_ultima_update": nombre_ultima_update,
                    "fecha_publicacion":   fecha_publicacion,
                    "fecha_check":         timezone.now(),
                    "detalle":             detalle
                }
            )

            checks_realizados += 1

        except Exception as e:
            errores.append(f"Error en instancia {inst.nombre_instancia}: {str(e)}")

    for error in errores:
        messages.error(request, error)

    return redirect('listar_inventario')

#=================================================================================
#=================================================================================
#=================================================================================
#=================================================================================


def detalles_instancia(request):

    if request.method == "POST":

        instancia_id = request.POST.get("id_instancia")
        servidor_id = request.POST.get("id_servidor")
        nombre_cliente = request.POST.get("cliente_id").strip()
        administrado = request.POST.get("administrado")
        observaciones = request.POST.get("observaciones").strip()

        if not nombre_cliente or not administrado:

            messages.error(
                request,
                "Debe llenar los campos obligatorios"
            )

            return redirect("listar_inventario")

        # obtener servidor
        servidor_obj = servidor.objects.get(id_servidor=servidor_id)

        # SI YA TIENE CLIENTE -> modificar nombre
        if nombre_cliente:
            servidor_obj.cliente_id = nombre_cliente
            servidor_obj.save()

        #obtener instancia
        instancia_obj = instancia.objects.get(id_instancia=instancia_id)
        instancia_obj.administrado = administrado
        instancia_obj.observaciones = observaciones
        instancia_obj.save()
        messages.success(
            request,
            "Informacion actualizadada correctamente."
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
        
        if instancia_id and instancia_obj:
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
