# accounts/validators.py
import re
from django.core.exceptions import ValidationError

def validate_custom_password(password):
    # 1. Longitud mínima de 8 caracteres
    if len(password) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres.")

    # 2. Al menos una mayúscula
    if not re.search(r"[A-Z]", password):
        raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")

    # 3. Al menos una minúscula
    if not re.search(r"[a-z]", password):
        raise ValidationError("La contraseña debe contener al menos una letra minúscula.")

    # 4. Al menos un carácter especial
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValidationError("La contraseña debe contener al menos un carácter especial.")

    # 5. No permitir números consecutivos
    if re.search(r"(012|123|234|345|456|567|678|789|890)", password):
        raise ValidationError("La contraseña no debe contener números consecutivos.")

    # 6. No permitir letras consecutivas (por ejemplo: abc, bcd)
    abc = "abcdefghijklmnopqrstuvwxyz"
    for i in range(len(abc) - 2):
        if abc[i:i+3] in password.lower():
            raise ValidationError("La contraseña no debe contener letras consecutivas.")

    return password
