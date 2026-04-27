from django.urls import path
from .views import (
    AdminDashboardView,
    AdminUserListView, AdminUserDetailView, AdminUserToggleActiveView,
    AdminDoctorListView, AdminDoctorDetailView, AdminDoctorToggleActiveView,
    AdminPatientListView, AdminPatientDetailView,
    AdminAppointmentListView, AdminAppointmentDetailView, AdminAppointmentStatusView,
)

urlpatterns = [

    # Dashboard
    path('dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),

    # Users
    path('users/',                        AdminUserListView.as_view(),         name='admin_user_list'),
    path('users/<int:user_id>/',          AdminUserDetailView.as_view(),       name='admin_user_detail'),
    path('users/<int:user_id>/toggle-active/', AdminUserToggleActiveView.as_view(), name='admin_user_toggle'),

    # Doctors
    path('doctors/',                           AdminDoctorListView.as_view(),         name='admin_doctor_list'),
    path('doctors/<int:doctor_id>/',           AdminDoctorDetailView.as_view(),       name='admin_doctor_detail'),
    path('doctors/<int:doctor_id>/toggle-active/', AdminDoctorToggleActiveView.as_view(), name='admin_doctor_toggle'),

    # Patients
    path('patients/',                    AdminPatientListView.as_view(),   name='admin_patient_list'),
    path('patients/<int:patient_id>/',   AdminPatientDetailView.as_view(), name='admin_patient_detail'),

    # Appointments
    path('appointments/',                          AdminAppointmentListView.as_view(),   name='admin_appointment_list'),
    path('appointments/<int:appointment_id>/',     AdminAppointmentDetailView.as_view(), name='admin_appointment_detail'),
    path('appointments/<int:appointment_id>/status/', AdminAppointmentStatusView.as_view(), name='admin_appointment_status'),
]