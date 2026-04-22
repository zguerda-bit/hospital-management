from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import PermissionDenied

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Appointment, Consultation, Diagnostic, Traitement
from .serializers import CompleteConsultationSerializer
from users.models import Patients, Doctors, TraceAction
from users.permissions import IsAdmin, IsDoctor, IsParent


def _log(user, action, table=""):
    TraceAction.objects.create(user=user, action=action, table_concernee=table)


class CreateAppointmentView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        doctor_id  = request.data.get('doctor_id')
        patient_id = request.data.get('patient_id')
        date_rdv   = request.data.get('date_rdv')
        motif      = request.data.get('motif', '').strip()
        reason     = request.data.get('reason', '').strip()

        if not all([doctor_id, patient_id, date_rdv]):
            return Response({'detail': 'doctor_id, patient_id et date_rdv sont requis.'}, status=status.HTTP_400_BAD_REQUEST)

        doctor  = get_object_or_404(Doctors,  id=doctor_id)
        patient = get_object_or_404(Patients, id=patient_id)

        appointment = Appointment.objects.create(
            doctor=doctor, patient=patient,
            date_rdv=date_rdv, motif=motif, reason=reason,
            status='PENDING', created_by=request.user,
        )
        _log(request.user, 'CREATE_APPOINTMENT', 'Appointment')
        return Response({'detail': 'Rendez-vous créé avec succès.', 'appointment_id': appointment.id}, status=status.HTTP_201_CREATED)


class CancelAppointmentView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)
        if appointment.status == 'COMPLETED':
            return Response({'detail': "Impossible d'annuler une consultation déjà terminée."}, status=status.HTTP_400_BAD_REQUEST)
        appointment.status = 'CANCELLED'
        appointment.save()
        _log(request.user, 'CANCEL_APPOINTMENT', 'Appointment')
        return Response({'detail': 'Rendez-vous annulé.'})


class CompleteConsultationView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)
        if appointment.doctor.user != request.user:
            raise PermissionDenied
        if appointment.status in ('COMPLETED', 'CANCELLED'):
            return Response({'detail': 'Ce rendez-vous ne peut plus être modifié.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CompleteConsultationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        c_data = serializer.validated_data['consultation']
        d_data = serializer.validated_data['diagnostic']
        t_data = serializer.validated_data['traitement']

        try:
            with transaction.atomic():
                consultation = Consultation.objects.create(
                    appointment=appointment,
                    poids=c_data['poids'], taille=c_data['taille'],
                    temperature=c_data.get('temperature', 37.0),
                    observation=c_data.get('observation', ''),
                )
                Diagnostic.objects.create(
                    consultation=consultation,
                    nom_maladie=d_data['nom_maladie'],
                    type_maladie=d_data.get('type_maladie', 'AUTRE'),
                    gravite=d_data.get('gravite', 'LEGERE'),
                    commentaire_medical=d_data.get('commentaire_medical', ''),
                    explication_parent=d_data.get('explication_parent', ''),
                )
                Traitement.objects.create(
                    consultation=consultation,
                    medicament=t_data['medicament'], dose=t_data['dose'],
                    duree=t_data['duree'], instructions=t_data.get('instructions', ''),
                )
                appointment.status = 'COMPLETED'
                appointment.save()
                _log(request.user, 'CREATE_CONSULTATION', 'Consultation')
        except Exception as e:
            return Response({'detail': f"Erreur : {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': 'Consultation enregistrée avec succès.'}, status=status.HTTP_201_CREATED)


class PatientHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsParent]

    def get(self, request, patient_id):
        patient = get_object_or_404(Patients, id=patient_id, parent=request.user)
        appointments = (
            Appointment.objects
            .filter(patient=patient, status='COMPLETED')
            .select_related('consultation')
            .order_by('-date_rdv')
        )
        history = []
        for a in appointments:
            consultation = getattr(a, 'consultation', None)
            entry = {
                'appointment_id': a.id, 'date_rdv': a.date_rdv,
                'motif': a.motif, 'reason': a.reason, 'consultation': None,
            }
            if consultation:
                entry['consultation'] = {
                    'id': consultation.id,
                    'date_consultation': consultation.date_consultation,
                    'poids': consultation.poids, 'taille': consultation.taille,
                    'temperature': consultation.temperature, 'observation': consultation.observation,
                    'diagnostics': [
                        {
                            'nom_maladie': d.nom_maladie,
                            'type_maladie': d.get_type_maladie_display(),
                            'gravite': d.get_gravite_display(),
                            'commentaire_medical': d.commentaire_medical,
                            'explication_parent': d.explication_parent,
                        } for d in consultation.diagnostics.all()
                    ],
                    'traitements': [
                        {
                            'medicament': t.medicament, 'dose': t.dose,
                            'duree': t.duree, 'instructions': t.instructions,
                        } for t in consultation.traitements.all()
                    ],
                }
            history.append(entry)

        return Response({
            'patient': {'id': patient.id, 'first_name': patient.first_name, 'last_name': patient.last_name},
            'history': history,
        })