from django.db import models
from users.models import Users


class Notification(models.Model):

    TYPE_CHOICES = (
        ('REMINDER',  'Rappel de rendez-vous'),
        ('RESULT',    'Résultat disponible'),
        ('MESSAGE',   'Message du service'),
        ('ADMISSION', 'Admission hospitalière'),
        ('DISCHARGE', 'Sortie hospitalière'),
    )

    recipient  = models.ForeignKey(
        Users, on_delete=models.CASCADE,
        related_name='notifications'
    )
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title      = models.CharField(max_length=150)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional link to an appointment
    appointment = models.ForeignKey(
        'consultations.Appointment',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications'
    )
    # NOTE: lab_result FK removed — LabResult model does not exist in this project

    class Meta:
        verbose_name        = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.get_notif_type_display()} → {self.recipient.username}'