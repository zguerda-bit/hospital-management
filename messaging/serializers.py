from rest_framework import serializers
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    expediteur_nom   = serializers.CharField(source='expediteur.get_full_name',   read_only=True)
    destinataire_nom = serializers.CharField(source='destinataire.get_full_name', read_only=True)

    class Meta:
        model  = Message
        fields = [
            'id', 'expediteur', 'expediteur_nom',
            'destinataire', 'destinataire_nom',
            'contenu', 'date_envoi', 'lu',
        ]
        read_only_fields = ['id', 'date_envoi', 'expediteur', 'expediteur_nom', 'destinataire_nom']


class SendMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = ['destinataire', 'contenu']
