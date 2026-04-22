from rest_framework import serializers
from .models import Allergie, Antecedent


class AllergieSerializer(serializers.ModelSerializer):
    reaction_label = serializers.SerializerMethodField()

    class Meta:
        model  = Allergie
        fields = [
            'id', 'patient',
            'nom', 'reaction', 'reaction_label',
            'description', 'date_detection',
        ]
        read_only_fields = ['id', 'patient']

    def get_reaction_label(self, obj):
        return obj.get_reaction_display()


class AllergieWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Allergie
        fields = ['nom', 'reaction', 'description', 'date_detection']


class AntecedentSerializer(serializers.ModelSerializer):
    type_label = serializers.SerializerMethodField()

    class Meta:
        model  = Antecedent
        fields = [
            'id', 'patient',
            'description', 'type_antecedent', 'type_label',
            'date_declaration',
        ]
        read_only_fields = ['id', 'patient']

    def get_type_label(self, obj):
        return obj.get_type_antecedent_display()


class AntecedentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Antecedent
        fields = ['description', 'type_antecedent', 'date_declaration']