from django.urls import path
from . import views

urlpatterns = [
    # Admin
    path('appointments/new/',                          views.CreateAppointmentView.as_view(),    name='create_appointment'),
    path('appointments/<int:appointment_id>/cancel/',  views.CancelAppointmentView.as_view(),    name='cancel_appointment'),

    # Doctor
    path('appointments/<int:appointment_id>/complete/', views.CompleteConsultationView.as_view(), name='complete_consultation'),

    # Parent
    path('patients/<int:patient_id>/history/',         views.PatientHistoryView.as_view(),       name='patient_history'),
]