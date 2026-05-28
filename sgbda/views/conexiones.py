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

        motor = request.POST.get('motor').strip()
        ip_servidor = request.POST.get('ip_servidor').strip()
        puerto = request.POST.get('puerto').strip()
        autenticacion = request.POST.get('autenticacion').strip()
        usuario = request.POST.get('usuario', '').strip()
        password = request.POST.get('contraseña', '').strip()

        # ==========================================
        # VALIDACIONES GENERALES
        # ==========================================
        if not all([
            motor.strip(),
            ip_servidor.strip(),
            puerto.strip(),
            autenticacion.strip()
        ]):
            messages.error(request,"IP, puerto y autenticación son obligatorios")
            return redirect ('listar_conexiones')
        
        # ==========================================
        # VALIDAR CREDENCIALES
        # ==========================================
        if autenticacion in ["Database Authentication"]:

            if not all([usuario, password]):

                messages.error(
                    request,
                    "Usuario y contraseña son obligatorios"
                )

                return redirect('listar_conexiones')


        try:

            # =====================================================
            # STRING DE CONEXION
            # =====================================================
            if motor == "SQL SERVER":

                if autenticacion == "Database Authentication":

                    conn_str = (
                        "DRIVER={ODBC Driver 18 for SQL Server};"
                        f"SERVER={ip_servidor},{puerto};"
                        f"UID={usuario};"
                        f"PWD={password};"
                        "TrustServerCertificate=yes;"
                    )
            
            if motor == "POSTGRESQL":

                if autenticacion == "Database Authentication":

                    conn_str = (
                        "DRIVER={PostgreSQL Unicode};"
                        f"SERVER={ip_servidor},{puerto};"
                        f"UID={usuario};"
                        f"PWD={password};"
                        "TrustServerCertificate=yes;"
                    )

            # =====================================================
            # TEST DE CONEXION
            # =====================================================

            with pyodbc.connect(conn_str):
                pass

            # =====================================================
            # SI CONECTA -> GUARDAR CONFIGURACION
            # =====================================================

            conexion.objects.create(
                motor = motor,
                ip_servidor=ip_servidor,
                puerto=puerto,
                tipo_autenticacion=autenticacion,
                usuario=usuario,
                password_encriptado=password
            )

            # =====================================================
            # CERRAR CONEXION
            # =====================================================

            messages.success(
                request,
                'La conexion fue existosa'
            )

        except Exception as e:

            print({str(e)})

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