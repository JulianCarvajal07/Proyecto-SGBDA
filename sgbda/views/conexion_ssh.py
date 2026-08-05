import paramiko, ipaddress

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import conexion_ssh

def listar_conexiones_ssh(request):
    
    todas_conexiones = conexion_ssh.objects.all()
    
    return render(request, 'paginas/conexiones/conexion_ssh.html', {
        "conexiones": todas_conexiones
    })


def registro_conexion_ssh(request):

    if request.method == 'POST':

        ip_servidor = request.POST.get('ip_servidor', '').strip()
        puerto = request.POST.get('puerto', '').strip()
        usuario = request.POST.get('usuario', '').strip()
        password = request.POST.get('contraseña', '').strip()

        # ==========================================
        # VALIDACION DE CREDENCIALES
        # ==========================================
        if not all([

            ip_servidor.strip(),
            puerto.strip(),
            usuario.strip(),
            password.strip()
        ]):
            messages.error(request,"IP, puerto y autenticación son obligatorios")
            return redirect ('listar_conexiones_ssh')

        try:
            ipaddress.ip_address(ip_servidor)
        except ValueError:
            messages.error(request, "La dirección IP no es válida.")
            return redirect ('listar_conexiones_ssh')
        
        # ==========================================
        # VALIDAR CREDENCIALES
        # ==========================================
            
        if conexion_ssh.objects.filter(
            ip_servidor=ip_servidor, 
            usuario=usuario, 
        ).exists():
            messages.error(request, "Esta conexion ya existe en la base de datos")
            return redirect ('listar_conexiones_ssh')
        
        try:
            
            # =====================================================
            # STRING DE CONEXION / TEST DE CONEXION
            # =====================================================
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(
                hostname = ip_servidor,
                port = puerto,
                username = usuario,
                password = password,
                timeout = 5,
            )

            # =====================================================
            # SI CONECTA -> GUARDAR CONFIGURACION
            # =====================================================
            conexion_ssh.objects.create(
                ip_servidor=ip_servidor,
                puerto=puerto,
                usuario=usuario,
                password_encriptado=password,
            )

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

        finally:
            # =====================================================
            # CERRAR CONEXION
            # =====================================================
            if ssh is not None:
                ssh.close()

        return redirect('listar_conexiones_ssh')

    return render(request, 'paginas/conexiones/conexion_ssh.html')


def eliminar_conexion_ssh(request, id):

    if request.method == "POST":
        eliminar = get_object_or_404(conexion_ssh, id=id)
        eliminar.delete()
        messages.success(request, "conexion eliminada correctamente")

    return redirect("listar_conexiones_ssh")

