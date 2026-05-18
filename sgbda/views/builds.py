import pyodbc

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import actualizaciones

def listar_builds(request):
    
    builds = actualizaciones.objects.all()
    
    return render(request, 'paginas/builds.html', {
        "builds": builds})
