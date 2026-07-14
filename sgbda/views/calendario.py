# views/calendario.py
 
import calendar
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from ..models import Asignacion, cliente
 
 
def calendario_view(request, year=None, month=None):

    context = obtener_contexto_calendario(year, month)
 
    if request.headers.get('HX-Request') == 'true':
        html = render_to_string('paginas/calendario_fragmento.html', context)
        return HttpResponse(html)
 
    return render(request, 'paginas/calendario.html', context)
 

def obtener_contexto_calendario (year=None, month=None):

    hoy = date.today()
    year = year or hoy.year
    month = month or hoy.month
 
    # === ASIGNACIONES DEL MES ===
    # Ya no hay cálculo de patrones: todo registro tiene fecha_exacta,
    # así que basta con filtrar directo por año/mes.
    asignaciones = {}  # {dia: [asignaciones]}
    for asig in Asignacion.objects.filter(
        fecha_exacta__year=year,
        fecha_exacta__month=month
    ).select_related('cliente'):
        dia = asig.fecha_exacta.day
        asignaciones.setdefault(dia, []).append(asig)
 
    # === CALENDARIO ===
    cal = calendar.Calendar()
    semanas_raw = cal.monthdayscalendar(year, month)
 
    # Enriquecer con metadatos
    semanas = []
    for semana in semanas_raw:
        semana_meta = []
        for dia in semana:
            if dia == 0:
                semana_meta.append({'dia': 0})
            else:
                fecha = date(year, month, dia)
                dia_semana = fecha.weekday()
 
                # Posición del día dentro del mes (1er, 2do, 3er... lunes/martes/etc.)
                # Se sigue calculando solo para mostrarlo en el modal de creación,
                # ya NO se usa para derivar asignaciones.
                posicion_mes = (dia - 1) // 7 + 1
 
                semana_meta.append({
                    'dia': dia,
                    'dia_semana': dia_semana,
                    'posicion_mes': min(posicion_mes, 5),
                    'asignaciones': asignaciones.get(dia, []),
                })
        semanas.append(semana_meta)
 
    # Navegación
    mes_ant = month - 1 if month > 1 else 12
    ano_ant = year if month > 1 else year - 1
    mes_sig = month + 1 if month < 12 else 1
    ano_sig = year if month < 12 else year + 1
 
    # Clientes para el modal
    clientes = cliente.objects.all()
 
    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'semanas': semanas,
        'hoy': hoy,
        'mes_ant': mes_ant,
        'ano_ant': ano_ant,
        'mes_sig': mes_sig,
        'ano_sig': ano_sig,
        'clientes': clientes,
    }

    return context


def crear_asignacion(request):
    try:
        cliente_obj = cliente.objects.get(
            id_cliente=request.POST.get("cliente")
        )

        fecha = datetime.strptime(
            request.POST.get("fecha_exacta"),
            "%Y-%m-%d"
        ).date()

        Asignacion.objects.create(
            cliente=cliente_obj,
            motivo=request.POST.get("motivo"),
            fecha_exacta=fecha,
        )

        context = obtener_contexto_calendario(
            fecha.year,
            fecha.month
        )

        return render(
            request,
            "paginas/calendario_fragmento.html",
            context
        )

    except Exception as e:
        return HttpResponse(str(e), status=400)
 
 
@require_POST
def eliminar_asignacion(request):
    asignacion_id = request.POST.get("asignacion-id")
 
    if not asignacion_id:
        messages.error(request, "Error, no se especificó una asignación")
        return redirect('calendario')
 
    asignacion_obj = get_object_or_404(Asignacion, id=asignacion_id)

    fecha = asignacion_obj.fecha_exacta

    asignacion_obj.delete()
    
    context = obtener_contexto_calendario(fecha.year, fecha.month)
    # messages.success(request, "Se ha eliminado la asignación")
    
    return render(request, "paginas/calendario_fragmento.html",context)