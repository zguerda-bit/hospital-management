from django.urls import path
from .views import (
    PatientDashboardView,
    PatientProfileView,
    MyAppointmentsView,
    BookAppointmentView,
    ConfirmBookAppointmentView,
)

urlpatterns = [
    path('dashboard/',                        PatientDashboardView.as_view(),       name='patient_dashboard'),
    path('profile/',                          PatientProfileView.as_view(),          name='patient_profile'),
    path('appointments/',                     MyAppointmentsView.as_view(),          name='my_appointments'),
    path('book/',                             BookAppointmentView.as_view(),         name='book_appointment'),
    path('book/confirm/<int:doctor_id>/',     ConfirmBookAppointmentView.as_view(),  name='confirm_book'),
]