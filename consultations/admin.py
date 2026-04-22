from django.contrib import admin
from .models import Appointment, Consultation, Diagnostic, Traitement


class DiagnosticInline(admin.TabularInline):
    model = Diagnostic
    extra = 0
    min_num = 1


class TraitementInline(admin.TabularInline):
    model = Traitement
    extra = 0
    min_num = 1


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date_rdv', 'status', 'created_by')
    list_filter = ('status', 'doctor__specialty')
    search_fields = (
        'patient__first_name',
        'patient__last_name',
        'doctor__user__last_name',
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date_rdv'


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'date_consultation', 'poids', 'taille', 'temperature')
    inlines = [DiagnosticInline, TraitementInline]
    search_fields = (
        'appointment__patient__first_name',
        'appointment__patient__last_name',
    )
    readonly_fields = ('date_consultation',)


@admin.register(Diagnostic)
class DiagnosticAdmin(admin.ModelAdmin):
    list_display = ('nom_maladie', 'type_maladie', 'gravite', 'consultation')
    list_filter = ('type_maladie', 'gravite')
    search_fields = ('nom_maladie',)


@admin.register(Traitement)
class TraitementAdmin(admin.ModelAdmin):
    list_display = ('medicament', 'dose', 'duree', 'consultation')
    search_fields = ('medicament',)