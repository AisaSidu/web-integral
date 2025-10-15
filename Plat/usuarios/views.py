from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from usuarios.Cuentas.formulario import CustomUserCreationForm


def vista_registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)  # Inicia sesión automáticamente
            return redirect('home')  # Redirige a la página de inicio
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})


def vista_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def vista_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
