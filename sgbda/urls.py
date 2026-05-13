from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_usuario, name='login'),
    path('inicio/', views.bases_de_datos, name='bases_de_datos'),
]
