from django.db import models
from django.contrib.auth.models import AbstractUser


class Address(models.Model):
    address_line = models.CharField(max_length=100)
    region = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    code_postal = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"

    def __str__(self):
        return f"{self.address_line}, {self.city}"


class Users(AbstractUser):
    email = models.EmailField(unique=True)

    ROLE_CHOICES = (
        ('ADMIN', 'Administrateur'),
        ('DOCTOR', 'Médecin'),
        ('PARENT', 'Parent'),
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.username} ({self.role})"


class Specialty(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Spécialité"
        verbose_name_plural = "Spécialités"

    def __str__(self):
        return self.name


class Doctors(models.Model):
    user = models.OneToOneField(Users, on_delete=models.CASCADE)
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='doctors/photos/', null=True, blank=True)
    horaire_travail = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    ville = models.CharField(max_length=100, blank=True)
    class Meta:
        verbose_name = "Médecin"
        verbose_name_plural = "Médecins"

    def __str__(self):
        return f"Dr. {self.user.last_name}"


class Patients(models.Model):
    parent = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'PARENT'},
        related_name='children'
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    # null=True lets existing DB rows survive the migration without a one-off
    # default. Enforce the value at the form level instead.
    birth_date = models.DateField(null=True, blank=True)

    GENDER_CHOICES = (
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)

    BLOOD_GROUP_CHOICES = (
         ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
         ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),
    )
    groupe_sanguin= models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    telephone_parent = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    date_creation_dossier = models.DateField(auto_now_add=True, null=True)
    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Reste_token(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Token de réinitialisation"
        verbose_name_plural = "Tokens de réinitialisation"

    def __str__(self):
        return f"Token de {self.user.username}"


class TraceAction(models.Model):
    user = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(max_length=100)
    table_concernee = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Trace d'action"
        verbose_name_plural = "Traces d'actions"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} — {self.action} ({self.timestamp:%Y-%m-%d %H:%M})"