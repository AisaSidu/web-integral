# usuarios/Cuentas/verificacion.py
import re
from django.core.exceptions import ValidationError

def validate_custom_password(password):
    if not password:
        raise ValidationError("Se requiere una contraseña.")

    if len(password) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres.")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")

    if not re.search(r"[a-z]", password):
        raise ValidationError("La contraseña debe contener al menos una letra minúscula.")

    if not re.search(r"\d", password):
        raise ValidationError("La contraseña debe contener al menos un número.")

    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValidationError("La contraseña debe contener al menos un carácter especial.")

    # No permitir dos letras mayúsculas consecutivas (por ejemplo: "AB" o "ÑÁ")
    for i in range(len(password) - 1):
        if password[i].isupper() and password[i+1].isupper():
            raise ValidationError("La contraseña no debe contener dos letras mayúsculas consecutivas.")

    # No permitir números consecutivos como '012','123', etc.
    if re.search(r"(012|123|234|345|456|567|678|789|890)", password):
        raise ValidationError("La contraseña no debe contener números consecutivos.")

    # No permitir letras consecutivas en orden alfabético (por ejemplo: 'abc', 'bcd')
    abc = "abcdefghijklmnopqrstuvwxyz"
    for i in range(len(abc) - 2):
        if abc[i:i+3] in password.lower():
            raise ValidationError("La contraseña no debe contener letras consecutivas.")

    return password
