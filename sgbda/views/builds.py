from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import actualizaciones
from sgbda.services.microsoft_gdr_sync import sync_gdr

def listar_builds(request):
    
    builds = actualizaciones.objects.all()
    
    return render(request, 'paginas/builds.html', {
        "builds": builds})


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