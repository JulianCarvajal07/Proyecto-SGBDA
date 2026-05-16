import pyodbc

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import conexion

def listar_inventario(request):
    
   
    
    return render(request, 'paginas/inventario.html')
