from django.shortcuts import render
from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.vista_registro, name='signup'),
    path('login/', views.vista_login, name='login'),
    path('logout/', views.vista_logout, name='logout'),
    # Creamos una URL simple para la página de bienvenida
    path('home/', lambda request: render(request, 'home.html'), name='home'),
]