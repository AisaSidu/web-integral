# usuarios/models.py
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class ActiveSession(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='active_session')
    session_key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.session_key}"


class FailedLoginAttempt(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    failed_attempts = models.PositiveIntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)

    def is_locked(self):
        return self.lockout_until and self.lockout_until > timezone.now()

    def reset(self):
        self.failed_attempts = 0
        self.lockout_until = None
        self.save()

    def register_failure(self):
        self.failed_attempts += 1
        if self.failed_attempts >= 3:
            self.lockout_until = timezone.now() + timedelta(minutes=5)  # bloqueado por 5 min
        self.save()

    def __str__(self):
        return f"{self.user.username} - attempts: {self.failed_attempts}"


# ---------------------------
# Models for roles / catálogo
# ---------------------------

class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Specialty"
        verbose_name_plural = "Specialties"
        ordering = ['name']

    def __str__(self):
        return self.name


class Profile(models.Model):
    ROLE_PATIENT = 'patient'
    ROLE_PSYCHOLOGIST = 'psychologist'
    ROLE_CHOICES = (
        (ROLE_PATIENT, 'Patient'),
        (ROLE_PSYCHOLOGIST, 'Psychologist'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_PATIENT)

    # common fields
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)

    # psychologist-specific fields
    license_number = models.CharField(max_length=150, blank=True, null=True)
    specialties = models.ManyToManyField(Specialty, blank=True, related_name='psychologists')
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_psychologist(self):
        return self.role == self.ROLE_PSYCHOLOGIST

    def is_patient(self):
        return self.role == self.ROLE_PATIENT

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role})"


class Document(models.Model):
    DOCUMENT_TYPES = (
        ('license', 'License'),
        ('id', 'Identity Document'),
        ('cv', 'CV'),
    )
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)  # admin marks True after verification

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.profile.user.username} - {self.doc_type}"


class AvailabilitySlot(models.Model):
    WEEKDAYS = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='availability')
    weekday = models.IntegerField(choices=WEEKDAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['weekday', 'start_time']

    def __str__(self):
        return f"{self.profile.user.username} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"
