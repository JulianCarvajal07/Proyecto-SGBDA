from django.urls import path
from .views.index import index
from .views.usuarios import registro_usuarios, listar_usuarios
from .views.login import login_usuario
from .views.bases_de_datos import bases_de_datos 
from django.contrib.auth.views import LogoutView



urlpatterns = [
    path('', index, name='index'),
    path('login/', login_usuario, name='login'),
    path('inicio/', bases_de_datos, name='bases_de_datos'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('listar_usuarios/', listar_usuarios, name='listar_usuarios'),
    path('registrar_usuarios/', registro_usuarios, name='registrar_usuarios'),
]
