from django.shortcuts import render, redirect
from django.contrib import messages
from sgbda.models import actualizaciones
from django.db.models import Q
from sgbda.services.microsoft_gdr__postgresql_sync_v2 import sync_gdr

def listar_builds(request):
    
    builds = actualizaciones.objects.all().order_by('major_version','-release_date')

    buscar = request.GET.get('buscar')
    version = request.GET.get('version')

    # FILTRO DE TEXTO
    if buscar:
        builds = builds.filter(
            Q(kb__icontains=buscar) |
            Q(build__icontains=buscar) |
            Q(descripcion__icontains=buscar)
        )

    # FILTRO POR VERSION
    if version:
        builds = builds.filter(
            major_version__icontains=version
        )

    context = {
        'builds':builds,
    }
    
    return render(request, 'paginas/builds.html', context)



def actualizar_builds(request):

    try:
        
        nuevos = sync_gdr()

        messages.success(
            request,
            f"Sincronización completada. "
            f"Se agregaron {nuevos} builds nuevas."
        )

    except Exception as e:

        messages.error(
            request,
            f"Error en sincronización: {str(e)}"
        )

    return redirect('listar_builds')