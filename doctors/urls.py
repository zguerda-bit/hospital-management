from django.urls import path
from .views import (
    DoctorDashboardView,
    DoctorProfileView,
    DoctorAppointmentsView,
    DoctorConsultationsView,
    DoctorDiagnosticsView,
    DoctorTreatmentsView,
)

urlpatterns = [
    path('dashboard/',     DoctorDashboardView.as_view(),     name='doctor_dashboard'),
    path('profile/',       DoctorProfileView.as_view(),       name='doctor_profile'),
    path('appointments/',  DoctorAppointmentsView.as_view(),  name='doctor_appointments'),
    path('consultations/', DoctorConsultationsView.as_view(), name='doctor_consultations'),
    path('diagnostics/',   DoctorDiagnosticsView.as_view(),   name='doctor_diagnostics'),
    path('treatments/',    DoctorTreatmentsView.as_view(),    name='doctor_treatments'),
]