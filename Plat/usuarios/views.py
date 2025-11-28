# usuarios/views.py
import time
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import Group

from usuarios.Cuentas.formulario import CustomUserCreationForm
from .models import ActiveSession, FailedLoginAttempt, Document
from .utils import session_key_exists
from django.contrib.auth.decorators import login_required

User = get_user_model()


def vista_root(request):
    """
    Redirige automáticamente:
    - a 'home' si el usuario está autenticado y su sesión es válida y no expiró por inactividad,
    - a 'login' en caso contrario.
    """
    if not request.user.is_authenticated:
        return redirect('login')

    session_key = request.session.session_key
    now = int(time.time())
    idle_timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 60)

    if session_key and session_key_exists(session_key):
        last_activity = request.session.get('last_activity')
        # Si no hay last_activity registrado, consideramos la sesión válida
        if last_activity is None or (now - int(last_activity) <= idle_timeout):
            return redirect('home')
        else:
            try:
                ActiveSession.objects.filter(user=request.user).delete()
            except Exception:
                pass
            try:
                request.session.flush()
            except Exception:
                request.session.clear()
            return redirect('login')

    try:
        active = ActiveSession.objects.get(user=request.user)
        if active.session_key and session_key_exists(active.session_key):
            return redirect('login')
    except ActiveSession.DoesNotExist:
        pass

    return redirect('login')


def vista_registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # crear usuario pero aún no commit para asegurar email y luego profile
            usuario = form.save(commit=False)
            usuario.email = form.cleaned_data.get('email')
            usuario.save()

            # actualizar profile creado por signal
            profile = usuario.profile
            role = form.cleaned_data.get('role')
            profile.role = role
            profile.phone = form.cleaned_data.get('phone') or ''
            if role == 'psychologist':
                profile.license_number = form.cleaned_data.get('license_number') or ''
                profile.is_verified = False
                profile.save()
                specs = form.cleaned_data.get('specialties')
                if specs:
                    profile.specialties.set(specs)
            else:
                profile.save()

            # asignar grupo adecuado
            group_name = 'psychologist' if role == 'psychologist' else 'patient'
            group, _ = Group.objects.get_or_create(name=group_name)
            usuario.groups.add(group)

            # iniciar sesión y registrar ActiveSession
            login(request, usuario)
            if request.session.session_key is None:
                request.session.create()
            ActiveSession.objects.update_or_create(user=usuario, defaults={'session_key': request.session.session_key})

            # si es psicólogo, redirigir al onboarding para subir documentos/verificación
            if profile.is_psychologist():
                return redirect('psych_onboarding')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})


def vista_login(request):
    raw_next = request.POST.get('next') or request.GET.get('next')
    next_url = raw_next if raw_next and raw_next != 'None' else None

    if request.GET.get('session_expired') == '1':
        messages.warning(request, "Tu sesión expiró por inactividad. Vuelve a iniciar sesión.")

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        username = request.POST.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                failed, _ = FailedLoginAttempt.objects.get_or_create(user=user)

                # Si la cuenta está bloqueada (FailedLoginAttempt usa timezone)
                if failed.is_locked():
                    remaining_seconds = int((failed.lockout_until - timezone.now()).total_seconds())
                    remaining_minutes = max(0, remaining_seconds // 60)
                    messages.error(request, f"Tu cuenta está bloqueada. Intenta nuevamente en {remaining_minutes} minutos.")
                    return render(request, 'login.html', {'form': form, 'next': next_url})
            except User.DoesNotExist:
                # Usuario no existe (no registrar intentos para evitar enumeración)
                pass

        if form.is_valid():
            usuario = form.get_user()

            # Reiniciar intentos fallidos si inicia sesión correctamente
            FailedLoginAttempt.objects.filter(user=usuario).update(failed_attempts=0, lockout_until=None)

            # --- Lógica de sesiones activas ---
            if request.session.session_key is None:
                request.session.create()
            current_key = request.session.session_key

            try:
                active = ActiveSession.objects.get(user=usuario)
                if active.session_key and active.session_key != current_key:
                    if session_key_exists(active.session_key):
                        messages.error(
                            request,
                            "Tienes una sesión activa, continúa ahí o finalízala para seguir aquí"
                        )
                        return render(request, 'login.html', {'form': form, 'next': next_url})
                    else:
                        active.session_key = current_key
                        active.save()
                else:
                    active.session_key = current_key
                    active.save()
            except ActiveSession.DoesNotExist:
                ActiveSession.objects.create(user=usuario, session_key=current_key)
            # --- Fin de manejo de sesión activa ---

            login(request, usuario)

            # redirección según rol / verificación
            try:
                profile = usuario.profile
                if profile.is_psychologist():
                    if not profile.is_verified:
                        return redirect('psych_onboarding')
                    # si está verificado, podrías redirigir a un dashboard específico
                    return redirect(next_url or 'home')
            except Exception:
                # por seguridad, si algo falla con profile, ir a home
                pass

            return redirect(next_url or 'home')

        else:
            # Si el login falla, registrar intento
            if username:
                try:
                    user = User.objects.get(username=username)
                    failed, _ = FailedLoginAttempt.objects.get_or_create(user=user)
                    failed.register_failure()

                    if failed.failed_attempts >= 3:
                        messages.error(request, "Has superado los 3 intentos. Tu cuenta está bloqueada por 5 minutos.")
                    else:
                        remaining = 3 - failed.failed_attempts
                        messages.error(request, f"Contraseña incorrecta. Te quedan {remaining} intentos.")
                except User.DoesNotExist:
                    pass

    else:
        form = AuthenticationForm(request)

    return render(request, 'login.html', {'form': form, 'next': next_url})


def vista_logout(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            ActiveSession.objects.filter(user=request.user).delete()
        logout(request)
        return redirect('login')
    return render(request, 'logout_confirm.html')


def aviso_privacidad(request):
    return render(request, 'Usuarios/aviso_privacidad.html')


@login_required
def psych_onboarding(request):
    profile = getattr(request.user, 'profile', None)
    if profile is None or not profile.is_psychologist():
        return redirect('home')

    if profile.is_verified:
        return redirect('home')  # o a un dashboard si lo creas

    class DocForm(forms.Form):
        doc_type = forms.ChoiceField(choices=(('license','License'),('id','ID'),('cv','CV')))
        file = forms.FileField()

    uploaded = False
    if request.method == 'POST':
        form = DocForm(request.POST, request.FILES)
        if form.is_valid():
            # crear Document; admin lo marcará como accepted más tarde
            Document.objects.create(
                profile=profile,
                doc_type=form.cleaned_data['doc_type'],
                file=request.FILES['file'],
                accepted=False
            )
            uploaded = True
    else:
        form = DocForm()

    documents = profile.documents.all()
    return render(request, 'usuarios/psych_onboarding.html', {
        'profile': profile,
        'form': form,
        'documents': documents,
        'uploaded': uploaded,
    })