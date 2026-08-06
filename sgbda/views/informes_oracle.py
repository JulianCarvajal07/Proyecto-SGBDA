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

            # --- GENERAR OBSERVACIONES ---
            observaciones = generar_observaciones(datos)

            # Dentro de tu vista:
            contexto['empresa'] = get_empresa_por_ip(conexion.ip_servidor)
            contexto['reporte'] = datos
            contexto['conexion'] = conexion
            contexto['observaciones'] = observaciones
            
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


def generar_observaciones(datos):
    """Genera recomendaciones de DBA basadas en las métricas recolectadas."""
    obs = []
    
    # --- TABLESPACES ---
    for ts in datos.get('tablespaces', []):
        pct = float(ts.get('pct_uso', 0) or 0)
        nombre = ts.get('nombre', 'Desconocido')
        
        if pct >= 95:
            obs.append({
                'tipo': 'danger',
                'titulo': f'Crítico: Tablespace {nombre}',
                'mensaje': f'El tablespace <strong>{nombre}</strong> está al <strong>{pct}%</strong> de su capacidad. Se recomienda agregar datafiles o habilitar autoextend de inmediato para evitar bloqueos de transacciones.'
            })
        elif pct >= 85:
            obs.append({
                'tipo': 'warning',
                'titulo': f'Alerta: Tablespace {nombre}',
                'mensaje': f'El tablespace <strong>{nombre}</strong> está al <strong>{pct}%</strong> de uso. Se sugiere monitorear y planificar ampliación de almacenamiento.'
            })
    
    # --- OBJETOS INVÁLIDOS ---
    obj_inv = int(datos.get('obj_invalidos', 0) or 0)
    if obj_inv > 0:
        obs.append({
            'tipo': 'warning',
            'titulo': 'Objetos Inválidos Detectados',
            'mensaje': f'Se encontraron <strong>{obj_inv}</strong> objetos con estado INVALID. Ejecutar <code>utlrp.sql</code> o revisar dependencias rotas.'
        })
    
    # --- ERRORES DE COMPILACIÓN ---
    err_comp = int(datos.get('errores_compilacion', 0) or 0)
    if err_comp > 0:
        obs.append({
            'tipo': 'danger',
            'titulo': 'Errores de Compilación',
            'mensaje': f'Existen <strong>{err_comp}</strong> errores registrados en <code>dba_errors</code>. Revisar objetos que fallaron compilación.'
        })
    
    # --- BUFFER CACHE HIT RATIO ---
    buffer_hit = float(datos.get('buffer_hit', 0) or 0)
    if buffer_hit < 90:
        obs.append({
            'tipo': 'danger',
            'titulo': 'Buffer Cache Hit Ratio Bajo',
            'mensaje': f'El buffer hit ratio es de <strong>{buffer_hit}%</strong> (recomendado > 95%). La instancia está realizando muchas lecturas físicas. Considerar aumentar la SGA o revisar queries sin índices.'
        })
    elif buffer_hit < 95:
        obs.append({
            'tipo': 'warning',
            'titulo': 'Buffer Cache Hit Ratio Regular',
            'mensaje': f'El buffer hit ratio es de <strong>{buffer_hit}%</strong>. Monitorear carga de trabajo y planes de ejecución.'
        })
    
    # --- MEMORIA RAM ---
    ram_pct = float(datos.get('ram_usada_pct', 0) or 0)
    if ram_pct >= 90:
        obs.append({
            'tipo': 'danger',
            'titulo': 'Uso de RAM Crítico',
            'mensaje': f'El servidor está usando el <strong>{ram_pct}%</strong> de la memoria RAM. Riesgo de swapping y degradación severa del performance.'
        })
    elif ram_pct >= 75:
        obs.append({
            'tipo': 'warning',
            'titulo': 'Uso de RAM Elevado',
            'mensaje': f'El servidor está usando el <strong>{ram_pct}%</strong> de la memoria RAM. Revisar procesos consumidores y ajustar parámetros de memoria de Oracle.'
        })
    
    # --- FILESYSTEMS ---
    for fs in datos.get('filesystems', []):
        pct_fs = int(fs.get('use_pct', '0%').replace('%', ''))
        mount = fs.get('mounted_on', 'Desconocido')
        if pct_fs >= 90:
            obs.append({
                'tipo': 'danger',
                'titulo': f'Filesystem {mount} Saturado',
                'mensaje': f'El filesystem montado en <strong>{mount}</strong> está al <strong>{pct_fs}%</strong>. Liberar espacio o expandir volumen para evitar caída del servicio.'
            })
        elif pct_fs >= 80:
            obs.append({
                'tipo': 'warning',
                'titulo': f'Filesystem {mount} con Alto Uso',
                'mensaje': f'El filesystem <strong>{mount}</strong> está al <strong>{pct_fs}%</strong>. Planificar limpieza o expansión.'
            })
    
    # --- BACKUPS ---
    backups = datos.get('backups', [])
    if not backups:
        obs.append({
            'tipo': 'danger',
            'titulo': 'No se Detectaron Backups',
            'mensaje': 'No se encontraron archivos de backup en las rutas configuradas. Verificar política de respaldo y ejecución de jobs RMAN/Export.'
        })
    
    # --- ESTADÍSTICAS DE TABLAS ---
    stats = datos.get('stats_tablas', {})
    sin_stats = int(stats.get('sin_estadisticas', 0) or 0)
    no_act = int(stats.get('no_actualizadas', 0) or 0)
    
    if sin_stats > 0:
        obs.append({
            'tipo': 'warning',
            'titulo': 'Tablas Sin Estadísticas',
            'mensaje': f'Hay <strong>{sin_stats}</strong> tablas sin estadísticas. El optimizador puede generar planes de ejecución deficientes. Ejecutar <code>DBMS_STATS.GATHER_SCHEMA_STATS</code>.'
        })
    if no_act > 0:
        obs.append({
            'tipo': 'info',
            'titulo': 'Estadísticas Obsoletas',
            'mensaje': f'<strong>{no_act}</strong> tablas tienen estadísticas desactualizadas. Considerar refrescar estadísticas en horarios de baja demanda.'
        })
    
    # --- ARCHIVER ---
    instancia = datos.get('estado_instancia', {})
    archiver = instancia.get('archiver', '')
    if archiver == 'STOPPED':
        obs.append({
            'tipo': 'danger',
            'titulo': 'Archiver Detenido',
            'mensaje': 'El proceso ARCH está detenido. La base de datos puede quedarse sin espacio en <code>LOG_ARCHIVE_DEST</code> y colgarse. Verificar inmediatamente.'
        })
    
    # --- UPTIME (Mantenimiento) ---
    uptime_str = datos.get('uptime', '')
    # Extraer días del string "123 dias, ..."
    import re
    dias_up = 0
    match = re.search(r'(\d+)\s+dias?', uptime_str, re.IGNORECASE)
    if match:
        dias_up = int(match.group(1))
    
    if dias_up > 365:
        obs.append({
            'tipo': 'info',
            'titulo': 'Revisión de Mantenimiento Programado',
            'mensaje': f'El servidor lleva <strong>{dias_up}</strong> días sin reiniciar. Evaluar ventana de mantenimiento para aplicar parches y liberar recursos del SO.'
        })
    
    # Si todo está bien
    if not obs:
        obs.append({
            'tipo': 'success',
            'titulo': 'Estado General Saludable',
            'mensaje': 'No se detectaron anomalías críticas en los parámetros revisados. Continuar monitoreo rutinario.'
        })
    
    return obs