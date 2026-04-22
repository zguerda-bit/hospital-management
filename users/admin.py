from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Address, Users, Specialty, Doctors, Patients, Reste_token, TraceAction


@admin.register(Users)
class UsersAdmin(UserAdmin):
    list_display  = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter   = ('role', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets     = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'phone', 'address')}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display  = ('address_line', 'city', 'region', 'code_postal')
    search_fields = ('city', 'region', 'address_line')


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display  = ('name',)
    search_fields = ('name',)


@admin.register(Doctors)
class DoctorsAdmin(admin.ModelAdmin):
    list_display  = ('user', 'specialty', 'ville', 'actif')
    list_filter   = ('specialty', 'actif')
    search_fields = ('user__username', 'user__last_name', 'ville')


@admin.register(Patients)
class PatientsAdmin(admin.ModelAdmin):
    list_display  = ('first_name', 'last_name', 'birth_date', 'gender', 'groupe_sanguin', 'parent', 'date_creation_dossier')
    list_filter   = ('gender', 'groupe_sanguin')
    search_fields = ('first_name', 'last_name', 'parent__username', 'email')


@admin.register(Reste_token)
class ResetTokenAdmin(admin.ModelAdmin):
    list_display  = ('user', 'token', 'created_at', 'expires_at')
    search_fields = ('user__username',)


@admin.register(TraceAction)
class TraceActionAdmin(admin.ModelAdmin):
    list_display    = ('user', 'action', 'table_concernee', 'timestamp')
    list_filter     = ('action', 'table_concernee')
    search_fields   = ('user__username', 'action')
    readonly_fields = ('timestamp',)