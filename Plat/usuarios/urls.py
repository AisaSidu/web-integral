# usuarios/urls.py
from django.shortcuts import render
from django.urls import path
from . import views

urlpatterns = [
    path('', views.vista_root, name='root'),
    path('signup/', views.vista_registro, name='signup'),
    path('login/', views.vista_login, name='login'),
    path('logout/', views.vista_logout, name='logout'),
    path('home/', lambda request: render(request, 'home.html'), name='home'),
    path('psych/onboarding/', views.psych_onboarding, name='psych_onboarding'),
    path('aviso_privacidad/', views.aviso_privacidad, name='aviso_privacidad'),

]
