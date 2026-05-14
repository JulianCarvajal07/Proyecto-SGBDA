from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_usuario, name='login'),
    path('inicio/', views.bases_de_datos, name='bases_de_datos'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('usuarios/', views.usuarios, name='usuarios'),
]
