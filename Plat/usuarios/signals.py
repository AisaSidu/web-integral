# usuarios/signals.py
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import ActiveSession
from .models import Profile


User = get_user_model()

@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(user_logged_out)
def remove_active_session_on_logout(sender, request, user, **kwargs):
    if user:
        ActiveSession.objects.filter(user=user).delete()
