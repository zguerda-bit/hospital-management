from rest_framework import serializers
from users.models import Users, Doctors, Patients, Specialty, Address
from consultations.models import Appointment


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Address
        fields = ['id', 'address_line', 'region', 'city', 'code_postal']


class AdminUserSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)

    class Meta:
        model  = Users
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name',
            'role', 'phone', 'is_active',
            'date_joined', 'address',
        ]
        read_only_fields = ['id', 'date_joined']


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model  = Users
        fields = [
            'username', 'email', 'password',
            'first_name', 'last_name',
            'role', 'phone',
        ]

    def validate_email(self, value):
        if Users.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate_username(self, value):
        if Users.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Users(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AdminDoctorSerializer(serializers.ModelSerializer):
    user       = AdminUserSerializer(read_only=True)
    specialty  = serializers.StringRelatedField()

    class Meta:
        model  = Doctors
        fields = [
            'id', 'user', 'specialty',
            'bio', 'ville', 'horaire_travail',
            'photo', 'actif',
        ]


class AdminDoctorCreateSerializer(serializers.Serializer):
    """Creates a User with role=DOCTOR and a linked Doctor profile in one call."""
    # User fields
    username   = serializers.CharField(max_length=150)
    email      = serializers.EmailField()
    password   = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=50)
    last_name  = serializers.CharField(max_length=50)
    phone      = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # Doctor fields
    specialty_id    = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(), source='specialty'
    )
    bio             = serializers.CharField(required=False, allow_blank=True)
    ville           = serializers.CharField(required=False, allow_blank=True)
    horaire_travail = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if Users.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate_username(self, value):
        if Users.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def create(self, validated_data):
        specialty       = validated_data.pop('specialty')
        bio             = validated_data.pop('bio', '')
        ville           = validated_data.pop('ville', '')
        horaire_travail = validated_data.pop('horaire_travail', '')
        password        = validated_data.pop('password')

        user = Users(**validated_data, role='DOCTOR')
        user.set_password(password)
        user.save()

        doctor = Doctors.objects.create(
            user=user,
            specialty=specialty,
            bio=bio,
            ville=ville,
            horaire_travail=horaire_travail,
        )
        return doctor


class AdminPatientSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model  = Patients
        fields = [
            'id', 'first_name', 'last_name',
            'birth_date', 'gender', 'groupe_sanguin',
            'telephone_parent', 'email',
            'date_creation_dossier',
            'parent', 'parent_name',
        ]

    def get_parent_name(self, obj):
        return f"{obj.parent.first_name} {obj.parent.last_name}"


class AdminAppointmentSerializer(serializers.ModelSerializer):
    doctor_name  = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()

    class Meta:
        model  = Appointment
        fields = [
            'id', 'doctor', 'doctor_name',
            'patient', 'patient_name',
            'date_rdv', 'heure', 'motif', 'reason',
            'status', 'status_label',
            'created_at', 'updated_at',
        ]

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.last_name} {obj.doctor.user.first_name}"

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_status_label(self, obj):
        return obj.get_status_display()