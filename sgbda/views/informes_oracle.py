from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import conexion_ssh
from django.shortcuts import render, get_object_or_404
from sgbda.services.extraccion_ssh import obtener_metricas_oracle
from django.http import JsonResponse
from django.template.loader import render_to_string


def informes_oracle(request):

    todas_conexiones = conexion_ssh.objects.all()
    
    return render(request, 'paginas/informes_oracle.html', {
        "conexiones": todas_conexiones
    })


def generar_informe(request, conexion_id):
    conexion = get_object_or_404(conexion_ssh, id=conexion_id)
    
    if request.method == "POST":
        contexto = {}
        try:
            # 1. Extraer datos por SSH
            datos = obtener_metricas_oracle(
                host=conexion.ip_servidor,
                user=conexion.usuario,
                password=conexion.password_encriptado,
                port=22
            )
            
            # 2. Ordenar tablespaces por % uso
            datos['tablespaces'] = sorted(
                datos.get('tablespaces', []), 
                key=lambda x: x['pct_uso'], 
                reverse=True
            )
            
            contexto['reporte'] = datos
            contexto['conexion'] = conexion
            
            # 3. Renderizar fragmento HTML para el modal
            html_informe = render_to_string('paginas/modals/informe_oracle_body.html', contexto, request=request)
            
            # Retorna SIEMPRE un JSON
            return JsonResponse({'status': 'ok', 'html': html_informe})

        except Exception as e:
            # En caso de error SSH o de ejecución, retorna también un JSON con el mensaje
            return JsonResponse({
                'status': 'error', 
                'message': f"Error al conectar con {conexion.ip_servidor}: {str(e)}"
            }, status=500)

    # Si es una petición GET estándar (al cargar la página por primera vez)
    return render(request, 'paginas/informes_oracle.html', {'conexion': conexion})