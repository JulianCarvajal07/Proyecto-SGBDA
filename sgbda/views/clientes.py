from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from sgbda.models import instancia, cliente, servidor

def listar_clientes(request):

    all_clientes = cliente.objects.all()

    return render(request, 'paginas/clientes.html',{
        'clientes': all_clientes,
    })

def registro_cliente(request):

    if request.method == 'POST':
        nombre_cliente = request.POST.get('nombre')

        if nombre_cliente:
            
            cliente.objects.create(
                nombre = nombre_cliente 
            )
            
            messages.success(request, "Cliente registrado correctamente")
            return redirect("listar_clientes")
        
        else:

            messages.error(request, "Ingrese un cliente")
            return redirect("listar_clientes")

def modificar_cliente(request):

    if request.method == 'POST':
        nombre_cliente = request.POST.get('nombre_cliente')
        cliente_id= request.POST.get('id_cliente')

        if nombre_cliente:

            cliente_obj = cliente.objects.get(id_cliente=cliente_id)
            cliente_obj.nombre = nombre_cliente
            cliente_obj.save()
            messages.success(request, "cliente actualizado exitosamente")
            return redirect('listar_clientes')

        else: 

            messages.error(request, "Debe registrar nombre de cliente")
            return redirect('listar_clientes')
        

            
