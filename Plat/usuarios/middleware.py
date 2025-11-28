# usuarios/middleware.py
import time
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.conf import settings
from .models import ActiveSession
from .utils import session_key_exists

class CleanStaleActiveSessionsMiddleware:
    """
    Elimina ActiveSession cuyo session_key ya no existe (sesión expirada/eliminada).
    Ejecutarlo temprano en la cadena de middlewares.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        stale = []
        for asess in ActiveSession.objects.all():
            if not session_key_exists(asess.session_key):
                stale.append(asess.pk)
        if stale:
            ActiveSession.objects.filter(pk__in=stale).delete()
        return self.get_response(request)


class SessionIdleTimeoutMiddleware:
    """
    Expira la sesión por inactividad solo en la ruta 'home' (p. ej. /home/).
    Excluye login/signup/logout, rutas estáticas, admin y captcha para evitar que la expiración
    interrumpa el flujo de registro o acceso.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 60)

        # preparar rutas exentas y home
        try:
            self.login_url = reverse('login')
            self.logout_url = reverse('logout')
            self.signup_url = reverse('signup')
            self.home_url = reverse('home')
        except NoReverseMatch:
            # fallbacks si todavía no están definidas las URLs
            self.login_url = '/login/'
            self.logout_url = '/logout/'
            self.signup_url = '/signup/'
            self.home_url = '/home/'

        # normalizar: asegurar trailing slash en las comparaciones
        def norm(u):
            if not u.endswith('/'):
                return u + '/'
            return u

        self.login_url = norm(self.login_url)
        self.logout_url = norm(self.logout_url)
        self.signup_url = norm(self.signup_url)
        self.home_url = norm(self.home_url)

        # prefijos públicos adicionales
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        if not static_url.startswith('/'):
            static_url = '/' + static_url
        if not static_url.endswith('/'):
            static_url = static_url + '/'
        self.static_prefix = static_url

        # rutas que deben estar exentas (comprobación por startswith)
        self.exempt_prefixes = [
            self.static_prefix,
            '/admin/',
            '/captcha/',
        ]
        # también añadir las rutas login/signup/logout (exact match with trailing slash)
        self.exempt_exact = {self.login_url, self.logout_url, self.signup_url}

    def __call__(self, request):
        path = request.path
        # normalizar path para comparación
        if not path.endswith('/'):
            path_cmp = path + '/'
        else:
            path_cmp = path

        # Si la ruta es exactamente una de las exentas -> no aplicar timeout
        if path_cmp in self.exempt_exact:
            return self.get_response(request)

        # Si la ruta comienza por un prefijo público (static, admin, captcha) -> no aplicar
        for pref in self.exempt_prefixes:
            if path.startswith(pref):
                return self.get_response(request)

        # IMPORTANT: sólo aplicar la expiración **si la ruta comienza por home_url**
        if not path_cmp.startswith(self.home_url):
            # no estamos en /home ni en sus subrutas -> no aplicar timeout
            return self.get_response(request)

        # A partir de aquí: estamos en /home (o subruta) -> aplicar lógica de timeout
        session = getattr(request, 'session', None)
        if session is None:
            return self.get_response(request)

        now = int(time.time())
        last_activity = session.get('last_activity')

        if request.user.is_authenticated:
            if last_activity and (now - last_activity > self.timeout):
                # expiró por inactividad: eliminar ActiveSession y vaciar session
                try:
                    ActiveSession.objects.filter(user=request.user).delete()
                except Exception:
                    pass
                try:
                    session.flush()
                except Exception:
                    session.clear()
                return redirect(f'{self.login_url}?session_expired=1')
            # actualizar timestamp de última actividad en /home
            session['last_activity'] = now
        else:
            # Si no está autenticado, no aplicamos bloqueo en /home; simplemente seguimos
            session['last_activity'] = now

        return self.get_response(request)