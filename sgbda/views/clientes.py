from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import instancia, cliente, servidor

def listar_clientes(request):

    all_clientes = cliente.objects.all()

    return render(request, 'paginas/clientes.html',{
        'clientes': all_clientes,
    })

def registro_cliente(request):
        

    return render(request, 'paginas/clientes.html')


