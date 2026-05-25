import pyodbc

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import conexion

def listar_conexiones(request):
    
    todas_conexiones = conexion.objects.all()
    
    return render(request, 'paginas/conexiones.html', {
        "conexiones": todas_conexiones
    })

def registro_conexion(request):

    if request.method == 'POST':

        ip_servidor = request.POST.get('ip_servidor').strip()
        puerto = request.POST.get('puerto').strip()
        autenticacion = request.POST.get('autenticacion').strip()
        usuario = request.POST.get('usuario').strip()
        password = request.POST.get('contraseña').strip()

        if not all([
            ip_servidor.strip(),
            puerto.strip(),
            autenticacion.strip(),
            usuario.strip(),
            password.strip()
        ]):
            messages.error(request,"Todos los campos son obligatorios")
            return redirect ('listar_conexiones')


        try:

            # =====================================================
            # STRING DE CONEXION
            # =====================================================

            conn_str = (
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={ip_servidor},{puerto};"
                f"UID={usuario};"
                f"PWD={password};"
                "TrustServerCertificate=yes;"
                "Connection Timeout=5;"
            )

            # =====================================================
            # TEST DE CONEXION
            # =====================================================

            conexion_sql = pyodbc.connect(conn_str)

            # =====================================================
            # SI CONECTA -> GUARDAR CONFIGURACION
            # =====================================================

            conexion.objects.create(
                ip_servidor=ip_servidor,
                puerto=puerto,
                tipo_autenticacion=autenticacion,
                usuario=usuario,
                password_encriptado=password
            )

            # =====================================================
            # CERRAR CONEXION
            # =====================================================

            conexion_sql.close()

            messages.success(
                request,
                'La conexion fue existosa'
            )

        except Exception as e:

            messages.error(
                request,
                f'Error de conexion: {str(e)}'
            )

        return redirect('listar_conexiones')

    return render(request, 'paginas/conexiones.html')


def eliminar_conexion(request, id):

    if request.method == "POST":
        eliminar = get_object_or_404(conexion, id=id)
        eliminar.delete()
        messages.success(request, "conexion eliminada correctamente")

    return redirect("listar_conexiones")