from django.urls import path
from .views.index import index
from .views.usuarios import registro_usuarios, listar_usuarios, eliminar_usuario
from .views.login import login_usuario
from .views.conexiones import registro_conexion, listar_conexiones, eliminar_conexion
from .views.inventario import listar_inventario, actualizar_inventario, asignar_cliente, eliminar_instancia
from .views.builds import listar_builds, actualizar_builds
from .views.clientes import listar_clientes, registro_cliente, modificar_cliente, eliminar_cliente
from django.contrib.auth.views import LogoutView



urlpatterns = [
    path('', index, name='index'),
    path('login/', login_usuario, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('listar_usuarios/', listar_usuarios, name='listar_usuarios'),
    path('registrar_usuarios/', registro_usuarios, name='registrar_usuarios'),
    path('eliminar_usuario/<int:id>/', eliminar_usuario, name="eliminar_usuario"),

    path('listar_conexiones/', listar_conexiones, name='listar_conexiones'),
    path('registro_conexion/', registro_conexion, name='registro_conexion'),
    path('eliminar_conexion/<int:id>/', eliminar_conexion, name='eliminar_conexion'),

    path('listar_clientes/', listar_clientes, name='listar_clientes'),
    path('registro_cliente/', registro_cliente, name='registro_cliente'),
    path('modificar_cliente/', modificar_cliente, name='modificar_cliente'),
    path('eliminar_cliente/', eliminar_cliente, name='eliminar_cliente'),

    path('listar_inventario/', listar_inventario, name='listar_inventario'),
    path('actualizar_inventario/', actualizar_inventario, name="actualizar_inventario"),
    path('asignar_cliente/', asignar_cliente, name="asignar_cliente"),
    path('eliminar_instancia/', eliminar_instancia, name='eliminar_instancia'),

    path('listar_builds/', listar_builds, name='listar_builds'),
    path('actualizar_builds/', actualizar_builds, name='actualizar_builds'),
]
