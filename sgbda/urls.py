from django.urls import path
from .views.index import index
from .views.usuarios import registro_usuarios, listar_usuarios, eliminar_usuario
from .views.login import login_usuario
from .views.conexiones import registro_conexion, listar_conexiones, eliminar_conexion
from .views.inventario import listar_inventario
from .views.builds import listar_builds
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

    path('listar_inventario/', listar_inventario, name='listar_inventario'),

    path('listar_builds/', listar_builds, name='listar_builds'),
]
