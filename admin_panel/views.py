from django.shortcuts import get_object_or_404
from django.db.models import Count, Q

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.models import Users, Doctors, Patients, TraceAction
from consultations.models import Appointment
from users.permissions import IsAdmin
from .serializers import (
    AdminUserSerializer, AdminUserCreateSerializer,
    AdminDoctorSerializer, AdminDoctorCreateSerializer,
    AdminPatientSerializer, AdminAppointmentSerializer,
)


def _log(user, action, table=""):
    TraceAction.objects.create(user=user, action=action, table_concernee=table)


# ─── Dashboard ────────────────────────────────────────────────────────────────

class AdminDashboardView(APIView):
    """GET /api/admin/dashboard/ — global stats for the admin home screen."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        total_doctors      = Doctors.objects.filter(actif=True).count()
        total_patients     = Patients.objects.count()
        total_parents      = Users.objects.filter(role='PARENT').count()
        total_appointments = Appointment.objects.count()

        appointments_by_status = {
            'pending':   Appointment.objects.filter(status='PENDING').count(),
            'confirmed': Appointment.objects.filter(status='CONFIRMED').count(),
            'completed': Appointment.objects.filter(status='COMPLETED').count(),
            'cancelled': Appointment.objects.filter(status='CANCELLED').count(),
        }

        recent_appointments = (
            Appointment.objects
            .select_related('doctor__user', 'patient')
            .order_by('-created_at')[:5]
        )

        return Response({
            'stats': {
                'total_doctors':      total_doctors,
                'total_patients':     total_patients,
                'total_parents':      total_parents,
                'total_appointments': total_appointments,
            },
            'appointments_by_status': appointments_by_status,
            'recent_appointments': AdminAppointmentSerializer(recent_appointments, many=True).data,
        })


# ─── Users ────────────────────────────────────────────────────────────────────

class AdminUserListView(APIView):
    """
    GET  /api/admin/users/       — list all users (filter by role)
    POST /api/admin/users/       — create a new user (PARENT or ADMIN)
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        users = Users.objects.all().order_by('-date_joined')

        role   = request.query_params.get('role', '').strip()
        search = request.query_params.get('search', '').strip()
        active = request.query_params.get('active', '').strip()

        if role:
            users = users.filter(role=role)
        if search:
            users = users.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)  |
                Q(email__icontains=search)       |
                Q(username__icontains=search)
            )
        if active in ('true', 'false'):
            users = users.filter(is_active=(active == 'true'))

        return Response(AdminUserSerializer(users, many=True).data)

    def post(self, request):
        serializer = AdminUserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        _log(request.user, 'CREATE_USER', 'Users')
        return Response(AdminUserSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminUserDetailView(APIView):
    """
    GET    /api/admin/users/<id>/  — get one user
    PATCH  /api/admin/users/<id>/  — edit user info
    DELETE /api/admin/users/<id>/  — delete user
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, user_id):
        user = get_object_or_404(Users, id=user_id)
        return Response(AdminUserSerializer(user).data)

    def patch(self, request, user_id):
        user = get_object_or_404(Users, id=user_id)
        serializer = AdminUserSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        _log(request.user, 'UPDATE_USER', 'Users')
        return Response(serializer.data)

    def delete(self, request, user_id):
        user = get_object_or_404(Users, id=user_id)
        if user == request.user:
            return Response(
                {'detail': 'Vous ne pouvez pas supprimer votre propre compte.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.delete()
        _log(request.user, 'DELETE_USER', 'Users')
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserToggleActiveView(APIView):
    """PATCH /api/admin/users/<id>/toggle-active/ — activate or deactivate a user."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, user_id):
        user = get_object_or_404(Users, id=user_id)
        if user == request.user:
            return Response(
                {'detail': 'Vous ne pouvez pas désactiver votre propre compte.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = not user.is_active
        user.save()
        state = 'activé' if user.is_active else 'désactivé'
        _log(request.user, f'USER_{state.upper()}', 'Users')
        return Response({'detail': f'Compte {state}.', 'is_active': user.is_active})


# ─── Doctors ──────────────────────────────────────────────────────────────────

class AdminDoctorListView(APIView):
    """
    GET  /api/admin/doctors/  — list all doctors
    POST /api/admin/doctors/  — create doctor (creates User + Doctor in one call)
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        doctors = Doctors.objects.select_related('user', 'specialty').all()

        search    = request.query_params.get('search', '').strip()
        specialty = request.query_params.get('specialty', '').strip()
        actif     = request.query_params.get('actif', '').strip()

        if search:
            doctors = doctors.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        if specialty:
            doctors = doctors.filter(specialty__name__icontains=specialty)
        if actif in ('true', 'false'):
            doctors = doctors.filter(actif=(actif == 'true'))

        return Response(AdminDoctorSerializer(doctors, many=True).data)

    def post(self, request):
        serializer = AdminDoctorCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        doctor = serializer.save()
        _log(request.user, 'CREATE_DOCTOR', 'Doctors')
        return Response(AdminDoctorSerializer(doctor).data, status=status.HTTP_201_CREATED)


class AdminDoctorDetailView(APIView):
    """
    GET    /api/admin/doctors/<id>/  — get one doctor
    PATCH  /api/admin/doctors/<id>/  — edit doctor
    DELETE /api/admin/doctors/<id>/  — delete doctor (also deletes linked user)
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, doctor_id):
        doctor = get_object_or_404(Doctors, id=doctor_id)
        return Response(AdminDoctorSerializer(doctor).data)

    def patch(self, request, doctor_id):
        doctor = get_object_or_404(Doctors, id=doctor_id)
        data   = request.data

        # Update linked user fields if provided
        user = doctor.user
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        if 'phone' in data:
            user.phone = data['phone'].strip()
        if 'email' in data:
            user.email = data['email'].strip()
        user.save()

        # Update doctor fields
        if 'bio' in data:
            doctor.bio = data['bio']
        if 'ville' in data:
            doctor.ville = data['ville']
        if 'horaire_travail' in data:
            doctor.horaire_travail = data['horaire_travail']
        if 'actif' in data:
            doctor.actif = data['actif']
        if 'specialty_id' in data:
            from users.models import Specialty
            doctor.specialty = get_object_or_404(Specialty, id=data['specialty_id'])
        doctor.save()

        _log(request.user, 'UPDATE_DOCTOR', 'Doctors')
        return Response(AdminDoctorSerializer(doctor).data)

    def delete(self, request, doctor_id):
        doctor = get_object_or_404(Doctors, id=doctor_id)
        doctor.user.delete()  # cascades to Doctor too
        _log(request.user, 'DELETE_DOCTOR', 'Doctors')
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminDoctorToggleActiveView(APIView):
    """PATCH /api/admin/doctors/<id>/toggle-active/ — activate or deactivate a doctor."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, doctor_id):
        doctor      = get_object_or_404(Doctors, id=doctor_id)
        doctor.actif = not doctor.actif
        doctor.save()
        state = 'activé' if doctor.actif else 'désactivé'
        _log(request.user, f'DOCTOR_{state.upper()}', 'Doctors')
        return Response({'detail': f'Médecin {state}.', 'actif': doctor.actif})


# ─── Patients ─────────────────────────────────────────────────────────────────

class AdminPatientListView(APIView):
    """GET /api/admin/patients/ — list all patients."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        patients = Patients.objects.select_related('parent').all()

        search = request.query_params.get('search', '').strip()
        if search:
            patients = patients.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        return Response(AdminPatientSerializer(patients, many=True).data)


class AdminPatientDetailView(APIView):
    """GET /api/admin/patients/<id>/ — get one patient's full info."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, patient_id):
        patient = get_object_or_404(Patients, id=patient_id)
        return Response(AdminPatientSerializer(patient).data)


# ─── Appointments ─────────────────────────────────────────────────────────────

class AdminAppointmentListView(APIView):
    """GET /api/admin/appointments/ — list all appointments with filters."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        appointments = (
            Appointment.objects
            .select_related('doctor__user', 'patient')
            .order_by('-date_rdv')
        )

        status_filter = request.query_params.get('status', '').strip()
        date_filter   = request.query_params.get('date', '').strip()
        doctor_name   = request.query_params.get('doctor_name', '').strip()
        patient_name  = request.query_params.get('patient_name', '').strip()

        if status_filter and status_filter != 'All':
            appointments = appointments.filter(status=status_filter)
        if date_filter:
            appointments = appointments.filter(date_rdv__date=date_filter)
        if doctor_name:
            appointments = appointments.filter(
                Q(doctor__user__last_name__icontains=doctor_name) |
                Q(doctor__user__first_name__icontains=doctor_name)
            )
        if patient_name:
            appointments = appointments.filter(
                Q(patient__first_name__icontains=patient_name) |
                Q(patient__last_name__icontains=patient_name)
            )

        return Response({
            'appointments':   AdminAppointmentSerializer(appointments, many=True).data,
            'status_choices': Appointment.STATUS_CHOICES,
        })


class AdminAppointmentDetailView(APIView):
    """
    GET   /api/admin/appointments/<id>/         — get one appointment
    PATCH /api/admin/appointments/<id>/status/  — change status
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)
        return Response(AdminAppointmentSerializer(appointment).data)


class AdminAppointmentStatusView(APIView):
    """PATCH /api/admin/appointments/<id>/status/ — update appointment status."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)
        new_status  = str(request.data.get('status', '')).strip()

        valid = dict(Appointment.STATUS_CHOICES).keys()
        if new_status not in valid:
            return Response({'detail': 'Statut invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        if appointment.status == 'COMPLETED':
            return Response(
                {'detail': 'Impossible de modifier une consultation terminée.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = new_status
        appointment.save()
        _log(request.user, f'UPDATE_APPOINTMENT_STATUS:{new_status}', 'Appointment')
        return Response({'detail': 'Statut mis à jour.', 'status': new_status})