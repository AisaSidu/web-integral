#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import ssl

# --- INICIO DEL PARCHE (ESTO ES LO QUE FALTABA) ---
def patched_wrap_socket(sock, keyfile=None, certfile=None, **kwargs):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile, keyfile)
    return context.wrap_socket(sock, server_side=True)

# Aplicamos el parche solo si la función no existe (Python 3.12+)
if not hasattr(ssl, 'wrap_socket'):
    ssl.wrap_socket = patched_wrap_socket

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Plat.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
