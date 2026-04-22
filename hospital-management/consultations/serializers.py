from rest_framework import serializers
from .models import Appointment, Consultation, Diagnostic, Traitement


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name  = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()

    class Meta:
        model  = Appointment
        fields = [
            'id', 'doctor', 'doctor_name',
            'patient', 'patient_name',
            'date_rdv', 'reason', 'status', 'status_label',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.last_name} {obj.doctor.user.first_name}"

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_status_label(self, obj):
        return obj.get_status_display()


class TraitementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Traitement
        fields = ['id', 'medicament', 'dose', 'duree', 'instructions']


class DiagnosticSerializer(serializers.ModelSerializer):
    type_label    = serializers.SerializerMethodField()
    gravite_label = serializers.SerializerMethodField()

    class Meta:
        model  = Diagnostic
        fields = [
            'id', 'nom_maladie',
            'type_maladie', 'type_label',
            'gravite', 'gravite_label',
            'commentaire_medical', 'explication_parent',
        ]

    def get_type_label(self, obj):
        return obj.get_type_maladie_display()

    def get_gravite_label(self, obj):
        return obj.get_gravite_display()


class ConsultationSerializer(serializers.ModelSerializer):
    diagnostics  = DiagnosticSerializer(many=True, read_only=True)
    traitements  = TraitementSerializer(many=True, read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model  = Consultation
        fields = [
            'id', 'appointment', 'patient_name',
            'date_consultation',
            'poids', 'taille', 'temperature', 'observation',
            'diagnostics', 'traitements',
        ]
        read_only_fields = ['id', 'date_consultation']

    def get_patient_name(self, obj):
        return f"{obj.appointment.patient.first_name} {obj.appointment.patient.last_name}"


# ── Used by CompleteConsultationView ─────────────────────────────────────────

class ConsultationInputSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Consultation
        fields = ['poids', 'taille', 'temperature', 'observation']


class DiagnosticInputSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Diagnostic
        fields = ['nom_maladie', 'type_maladie', 'gravite', 'commentaire_medical', 'explication_parent']


class TraitementInputSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Traitement
        fields = ['medicament', 'dose', 'duree', 'instructions']


class CompleteConsultationSerializer(serializers.Serializer):
    """
    Validates the full 3-part payload sent by the doctor to complete a consultation.
    Body:
    {
      "consultation": { "poids": 20, "taille": 110, "temperature": 37.0, "observation": "..." },
      "diagnostic":   { "nom_maladie": "Asthme", "type_maladie": "ALLERGIQUE",
                        "gravite": "MODEREE", "commentaire_medical": "...", "explication_parent": "..." },
      "traitement":   { "medicament": "Ventoline", "dose": "2 puffs", "duree": "7j", "instructions": "..." }
    }
    """
    consultation = ConsultationInputSerializer()
    diagnostic   = DiagnosticInputSerializer()
    traitement   = TraitementInputSerializer()