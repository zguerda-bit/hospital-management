from django.db import models
from users.models import Doctors, Patients, Users


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('CONFIRMED', 'Confirmé'),
        ('COMPLETED', 'Terminé'),
        ('CANCELLED', 'Annulé'),
    )

    doctor = models.ForeignKey(Doctors, on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name='appointments')
    created_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_appointments'
    )

    date_rdv = models.DateTimeField()
    heure = models.TimeField(null=True, blank=True)
    motif = models.CharField(max_length=200, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ['-date_rdv']

    def __str__(self):
        return f"{self.patient} avec Dr. {self.doctor.user.last_name} le {self.date_rdv:%d/%m/%Y}"


class Consultation(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='consultation'
    )
    date_consultation = models.DateTimeField(auto_now_add=True)

    poids = models.DecimalField(max_digits=5, decimal_places=2, help_text="en kg")
    taille = models.DecimalField(max_digits=5, decimal_places=2, help_text="en cm")
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=37.0,
        help_text="en °C"
    )
    observation = models.TextField(blank=True)

    class Meta:
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"
        ordering = ['-date_consultation']

    def __str__(self):
        return f"Consultation — {self.appointment.patient} ({self.date_consultation:%d/%m/%Y})"


class Diagnostic(models.Model):
    TYPE_CHOICES = (
        ('AIGU', 'Aigu'),
        ('CHRONIQUE', 'Chronique'),
        ('ALLERGIQUE', 'Allergique'),
        ('INFECTIEUX', 'Infectieux'),
        ('AUTRE', 'Autre'),
    )
    GRAVITE_CHOICES = (
        ('LEGERE', 'Légère'),
        ('MODEREE', 'Modérée'),
        ('SEVERE', 'Sévère'),
    )

    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='diagnostics'
    )
    nom_maladie = models.CharField(max_length=200)
    type_maladie = models.CharField(max_length=20, choices=TYPE_CHOICES, default='AUTRE')
    gravite = models.CharField(max_length=20, choices=GRAVITE_CHOICES, default='LEGERE')
    commentaire_medical = models.TextField(blank=True)
    explication_parent = models.TextField(blank=True)

    class Meta:
        verbose_name = "Diagnostic"
        verbose_name_plural = "Diagnostics"

    def __str__(self):
        return f"{self.nom_maladie} ({self.get_gravite_display()})"


class Traitement(models.Model):
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='traitements'
    )
    medicament = models.CharField(max_length=200)
    dose = models.CharField(max_length=100)
    duree = models.CharField(max_length=100, help_text="ex: 7 jours, 2 semaines")
    instructions = models.TextField(blank=True)
    doctor  = models.ForeignKey('users.Doctors',  on_delete=models.SET_NULL, null=True, blank=True, related_name='traitements')
    patient = models.ForeignKey('users.Patients', on_delete=models.SET_NULL, null=True, blank=True, related_name='traitements')

    class Meta:
        verbose_name = "Traitement"
        verbose_name_plural = "Traitements"

    def __str__(self):
        return f"{self.medicament} — {self.dose} ({self.duree})"
    
    
class LabResult(models.Model):
    STATUS_CHOICES = (
        ('NORMAL', 'Normal'),
        ('HIGH',   'Élevé'),
        ('LOW',    'Bas'),
    )

    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='lab_results'
    )
    test_name       = models.CharField(max_length=200)
    result_value    = models.CharField(max_length=100)
    unit            = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NORMAL')
    test_date       = models.DateField()

    class Meta:
        verbose_name        = 'Résultat de laboratoire'
        verbose_name_plural = 'Résultats de laboratoire'

    def __str__(self):
        return f'{self.test_name} — {self.result_value} ({self.status})'