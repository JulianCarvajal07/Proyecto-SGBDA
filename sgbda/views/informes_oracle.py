from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import conexion_ssh

def informes_oracle(request):

    todas_conexiones = conexion_ssh.objects.all()
    
    return render(request, 'paginas/informes_oracle.html', {
        "conexiones": todas_conexiones
    })

