from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import conexion_ssh

def informes_oracle(request):

    return render (request, 'paginas/informes_oracle.html')