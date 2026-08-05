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
                puerto=conexion.puerto,
                user=conexion.usuario,
                password=conexion.password_encriptado,
            )
            
            # 2. Ordenar tablespaces por % uso
            datos['tablespaces'] = sorted(
                datos.get('tablespaces', []), 
                key=lambda x: x['pct_uso'], 
                reverse=True
            )

            # Asegurar que ram_usada_pct sea un número limpio
            ram_raw = datos.get('ram_usada_pct', 0)
            try:
                datos['ram_usada_pct'] = int(float(str(ram_raw).replace('%', '')))
            except (ValueError, TypeError):
                datos['ram_usada_pct'] = 0

            def get_empresa_por_ip(ip):
                empresas = {
                    "10.75.36.": {
                        "nombre": "UNICLARETIANA",
                        "dirigido": "Ing. Carlos Alberto Gómez G.", 
                        "cargo": "Director TIC"
                    },
                    "172.21.230": {
                        "nombre": "BERCHMANS",
                        "dirigido": "Ing. Diego Fernando Tovar Suarez",
                        "cargo": "Coordinación de sistemas" 
                    },
                    "10.75.60": {
                        "nombre": "DEBORA",
                        "dirigido": "Recursos Tecnológicos y Apoyo Académico",
                        "cargo": ""
                    },
                    "10.75.19": {
                        "nombre": "CAMACHO",
                        "dirigido": "Ing. Carlos Alberto Rodríguez",
                        "cargo": "Director TIC"
                    },
                }
                
                for prefijo, datos in empresas.items():
                    if ip.startswith(prefijo):
                        return datos
                        
                return {"nombre": "no identificado", "dirigido": "no identificado", "cargo": "no identificado"}

            # Dentro de tu vista:
            contexto['empresa'] = get_empresa_por_ip(conexion.ip_servidor)
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