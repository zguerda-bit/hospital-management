from django.db import models
from users.models import Patients


class Allergie(models.Model):
    REACTION_CHOICES = (
        ('LEGERE',   'Légère'),
        ('MODEREE',  'Modérée'),
        ('SEVERE',   'Sévère'),
        ('CRITIQUE', 'Critique'),
    )

    patient        = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name='allergies')
    nom            = models.CharField(max_length=150, help_text="Nom de l'allergène")
    reaction       = models.CharField(max_length=20, choices=REACTION_CHOICES, default='LEGERE')
    description    = models.TextField(blank=True)
    date_detection = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name        = "Allergie"
        verbose_name_plural = "Allergies"
        ordering            = ['-date_detection']

    def __str__(self):
        return f"{self.nom} ({self.get_reaction_display()}) — {self.patient}"


class Antecedent(models.Model):
    TYPE_CHOICES = (
        ('MEDICAL',      'Médical'),
        ('CHIRURGICAL',  'Chirurgical'),
        ('FAMILIAL',     'Familial'),
        ('AUTRE',        'Autre'),
    )

    patient          = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name='antecedents')
    description      = models.TextField()
    type_antecedent  = models.CharField(max_length=20, choices=TYPE_CHOICES, default='MEDICAL')
    date_declaration = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name        = "Antécédent"
        verbose_name_plural = "Antécédents"
        ordering            = ['-date_declaration']

    def __str__(self):
        return f"{self.get_type_antecedent_display()} — {self.patient} ({self.date_declaration})"