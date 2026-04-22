from django.db import models
from users.models import Patients


class Document(models.Model):
    TYPE_CHOICES = (
        ('ORDONNANCE',   'Ordonnance'),
        ('RADIO',        'Radiographie'),
        ('ANALYSE',      'Analyse de laboratoire'),
        ('COMPTE_RENDU', 'Compte rendu'),
        ('AUTRE',        'Autre'),
    )

    patient      = models.ForeignKey(
        Patients,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    consultation = models.ForeignKey(
        'consultations.Consultation',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='documents'
    )
    nom_fichier  = models.CharField(max_length=255)
    type_doc     = models.CharField(max_length=20, choices=TYPE_CHOICES, default='AUTRE')
    fichier      = models.FileField(upload_to='documents/%Y/%m/')
    date_upload  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Document'
        verbose_name_plural = 'Documents'
        ordering            = ['-date_upload']

    def __str__(self):
        return f'{self.nom_fichier} — {self.patient}'
