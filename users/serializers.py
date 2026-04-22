from rest_framework import serializers
from .models import Users, Address, Specialty, Doctors, Patients, TraceAction


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address_line', 'region', 'city', 'code_postal']


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)

    class Meta:
        model = Users
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'address', 'is_active',
        ]
        read_only_fields = ['id', 'role']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'phone', 'email']

    def validate_email(self, value):
        user = self.instance
        if Users.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value


class DoctorSerializer(serializers.ModelSerializer):
    user       = UserSerializer(read_only=True)
    specialty  = SpecialtySerializer(read_only=True)
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        source='specialty',
        write_only=True,
        required=False,
    )

    class Meta:
        model = Doctors
        fields = ['id', 'user', 'specialty', 'specialty_id', 'bio', 'ville', 'horaire_travail', 'photo', 'actif']
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = Patients
        fields = [
            'id', 'first_name', 'last_name', 'birth_date', 'gender',
            'parent', 'parent_name', 'telephone_parent', 'email',
            'groupe_sanguin', 'date_creation_dossier',
        ]
        read_only_fields = ['id', 'parent', 'parent_name', 'date_creation_dossier']     
    def get_parent_name(self, obj):
        return f"{obj.parent.first_name} {obj.parent.last_name}"


class PatientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patients
        fields = ['first_name', 'last_name', 'birth_date', 'gender']

    def create(self, validated_data):
        validated_data['parent'] = self.context['request'].user
        return super().create(validated_data)


class TraceActionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = TraceAction
        fields = ['id', 'user', 'action', 'table_concernee', 'timestamp']