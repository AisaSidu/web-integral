from django.contrib import admin
from .models import Profile, Specialty, Document, AvailabilitySlot

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    search_fields = ['name']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_verified', 'license_number', 'hourly_rate')
    list_filter = ('role', 'is_verified', 'specialties')
    search_fields = ('user__username', 'user__email', 'license_number', 'bio')
    filter_horizontal = ('specialties',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('profile', 'doc_type', 'uploaded_at', 'accepted')
    list_filter = ('doc_type', 'accepted')
    search_fields = ('profile__user__username',)

    actions = ['accept_and_verify']

    def accept_and_verify(self, request, queryset):
        """Marcar documentos como aceptados y verificar el perfil asociado."""
        count = 0
        for doc in queryset:
            if not doc.accepted:
                doc.accepted = True
                doc.save()
            profile = doc.profile
            if not profile.is_verified:
                profile.is_verified = True
                profile.save()
            count += 1
        self.message_user(request, f"{count} documento(s) aceptado(s) y perfiles verificados cuando correspondía.")
    accept_and_verify.short_description = "Aceptar documentos y verificar perfil"


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('profile', 'weekday', 'start_time', 'end_time')
    list_filter = ('weekday',)
