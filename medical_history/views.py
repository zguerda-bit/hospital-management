from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.models import Patients, TraceAction
from .models import Allergie, Antecedent
from .serializers import (
    AllergieSerializer, AllergieWriteSerializer,
    AntecedentSerializer, AntecedentWriteSerializer,
)


def _log(user, action, table=""):
    TraceAction.objects.create(user=user, action=action, table_concernee=table)


def _get_patient(patient_id, user):
    """
    Doctor  → can access any patient.
    Parent  → can only access their own children.
    """
    if user.role == 'DOCTOR':
        return get_object_or_404(Patients, id=patient_id)
    if user.role == 'PARENT':
        return get_object_or_404(Patients, id=patient_id, parent=user)
    raise PermissionDenied


# ─────────────────────────────────────────────────────────────────────────────
# ALLERGIES
# ─────────────────────────────────────────────────────────────────────────────

class AllergieListCreateView(APIView):
    """
    GET  /api/medical/patients/<patient_id>/allergies/
    POST /api/medical/patients/<patient_id>/allergies/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        patient   = _get_patient(patient_id, request.user)
        allergies = Allergie.objects.filter(patient=patient)
        return Response(AllergieSerializer(allergies, many=True).data)

    def post(self, request, patient_id):
        patient    = _get_patient(patient_id, request.user)
        serializer = AllergieWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        allergie = serializer.save(patient=patient)
        _log(request.user, 'CREATE_ALLERGIE', 'Allergie')
        return Response(AllergieSerializer(allergie).data, status=status.HTTP_201_CREATED)


class AllergieDetailView(APIView):
    """
    GET    /api/medical/allergies/<allergie_id>/
    PATCH  /api/medical/allergies/<allergie_id>/
    DELETE /api/medical/allergies/<allergie_id>/
    """
    permission_classes = [IsAuthenticated]

    def _get_allergie(self, allergie_id, user):
        allergie = get_object_or_404(Allergie, id=allergie_id)
        if user.role == 'PARENT' and allergie.patient.parent != user:
            raise PermissionDenied
        return allergie

    def get(self, request, allergie_id):
        allergie = self._get_allergie(allergie_id, request.user)
        return Response(AllergieSerializer(allergie).data)

    def patch(self, request, allergie_id):
        allergie   = self._get_allergie(allergie_id, request.user)
        serializer = AllergieWriteSerializer(allergie, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        _log(request.user, 'UPDATE_ALLERGIE', 'Allergie')
        return Response(AllergieSerializer(allergie).data)

    def delete(self, request, allergie_id):
        allergie = self._get_allergie(allergie_id, request.user)
        allergie.delete()
        _log(request.user, 'DELETE_ALLERGIE', 'Allergie')
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# ANTÉCÉDENTS
# ─────────────────────────────────────────────────────────────────────────────

class AntecedentListCreateView(APIView):
    """
    GET  /api/medical/patients/<patient_id>/antecedents/
    POST /api/medical/patients/<patient_id>/antecedents/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        patient     = _get_patient(patient_id, request.user)
        antecedents = Antecedent.objects.filter(patient=patient)
        return Response(AntecedentSerializer(antecedents, many=True).data)

    def post(self, request, patient_id):
        patient    = _get_patient(patient_id, request.user)
        serializer = AntecedentWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        antecedent = serializer.save(patient=patient)
        _log(request.user, 'CREATE_ANTECEDENT', 'Antecedent')
        return Response(AntecedentSerializer(antecedent).data, status=status.HTTP_201_CREATED)


class AntecedentDetailView(APIView):
    """
    GET    /api/medical/antecedents/<antecedent_id>/
    PATCH  /api/medical/antecedents/<antecedent_id>/
    DELETE /api/medical/antecedents/<antecedent_id>/
    """
    permission_classes = [IsAuthenticated]

    def _get_antecedent(self, antecedent_id, user):
        antecedent = get_object_or_404(Antecedent, id=antecedent_id)
        if user.role == 'PARENT' and antecedent.patient.parent != user:
            raise PermissionDenied
        return antecedent

    def get(self, request, antecedent_id):
        antecedent = self._get_antecedent(antecedent_id, request.user)
        return Response(AntecedentSerializer(antecedent).data)

    def patch(self, request, antecedent_id):
        antecedent = self._get_antecedent(antecedent_id, request.user)
        serializer = AntecedentWriteSerializer(antecedent, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        _log(request.user, 'UPDATE_ANTECEDENT', 'Antecedent')
        return Response(AntecedentSerializer(antecedent).data)

    def delete(self, request, antecedent_id):
        antecedent = self._get_antecedent(antecedent_id, request.user)
        antecedent.delete()
        _log(request.user, 'DELETE_ANTECEDENT', 'Antecedent')
        return Response(status=status.HTTP_204_NO_CONTENT)