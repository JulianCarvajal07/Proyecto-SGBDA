import re
from django.shortcuts import render, redirect
from django.contrib import messages
from sgbda.models import instancia, cliente, servidor, checkSQL, actualizaciones
from sgbda.services.actualizar_instancias_v3 import actualizar_instancias_desde_conexiones
from django.utils import timezone
from django.db.models import Q
import queue
import threading
import re
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_GET


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

    # leer resultados de actualización si existen
    success_msgs = request.session.pop("actualizacion_success", [])
    error_msgs   = request.session.pop("actualizacion_errors", [])

    for msg in success_msgs:
        messages.success(request, msg)

    for msg in error_msgs:
        messages.error(request, msg)

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

def stream_actualizacion(request):
    log_queue    = queue.Queue()
    session_key  = request.session.session_key

    # asegurar que la sesión existe antes de pasarla al hilo
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    def run():
        errores_sync      = []
        errores_check     = []
        nuevos_servidores = 0
        nuevas_instancias = 0
        checks_realizados = 0

        try:
            result = actualizar_instancias_desde_conexiones(log_queue)

            nuevos_servidores = result["servidores_nuevos"]
            nuevas_instancias = result["instancias_nuevas"]
            errores_sync      = result["errores"]

            log_queue.put(f"✔ Servidores nuevos: {nuevos_servidores} | Instancias nuevas: {nuevas_instancias}")

            if not errores_sync:
                log_queue.put("✔ Sincronización completada sin errores.")
            else:
                for e in errores_sync:
                    log_queue.put(f"✘ {e}")

            log_queue.put("─── Iniciando verificación de builds ───")

            instancias_qs = instancia.objects.all()

            for inst in instancias_qs:
                try:
                    if inst.edition != 'PostgreSQL':
                        match = re.search(r'\d{4}', inst.major_version)
                        version_normalizada = match.group() if match else inst.major_version
                    else:
                        match = re.search(r'\d+', inst.major_version)
                        version_normalizada = match.group() if match else inst.major_version

                    ultima_actualizacion = actualizaciones.objects.filter(
                        major_version=version_normalizada,
                    ).order_by('-release_date', '-build').first()

                    if not ultima_actualizacion:
                        msg = f"Sin referencia para versión {inst.major_version} en {inst.nombre_instancia}"
                        errores_check.append(msg)
                        log_queue.put(f"✘ {msg}")
                        continue

                    build_instancia      = inst.build
                    build_referencia     = ultima_actualizacion.build
                    nombre_ultima_update = ultima_actualizacion.descripcion
                    fecha_publicacion    = ultima_actualizacion.release_date

                    if build_instancia == build_referencia:
                        estado  = "Actualizado"
                        detalle = f"La instancia está en el build más reciente ({build_referencia})"
                    else:
                        estado  = "Desactualizado"
                        detalle = f"Build actual: {build_instancia} | Build más reciente: {build_referencia} ({ultima_actualizacion.kb})"

                    checkSQL.objects.update_or_create(
                        instancia=inst,
                        defaults={
                            "build_detectado":      build_instancia,
                            "build_referencia":     build_referencia,
                            "estado":               estado,
                            "nombre_ultima_update": nombre_ultima_update,
                            "fecha_publicacion":    fecha_publicacion,
                            "fecha_check":          timezone.now(),
                            "detalle":              detalle
                        }
                    )

                    log_queue.put(f"✔ {inst.nombre_instancia} — {estado} (build {build_instancia})")
                    checks_realizados += 1

                except Exception as e:
                    msg = f"Error en {inst.nombre_instancia}: {str(e)}"
                    errores_check.append(msg)
                    log_queue.put(f"✘ {msg}")

            log_queue.put(f"✔ Checks realizados: {checks_realizados} | Errores: {len(errores_check)}")

        except Exception as e:
            log_queue.put(f"✘ Error inesperado: {str(e)}")
            errores_check.append(f"Error inesperado: {str(e)}")

        finally:
            # ── Guardar en sesión directamente desde el hilo ──────────────
            try:
                from importlib import import_module
                from django.conf import settings

                SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
                session = SessionStore(session_key)

                success_msgs = [
                    f"Servidores nuevos: {nuevos_servidores} | Instancias nuevas: {nuevas_instancias}",
                    f"Checks realizados: {checks_realizados}",
                ]
                if not errores_sync and not errores_check:
                    success_msgs.append("Inventario actualizado sin errores.")

                session["actualizacion_success"] = success_msgs
                session["actualizacion_errors"]  = errores_sync + errores_check
                session.save()

            except Exception as e_session:
                print(f"Error guardando sesión: {e_session}")

            finally:
                log_queue.put(None)  # señal de fin

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    def event_stream():
        while True:
            mensaje = log_queue.get()
            if mensaje is None:
                yield "event: fin\ndata: Proceso completado\n\n"
                break
            yield f"data: {mensaje}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
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

